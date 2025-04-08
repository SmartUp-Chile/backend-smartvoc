from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from datetime import datetime
import logging
import json

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///smartvoc.db')

# Inicialización de la aplicación
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Definición de modelos
class RequestLog(Base):
    __tablename__ = 'request_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String(10))
    path = Column(String(255))
    ip = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(255))
    response_status = Column(Integer)
    processing_time = Column(Integer)
    request_data = Column(Text)

class SmartVOCClient(Base):
    __tablename__ = 'smartvoc_clients'
    clientId = Column(Integer, primary_key=True, autoincrement=True)
    clientName = Column(String(100), nullable=False, unique=True)
    clientSlug = Column(String(100), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'clientId': self.clientId,
            'clientName': self.clientName,
            'clientSlug': self.clientSlug,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None
        }

# Crear tablas
@app.before_first_request
def setup_database():
    Base.metadata.create_all(bind=engine)

# Middleware para loggear peticiones
@app.before_request
def log_request():
    start_time = datetime.utcnow()
    request.start_time = start_time

@app.after_request
def log_response(response):
    try:
        request_data = None
        if request.is_json:
            request_data = json.dumps(request.get_json())
        
        end_time = datetime.utcnow()
        processing_time = (end_time - request.start_time).total_seconds() * 1000
        
        log = RequestLog(
            method=request.method,
            path=request.path,
            ip=request.remote_addr,
            timestamp=request.start_time,
            user_agent=request.user_agent.string,
            response_status=response.status_code,
            processing_time=int(processing_time),
            request_data=request_data
        )
        
        db_session.add(log)
        db_session.commit()
    except Exception as e:
        logger.error(f"Error al registrar la petición: {str(e)}")
        db_session.rollback()
    
    return response

# Limpiar sesión al finalizar
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# Rutas básicas
@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado de la API."""
    return jsonify({"status": "ok", "message": "El servicio está funcionando correctamente"})

@app.route('/api/db/test', methods=['GET'])
def db_test():
    """Prueba la conexión a la base de datos."""
    try:
        # Intentar ejecutar una consulta simple para verificar la conexión
        result = db_session.execute('SELECT 1').scalar()
        
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

# Ruta para listar clientes de SmartVOC
@app.route('/api/smartvoc/clients', methods=['GET'])
def get_smartvoc_clients():
    try:
        clients = SmartVOCClient.query.all()
        if not clients:
            return jsonify({
                "message": "No hay clientes registrados en la base de datos.",
                "clients": []
            }), 200
        
        clients_dict = [client.to_dict() for client in clients]
        return jsonify(clients_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para crear un cliente de SmartVOC
@app.route('/api/smartvoc/clients', methods=['POST'])
def create_smartvoc_client():
    data = request.get_json()
    client_name = data.get("clientName", "")
    
    if not client_name:
        return jsonify({"error": "El parámetro clientName es obligatorio"}), 400
    
    # Generar clientSlug en formato CamelCase
    client_slug = ''.join(word.capitalize() for word in client_name.split())
    
    try:
        # Verificar si ya existe un cliente con ese nombre
        existing_client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if existing_client:
            return jsonify({"error": f"Ya existe un cliente con el nombre '{client_name}'"}), 400
        
        # Crear el nuevo cliente
        new_client = SmartVOCClient(
            clientName=client_name,
            clientSlug=client_slug
        )
        db_session.add(new_client)
        db_session.commit()
        
        return jsonify({"message": f"Cliente {client_name} creado exitosamente"}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Iniciar el servidor de desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000) 