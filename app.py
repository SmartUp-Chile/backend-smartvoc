from flask import Flask, jsonify, request
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

# Importar modelos después de inicializar db
from models import RequestLog

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
    # Registrar la solicitud en la base de datos si no es una solicitud a /static/
    if not request.path.startswith('/static/'):
        log_entry = RequestLog(
            endpoint=request.path,
            method=request.method
        )
        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al registrar solicitud: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "El servicio está funcionando correctamente con hot reload activado"})

@app.route('/api/db-test', methods=['GET'])
def db_test():
    """Endpoint para probar la conexión a la base de datos."""
    try:
        # Intentar ejecutar una consulta simple para verificar la conexión
        result = db.session.execute('SELECT 1').scalar()
        
        # Obtener el número de solicitudes registradas
        request_count = RequestLog.query.count()
            
        return jsonify({
            "status": "ok",
            "main_db": "conectada",
            "request_count": request_count
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Crear todas las tablas de la base de datos si no existen
    with app.app_context():
        db.create_all()
    
    # Iniciar el servidor de desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000) 