from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from ..config import config
from .models import Base

# Crear el engine de SQLAlchemy
engine = create_engine(
    config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30
)

# Crear la fábrica de sesiones
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@contextmanager
def get_db():
    """Contexto para manejar sesiones de base de datos"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def init_db():
    """Inicializa la base de datos creando todas las tablas"""
    Base.metadata.create_all(engine)

def get_session():
    """Obtiene una nueva sesión de base de datos"""
    return Session() 