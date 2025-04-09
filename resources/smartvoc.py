from flask_restx import Namespace, Resource, fields
import logging
from app import db
from services.smartvoc_service import SmartVOCService
from utils.api_models import create_response_model
from utils.api_helpers import validate_json_request
from exceptions.custom_exceptions import ResourceNotFoundError, ValidationError

# Configuración de logging
logger = logging.getLogger(__name__)

# Servicio de SmartVOC
smartvoc_service = SmartVOCService()

# Variables globales para el namespace y modelos
smartvoc_ns = None
client_input = None
client_output = None
success_response = None
error_response = None
list_response = None

def init_smartvoc_namespace(api):
    """Inicializa el namespace de SmartVOC y sus modelos"""
    global smartvoc_ns, client_input, client_output, success_response, error_response, list_response
    
    logger.info("Inicializando namespace de SmartVOC...")
    
    # Definir modelos de entrada y salida
    client_input = api.model('ClientInput', {
        'name': fields.String(required=True, description='Nombre del cliente'),
        'api_key': fields.String(required=True, description='API key del cliente'),
        'config': fields.Raw(description='Configuración del cliente en formato JSON'),
        'active': fields.Boolean(default=True, description='Estado del cliente')
    })
    
    client_output = api.model('ClientOutput', {
        'id': fields.String(description='ID del cliente'),
        'name': fields.String(description='Nombre del cliente'),
        'api_key': fields.String(description='API key del cliente'),
        'config': fields.Raw(description='Configuración del cliente'),
        'active': fields.Boolean(description='Estado del cliente'),
        'created_at': fields.DateTime(description='Fecha de creación'),
        'updated_at': fields.DateTime(description='Fecha de última actualización')
    })
    
    # Crear modelos de respuesta
    success_response = create_response_model(api, 'SmartVOCSuccess', 
                                            {'client': fields.Nested(client_output)})
    
    error_response = create_response_model(api, 'SmartVOCError', 
                                          {'message': fields.String()}, is_error=True)
    
    list_response = create_response_model(api, 'SmartVOCList', 
                                         {'clients': fields.List(fields.Nested(client_output)),
                                          'total': fields.Integer()})
    
    # Definir la clase del recurso SmartVOC
    class SmartVOCResource(Resource):
        @smartvoc_ns.doc('get_clients')
        @smartvoc_ns.response(200, 'Success', list_response)
        @smartvoc_ns.response(404, 'Not Found', error_response)
        @smartvoc_ns.response(500, 'Server Error', error_response)
        def get(self):
            """Obtiene la lista de clientes o información de un cliente específico"""
            try:
                clients = smartvoc_service.get_clients()
                return {
                    'status': 'success',
                    'clients': clients,
                    'total': len(clients)
                }, 200
            except ResourceNotFoundError as e:
                logger.error(f"Error al obtener clientes: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e)
                }, 404
            except Exception as e:
                logger.error(f"Error en SmartVOC GET: {str(e)}")
                return {
                    'status': 'error',
                    'message': f'Error interno: {str(e)}'
                }, 500
        
        @smartvoc_ns.doc('create_client')
        @smartvoc_ns.expect(client_input)
        @smartvoc_ns.response(201, 'Created', success_response)
        @smartvoc_ns.response(400, 'Validation Error', error_response)
        @smartvoc_ns.response(500, 'Server Error', error_response)
        def post(self):
            """Crea un nuevo cliente"""
            try:
                data = validate_json_request()
                new_client = smartvoc_service.create_client(data)
                return {
                    'status': 'success',
                    'client': new_client
                }, 201
            except ValidationError as e:
                logger.error(f"Error de validación al crear cliente: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e)
                }, 400
            except Exception as e:
                logger.error(f"Error en SmartVOC POST: {str(e)}")
                return {
                    'status': 'error',
                    'message': f'Error interno: {str(e)}'
                }, 500
        
        @smartvoc_ns.doc('update_client')
        @smartvoc_ns.expect(client_input)
        @smartvoc_ns.response(200, 'Updated', success_response)
        @smartvoc_ns.response(400, 'Validation Error', error_response)
        @smartvoc_ns.response(404, 'Not Found', error_response)
        @smartvoc_ns.response(500, 'Server Error', error_response)
        def put(self):
            """Actualiza un cliente existente"""
            try:
                data = validate_json_request()
                updated_client = smartvoc_service.update_client(data.get('id'), data)
                return {
                    'status': 'success',
                    'client': updated_client
                }, 200
            except ValidationError as e:
                logger.error(f"Error de validación al actualizar cliente: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e)
                }, 400
            except ResourceNotFoundError as e:
                logger.error(f"Cliente no encontrado: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e)
                }, 404
            except Exception as e:
                logger.error(f"Error en SmartVOC PUT: {str(e)}")
                return {
                    'status': 'error',
                    'message': f'Error interno: {str(e)}'
                }, 500
    
    logger.info("Namespace de SmartVOC inicializado correctamente")
    return SmartVOCResource 