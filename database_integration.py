from sqlalchemy import create_engine, Column, BigInteger, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# ----------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA CONEXIÓN (MySQL)
# ----------------------------------------------------------------------
# Franz: Debes actualizar estas credenciales con las de tu servidor MySQL.
# El formato es: mysql+pymysql://USUARIO:PASSWORD@HOST:PUERTO/NOMBRE_BD
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://usuario:password@localhost:3306/agrimet_db"

# El motor de la base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True  # Ayuda a re-conectar si la base de datos se desconecta por inactividad
)

# Sesión local para interactuar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán todos los modelos (User, UserDevice, IrrigationLog, etc.)
Base = declarative_base()

# ----------------------------------------------------------------------
# 2. DEPENDENCIA PARA LOS ENDPOINTS (get_db)
# ----------------------------------------------------------------------
def get_db():
    """
    Función generadora para inyectar la sesión de la BD en las rutas de FastAPI.
    Garantiza que la conexión se cierre después de cada petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------------------------
# 3. MODELOS BASE (Core del Sistema)
# ----------------------------------------------------------------------

class User(Base):
    """
    Mapea la tabla 'users'. Almacena identidades anónimas basadas 
    en el ID persistente de la App móvil.
    """
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    external_id = Column(String(100), unique=True, index=True) # ID anónimo de Android
    name = Column(String(150), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    role = Column(String(50), default="ANONYMOUS")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class UserDevice(Base):
    """
    Mapea la tabla 'user_devices'. Gestiona los tokens de FCM para notificaciones.
    """
    __tablename__ = "user_devices"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fcm_token = Column(String(512), unique=True, nullable=False)
    platform = Column(String(30), default="Android")
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Notification(Base):
    """
    Mapea la tabla 'notifications'. Historial de mensajes enviados.
    """
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data_json = Column(JSON, nullable=True) # Datos extra para la App
    audience_type = Column(String(20), nullable=False) # 'USER', 'GROUP', 'ALL'
    status = Column(String(20), default="SENT")
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

class NotificationUser(Base):
    """
    Mapea la tabla 'notification_user'. Rastrea el estado de cada notificación para cada usuario.
    """
    __tablename__ = "notification_user"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    notification_id = Column(BigInteger, ForeignKey("notifications.id", ondelete="CASCADE"))
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    read_status = Column(String(20), default="UNREAD") # 'UNREAD' o 'READ'
    interaction_status = Column(String(20), default="NONE") # 'OPENED' o 'DISMISSED'
    first_opened_at = Column(DateTime, nullable=True)

class NotificationEvent(Base):
    """
    Mapea la tabla 'notification_events'. Log detallado de auditoría de clics.
    """
    __tablename__ = "notification_events"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    notification_id = Column(BigInteger, ForeignKey("notifications.id", ondelete="CASCADE"))
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    event_type = Column(String(30), nullable=False) # 'OPENED', 'DISMISSED'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)