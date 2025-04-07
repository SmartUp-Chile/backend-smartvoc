from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import active_config
import os

# Inicialización de la aplicación
app = Flask(__name__)
app.config.from_object(active_config)

# Asegurar que existe el directorio instance para SQLite
if not os.path.exists('instance'):
    os.makedirs('instance')

# Inicializar la base de datos
db = SQLAlchemy(app)

# Variable para controlar si las tablas ya fueron creadas
_tables_created = False

@app.before_first_request
def create_tables():
    """Crea las tablas en la base de datos antes de la primera solicitud."""
    global _tables_created
    if not _tables_created:
        app.logger.info("Creando tablas en la base de datos...")
        db.create_all()
        _tables_created = True
        app.logger.info("Tablas creadas correctamente.")

@app.before_request
def log_request():
    # Importar RequestLog aquí para evitar importación circular
    from models import RequestLog
    
    # Registrar la solicitud en la base de datos si no es una solicitud a /static/ o a la documentación
    if not request.path.startswith('/static/') and not request.path.startswith('/api/docs'):
        log_entry = RequestLog(
            endpoint=request.path,
            method=request.method,
            status_code=200,  # Se actualizará después con el código de respuesta real
            response_time=0,  # Se calculará después del procesamiento
            ip_address=request.remote_addr if request.remote_addr else "unknown",
            user_agent=request.user_agent.string if request.user_agent else "unknown"
        )
        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al registrar solicitud: {e}")

# Configurar la API con Swagger
from api import api_bp
app.register_blueprint(api_bp)

# Mantener los endpoints antiguos para compatibilidad (serán eliminados en versiones futuras)
@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint antiguo para compatibilidad. Por favor, use /api/health/ en su lugar."""
    return {"status": "ok", "message": "El servicio está funcionando correctamente con hot reload activado"}

@app.route('/api/db-test', methods=['GET'])
def db_test():
    """Endpoint antiguo para compatibilidad. Por favor, use /api/db/test en su lugar."""
    from resources.db import DBTestResource
    resource = DBTestResource()
    return resource.get()

if __name__ == '__main__':
    # Importar modelos para registrarlos con SQLAlchemy
    from models import RequestLog, SmartVOCClient
    
    # Crear todas las tablas de la base de datos si no existen
    with app.app_context():
        db.create_all()
    
    # Iniciar el servidor de desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000) 