from flask import Blueprint
from flask_restx import Api, Resource, fields

# Crear el Blueprint para la API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Inicializar la API
api = Api(api_bp,
    title='SmartVOC API',
    version='1.0',
    description='API para gestionar conversaciones y análisis de SmartVOC',
    doc='/docs',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key'
        }
    }
)

# Crear namespaces
health_ns = api.namespace('health', description='Operaciones de salud del servicio')
db_ns = api.namespace('db', description='Operaciones de base de datos')
smartvoc_ns = api.namespace('smartvoc', description='Operaciones de SmartVOC')
analysis_ns = api.namespace('analysis', description='Operaciones de análisis de conversaciones')

# Definir modelos de respuesta
health_model = api.model('Health', {
    'status': fields.String(required=True, description='Estado del servicio'),
    'message': fields.String(required=True, description='Mensaje de estado')
})

db_test_model = api.model('DBTest', {
    'status': fields.String(required=True, description='Estado de la conexión'),
    'message': fields.String(required=True, description='Mensaje de estado'),
    'request_count': fields.Integer(description='Número de solicitudes realizadas')
})

db_error_model = api.model('DBError', {
    'error': fields.String(required=True, description='Mensaje de error')
})

# Utilizamos una función de inicialización para registrar recursos
def init_resources():
    from resources import register_resources
    resources = register_resources()
    
    # Inicializar modelos de SmartVOC
    from resources.smartvoc import init_smartvoc_models
    init_smartvoc_models(api)
    
    # Registrar recursos en los namespaces
    health_ns.add_resource(resources['HealthResource'], '')
    db_ns.add_resource(resources['DBTestResource'], '/test')
    smartvoc_ns.add_resource(resources['SmartVOCResource'], '')
    analysis_ns.add_resource(resources['AnalysisResource'], '/<string:conversation_id>') 