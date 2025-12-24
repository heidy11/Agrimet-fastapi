from pydantic import BaseModel
from typing import Optional

# ------------------------------------------------------------------
# Contratos de Petición (Request Models)
# ------------------------------------------------------------------

# Corresponde a la petición de registro de token (POST /fcm/register)
class TokenRegistrationRequest(BaseModel):
    # NOTA: user_id es el ID ANÓNIMO PERSISTENTE enviado desde la App Kotlin.
    user_id: int 
    fcm_token: str
    platform: str = "Android"
    
    class Config:
        from_attributes = True

# Corresponde a la petición de reporte de evento (POST /notification/report)
class NotificationReportRequest(BaseModel):
    user_id: int
    notification_id: str 
    event_type: str # Ej: OPENED, DISMISSED
    event_timestamp: int # Timestamp en milisegundos (Unix)
    
    class Config:
        from_attributes = True

# ------------------------------------------------------------------
# Contrato de Respuesta (Response Model)
# ------------------------------------------------------------------

# Modelo de Respuesta Genérica (HTTP 200/201)
class StatusResponse(BaseModel):
    status: str
    message: str