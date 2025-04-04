import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Config(object):
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'development-key-for-smartvoc')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de pool de conexiones - solo para SQL Server, no para SQLite
    # Estos parámetros se aplicarán dinámicamente solo si no estamos usando SQLite
    
    # Binds para múltiples bases de datos
    SQLALCHEMY_BINDS = {
        'db_smartvoc': os.getenv('DB_SMARTVOC_URI', 'sqlite:///instance/smartvoc.db')
    }
    
    # Base de datos principal
    # Comprobar si hay una URL de base de datos configurada en las variables de entorno
    if os.getenv('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
        # Compatibilidad con Heroku Postgres
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
            
        # Aplicar configuración de pool solo para bases de datos no SQLite
        if not SQLALCHEMY_DATABASE_URI.startswith('sqlite:'):
            SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_size': 20,
                'max_overflow': 30,
                'pool_timeout': 60,
                'pool_recycle': 300
            }
    else:
        # URL de base de datos predeterminada si no se proporciona en variables de entorno
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/smartvoc.db')

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/smartvoc_dev.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Se puede sobrescribir con variables de entorno específicas para producción

# Configuración predeterminada basada en el entorno
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# Configuración activa basada en la variable de entorno FLASK_ENV
active_config = config_by_name[os.getenv('FLASK_ENV', 'development')] 