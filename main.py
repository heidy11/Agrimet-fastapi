import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials
import time

# --- 1. IMPORTACIONES DE BASE DE DATOS ---
# Importamos la configuración y los modelos que mapean a tu agrimet.sql
from database_integration import engine, Base, get_db, User, UserDevice
# Importamos los routers de los otros servicios (Clima, Riego, Chat)
from routers import weather_router, irrigation_router, chat_router, fcm_router_db

# --- 2. INICIALIZACIÓN DE LA BASE DE DATOS ---
# Esto crea las tablas automáticamente en MySQL si aún no existen
Base.metadata.create_all(bind=engine)

# --- 3. CONFIGURACIÓN DE FIREBASE ADMIN ---
# Franz: Asegúrate de tener el archivo 'serviceAccountKey.json' en la raíz del proyecto
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("[FIREBASE] SDK inicializado correctamente para notificaciones push.")
except Exception as e:
    print(f"[FIREBASE] Advertencia: No se pudo inicializar (revisa serviceAccountKey.json): {e}")

# --- 4. CONFIGURACIÓN DE LA APLICACIÓN ---
app = FastAPI(
    title="Agrimet API - Backend Real",
    description="Backend conectado a MySQL para registro de dispositivos y servicios climáticos.",
    version="2.0.0"
)

# Habilitar CORS para que el teléfono físico pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. REGISTRO DE ROUTERS (MODULARIZACIÓN) ---
# Incluimos los otros servicios para que todo corra en el mismo puerto 9000
app.include_router(fcm_router_db.router)      # Lógica real de registro y reportes en BD
app.include_router(weather_router.router)   # Clima y Alertas
app.include_router(irrigation_router.router) # Cálculo de Riego
app.include_router(chat_router.router)       # Chatbot

# --- 6. ENDPOINT RAÍZ ---
@app.get("/")
def read_root():
    """Verificación de estado del servidor."""
    return {
        "app": "Agrimet API",
        "status": "Running",
        "database": "Connected (MySQL)",
        "port": 9000,
        "firebase_admin": "Initialized" if firebase_admin._apps else "Error"
    }

# --- 7. MODO DE EJECUCIÓN ---
# Franz: Para correr el servidor usa el siguiente comando en la terminal:
# uvicorn main:app --host 0.0.0.0 --port 9000 --reload