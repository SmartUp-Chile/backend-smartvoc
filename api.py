from flask import Blueprint
from flask_restx import Api, Resource, fields

# Crear un Blueprint para la API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Inicializar la API con el Blueprint
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Tipo: 'Bearer {token}'. Ejemplo: 'Bearer abcdef123456'"
    }
}

api = Api(
    api_bp,
    version='0.3.0',
    title='SmartVOC API',
    description='API para el servicio SmartVOC',
    doc='/docs',
    authorizations=authorizations,
)

# Crear namespaces para organizar los endpoints
health_ns = api.namespace('health', description='Verificación de estado del servicio')
db_ns = api.namespace('db', description='Operaciones relacionadas con la base de datos')
# El namespace smartvoc_ns se define en resources/smartvoc.py

# Definir modelos de respuesta
health_model = api.model('Health', {
    'status': fields.String(required=True, description='Estado del servicio', example='ok'),
    'message': fields.String(required=True, description='Mensaje descriptivo', example='El servicio está funcionando correctamente')
})

db_test_model = api.model('DBTest', {
    'status': fields.String(required=True, description='Estado de la conexión', example='ok'),
    'main_db': fields.String(required=True, description='Estado de la base de datos principal', example='conectada'),
    'request_count': fields.Integer(required=True, description='Número de solicitudes registradas', example=42)
})

db_error_model = api.model('DBError', {
    'status': fields.String(required=True, description='Estado de error', example='error'),
    'error': fields.String(required=True, description='Mensaje de error', example='Error de conexión a la base de datos')
})

# Importamos los recursos para que sean registrados en la API
import resources 