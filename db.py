from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///smartvoc.db')

# Inicialización del engine y la sesión
engine = create_engine(DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base declarativa para los modelos
Base = declarative_base()
Base.query = db_session.query_property()

def init_db(app=None):
    """
    Inicializa la base de datos y crea las tablas.
    Si se proporciona una aplicación Flask, configura los listeners de eventos.
    """
    logger.info("Inicializando base de datos...")
    try:
        # Importar modelos para que SQLAlchemy los registre
        import models
        
        # Crear tablas
        Base.metadata.create_all(bind=engine)
        
        # Configurar manejadores de eventos de la aplicación Flask
        if app:
            @app.teardown_appcontext
            def cleanup(exception=None):
                shutdown_session(exception)
            
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        raise

def shutdown_session(exception=None):
    """Remueve la sesión al finalizar la petición."""
    if exception:
        logger.error(f"Error durante la petición: {str(exception)}")
    db_session.remove() 