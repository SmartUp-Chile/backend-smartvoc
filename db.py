from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os

# Configuración de la base de datos
DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///smartvoc.db')

# Inicialización del engine y la sesión
engine = create_engine(DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base declarativa para los modelos
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Inicializa la base de datos y crea las tablas."""
    Base.metadata.create_all(bind=engine)

def shutdown_session(exception=None):
    """Remueve la sesión al finalizar la petición."""
    db_session.remove() 