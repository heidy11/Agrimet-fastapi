from fastapi import APIRouter, HTTPException, status
from models.fcm_models import TokenRegistrationRequest, NotificationReportRequest, StatusResponse
from datetime import datetime, timezone
import time
import logging

# Configuración de Logging para simular la BD
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

router = APIRouter(
    prefix="/api/v1",
    tags=["FCM Management"]
)

# ----------------------------------------------------------------------
# 1. ENDPOINT: Registro de Token (POST /api/v1/fcm/register)
# SIMULA: UPSERT en user_devices
# ----------------------------------------------------------------------
@router.post("/fcm/register", response_model=StatusResponse, status_code=status.HTTP_201_CREATED)
async def register_fcm_token(request: TokenRegistrationRequest):
    """
    Recibe el token de FCM y el ID de usuario ANÓNIMO persistente y simula el registro en la BD.
    """
    try:
        # ⭐️ INICIO DE LA LÓGICA FUNCIONAL (SIMULADA) ⭐️
        
        # 1. Simular verificación/creación de usuario anónimo
        logging.info(f"[BD-USERS] Verificando/Creando usuario ID: {request.user_id}")

        # 2. Simular lógica UPSERT (Actualizar o Insertar) en user_devices
        # Asumimos que la operación de BD fue exitosa.
        log_action = f"UPSERT successful for Token: {request.fcm_token[:10]}... (User ID: {request.user_id})"
        logging.info(f"[BD-DEVICES] {log_action}")
        
        # ⭐️ FIN DE LA LÓGICA FUNCIONAL ⭐️
        
        return StatusResponse(status="success", message="Token registrado exitosamente.")
        
    except Exception as e:
        # Esto debe capturar errores de conexión o de query SQL
        logging.error(f"FATAL ERROR: Fallo al procesar registro: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al procesar el registro: {e}")

# ----------------------------------------------------------------------
# 2. ENDPOINT: Reporte de Eventos (POST /api/v1/notification/report)
# SIMULA: INSERT en notification_events y UPDATE en notification_user
# ----------------------------------------------------------------------
@router.post("/notification/report", response_model=StatusResponse)
async def report_notification_event(request: NotificationReportRequest):
    """
    Recibe un evento de interacción (OPENED, DISMISSED) desde la App Kotlin y simula el registro y la actualización de estado en la BD.
    """
    try:
        # Convierte el timestamp de milisegundos a un objeto datetime UTC
        event_time = datetime.fromtimestamp(request.event_timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # ⭐️ INICIO DE LA LÓGICA FUNCIONAL (SIMULADA) ⭐️
        
        # 1. Simular INSERT en la tabla de LOG (notification_events)
        log_insert = f"INSERTED: Event Type '{request.event_type}' at {event_time} (Notif ID: {request.notification_id})"
        logging.info(f"[BD-EVENTS] {log_insert}")

        # 2. Simular lógica UPDATE en la tabla de ESTADO (notification_user)
        if request.event_type == "OPENED":
            log_update = f"UPDATED: Set read_status='READ', first_opened_at='{event_time}' for User {request.user_id}"
        elif request.event_type == "DISMISSED":
             log_update = f"UPDATED: Set interaction_status='DISMISSED' for User {request.user_id}"
        else:
            log_update = f"UPDATED: Status unknown for Event Type: {request.event_type}"
            
        logging.info(f"[BD-STATUS] {log_update}")
        
        # ⭐️ FIN DE LA LÓGICA FUNCIONAL ⭐️

        return StatusResponse(status="success", message=f"Evento '{request.event_type}' registrado.")
        
    except Exception as e:
        # En una aplicación real, se manejarían errores de BD aquí.
        logging.error(f"FATAL ERROR: Fallo al procesar reporte de evento: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al procesar el reporte: {e}")