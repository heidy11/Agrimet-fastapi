from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database_integration import get_db, User, UserDevice, AudienceGroup
from models.fcm_models import TokenRegistrationRequest, StatusResponse
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/v1", tags=["FCM & Identity"])

@router.post("/fcm/register", response_model=StatusResponse)
async def register_fcm_token(request: TokenRegistrationRequest, db: Session = Depends(get_db)):
    """
    Franz: Esta función soluciona el problema del token cambiante sin tocar tu BD.
    Usa el 'external_id' (el ID fijo del cel) para encontrar siempre al mismo usuario.
    """
    try:
        # 1. Buscar al usuario por 'external_id' (el umero del teléfono)
        # No importa si reinstala la App, el external_id será el mismo.
        user = db.query(User).filter(User.external_id == str(request.user_id)).first()
        
        if not user:
            # Si es la primera vez en la vida que abre la app, lo creamos
            user = User(external_id=str(request.user_id), role="FARMER", is_active=True)
            db.add(user)
            db.flush() # Para obtener el 'user.id' generado por MariaDB

        # 2. Gestionar el Token en 'user_devices' (UPSERT)
        # Buscamos si este usuario ya tiene un dispositivo registrado
        device = db.query(UserDevice).filter(UserDevice.user_id == user.id).first()
        
        if device:
            # Si el token cambió (como te pasó en las pruebas), lo actualizamos
            if device.fcm_token != request.fcm_token:
                device.fcm_token = request.fcm_token
                device.last_seen_at = datetime.now(timezone.utc)
                device.is_active = True
        else:
            # Si es un dispositivo nuevo para este usuario
            new_device = UserDevice(
                user_id=user.id,
                fcm_token=request.fcm_token,
                platform="Android",
                is_active=True
            )
            db.add(new_device)
        
        db.commit()
        return StatusResponse(status="success", message="Identidad reconocida y token actualizado.")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")

@router.post("/fcm/assign_groups")
async def assign_groups(external_id: str, group_names: list[str], db: Session = Depends(get_db)):
    """
    Permite que un usuario pertenezca a varios grupos (A, B, C) al mismo tiempo
    usando tu tabla existente 'user_groups'.
    """
    user = db.query(User).filter(User.external_id == external_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 1. Buscamos los IDs de los grupos en tu tabla 'audience_groups'
    selected_groups = []
    for name in group_names:
        group = db.query(AudienceGroup).filter(AudienceGroup.name == name).first()
        if not group:
            # Si el grupo (A, B o C) no existe, lo creamos
            group = AudienceGroup(name=name, description=f"Grupo segmentado {name}")
            db.add(group)
            db.flush()
        selected_groups.append(group)

    # 2. Actualizamos la relación en 'user_groups'
    # SQLAlchemy se encarga de insertar en la tabla intermedia automáticamente
    user.groups = selected_groups
    db.commit()

    return {
        "status": "success",
        "user": external_id,
        "nudos_asignados": [g.name for g in user.groups]
    }