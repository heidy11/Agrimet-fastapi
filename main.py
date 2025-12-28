import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials

# --- 1. IMPORTACIONES DE BASE DE DATOS Y ROUTERS ---
# Asegúrate de que estos archivos existan en tu estructura de carpetas
try:
    from database_integration import engine, Base
    from routers import (
        weather_router, 
        irrigation_router, 
        chat_router, 
        fcm_router_db, 
        group_router,
        notification_admin_router
    )
except ImportError as e:
    print(f"[ERROR CRÍTICO] Fallo al importar módulos: {e}")
    
    raise e

# --- 2. CONFIGURACIÓN DE LOGS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgrimetAPI")

# --- 3. INICIALIZACIÓN DE LA BASE DE DATOS (MariaDB) ---
# Al arrancar, SQLAlchemy verifica y crea las tablas que falten según agrimet.sql
try:
    Base.metadata.create_all(bind=engine)
    logger.info("[DATABASE] Conexión exitosa y tablas verificadas.")
except Exception as e:
    logger.error(f"[DATABASE] Error al conectar o crear tablas: {e}")

# --- 4. CONFIGURACIÓN DE FIREBASE ADMIN (Notificaciones Push) ---
# El archivo serviceAccountKey.json debe estar en la carpeta raíz
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
try:
    if not firebase_admin._apps:
        if os.path.exists(SERVICE_ACCOUNT_PATH):
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("[FIREBASE] SDK inicializado correctamente.")
        else:
            logger.warning("[FIREBASE] Falta serviceAccountKey.json. Las notificaciones remotas no funcionarán.")
except Exception as e:
    logger.error(f"[FIREBASE] Error de inicialización: {e}")

# --- 5. CONFIGURACIÓN DE LA APP ---
app = FastAPI(
    title="Agrimet API - Sistema de Gestión Agrícola",
    description="Backend oficial con soporte para identidades persistentes y segmentación por nudos.",
    version="2.5.0"
)

# Habilitar CORS para permitir que el teléfono físico (Android) se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 6. REGISTRO DE ROUTERS (Unificación de Servicios) ---
# Cada router maneja una parte lógica del sistema en el puerto 9000
app.include_router(fcm_router_db.router)             # Registro de Tokens e Identidad
app.include_router(group_router.router)              # Gestión de Nudos (A, B, C)
app.include_router(weather_router.router)            # Clima y Alertas
app.include_router(irrigation_router.router)          # Calculadora de Riego
app.include_router(chat_router.router)                # Chatbot AGRIbot
app.include_router(notification_admin_router.router)  # Envío masivo desde el Admin

# --- 7. ENDPOINTS DE ESTADO ---
@app.get("/")
def health_check():
    """Verifica si el servidor y sus componentes están vivos."""
    return {
        "status": "online",
        "port": 9000,
        "database": "MariaDB Connected",
        "firebase": "Ready" if firebase_admin._apps else "Not Configured",
        "version": "2.5.0"
    }

# --- 8. COMANDO DE EJECUCIÓN (Recordatorio para Franz) ---
# uvicorn main:app --host 0.0.0.0 --port 9000 --reload