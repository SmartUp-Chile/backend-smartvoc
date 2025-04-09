"""
API para el análisis de conversaciones de clientes
"""
import logging
from flask import request
from flask_restx import Namespace, Resource, fields
from services.analysis_service import AnalysisService
from utils.api_models import create_response_model
from exceptions.custom_exceptions import ResourceNotFoundError, ValidationError

# Configuración de logging
logger = logging.getLogger(__name__)

# Inicialización del namespace para análisis
analysis_ns = Namespace('analysis', description='Operaciones de análisis de conversaciones')

# Inicialización del servicio de análisis
analysis_service = AnalysisService()

def init_analysis_namespace():
    """Inicializa el namespace de análisis y configura los modelos"""
    global analysis_input, analysis_output, list_response, success_response, error_response
    
    # Modelo para entrada de análisis
    analysis_input = analysis_ns.model('AnalysisInput', {
        'client_name': fields.String(required=True, description='Nombre del cliente'),
        'conversation_id': fields.String(required=True, description='ID de la conversación'),
        'analysis_type': fields.String(required=True, description='Tipo de análisis'),
        'result': fields.Raw(required=True, description='Resultado del análisis'),
        'metadata': fields.Raw(description='Metadatos adicionales')
    })
    
    # Modelo para salida de análisis
    analysis_output = analysis_ns.model('AnalysisOutput', {
        'id': fields.Integer(description='ID del análisis'),
        'conversation_id': fields.String(description='ID de la conversación'),
        'analysis_type': fields.String(description='Tipo de análisis'),
        'result': fields.Raw(description='Resultado del análisis'),
        'metadata': fields.Raw(description='Metadatos adicionales'),
        'created_at': fields.DateTime(description='Fecha de creación'),
        'updated_at': fields.DateTime(description='Fecha de última actualización')
    })
    
    # Modelo para respuestas de listado
    list_response = analysis_ns.model('AnalysisList', {
        'success': fields.Boolean(description='Indica si la operación fue exitosa'),
        'analyses': fields.List(fields.Nested(analysis_output), description='Lista de análisis')
    })
    
    # Modelos de respuesta
    success_response = create_response_model(analysis_ns, 'AnalysisSuccess', analysis_output)
    error_response = analysis_ns.model('ErrorResponse', {
        'success': fields.Boolean(description='Indica si la operación fue exitosa'),
        'message': fields.String(description='Mensaje de error')
    })
    
    # Recurso para operaciones de análisis
    class AnalysisResource(Resource):
        @analysis_ns.doc('get_analysis')
        @analysis_ns.response(200, 'Análisis obtenido correctamente', model=list_response)
        @analysis_ns.response(404, 'Análisis no encontrado', model=error_response)
        def get(self, conversation_id):
            """Obtiene el análisis de una conversación específica"""
            try:
                client_name = request.args.get('client_name')
                analysis_type = request.args.get('analysis_type')
                
                if not client_name:
                    return {'success': False, 'message': 'El parámetro client_name es obligatorio'}, 400
                
                result = analysis_service.get_client_analyses(
                    client_name=client_name,
                    conversation_id=conversation_id,
                    analysis_type=analysis_type
                )
                
                if not result.get('analyses'):
                    return {'success': False, 'message': 'Análisis no encontrado'}, 404
                
                return result, 200
                
            except Exception as e:
                logger.error(f"Error al obtener análisis: {str(e)}")
                return {'success': False, 'message': str(e)}, 500
        
        @analysis_ns.doc('create_analysis')
        @analysis_ns.expect(analysis_input)
        @analysis_ns.response(201, 'Análisis creado correctamente', model=success_response)
        @analysis_ns.response(400, 'Datos inválidos', model=error_response)
        def post(self, conversation_id):
            """Crea un nuevo análisis para una conversación"""
            try:
                data = request.json
                if not data:
                    return {'success': False, 'message': 'No se proporcionaron datos'}, 400
                
                data['conversation_id'] = conversation_id
                
                if not data.get('client_name'):
                    return {'success': False, 'message': 'El campo client_name es obligatorio'}, 400
                
                result = analysis_service.create_analysis(
                    client_name=data.get('client_name'),
                    analysis_data=data
                )
                
                return {
                    'success': True,
                    'message': 'Análisis creado correctamente',
                    'data': result
                }, 201
                
            except ValidationError as e:
                logger.error(f"Error de validación al crear análisis: {str(e)}")
                return {'success': False, 'message': str(e)}, 400
            except Exception as e:
                logger.error(f"Error al crear análisis: {str(e)}")
                return {'success': False, 'message': str(e)}, 500
        
        @analysis_ns.doc('update_analysis')
        @analysis_ns.expect(analysis_input)
        @analysis_ns.response(200, 'Análisis actualizado correctamente', model=success_response)
        @analysis_ns.response(404, 'Análisis no encontrado', model=error_response)
        def put(self, conversation_id):
            """Actualiza un análisis existente"""
            try:
                data = request.json
                if not data:
                    return {'success': False, 'message': 'No se proporcionaron datos'}, 400
                
                if not data.get('client_name'):
                    return {'success': False, 'message': 'El campo client_name es obligatorio'}, 400
                
                if not data.get('analysis_type'):
                    return {'success': False, 'message': 'El campo analysis_type es obligatorio'}, 400
                
                result = analysis_service.update_analysis(
                    client_name=data.get('client_name'),
                    conversation_id=conversation_id,
                    analysis_type=data.get('analysis_type'),
                    analysis_data=data
                )
                
                return {
                    'success': True,
                    'message': 'Análisis actualizado correctamente',
                    'data': result
                }, 200
                
            except ResourceNotFoundError as e:
                logger.error(f"Análisis no encontrado: {str(e)}")
                return {'success': False, 'message': str(e)}, 404
            except ValidationError as e:
                logger.error(f"Error de validación al actualizar análisis: {str(e)}")
                return {'success': False, 'message': str(e)}, 400
            except Exception as e:
                logger.error(f"Error al actualizar análisis: {str(e)}")
                return {'success': False, 'message': str(e)}, 500
        
        @analysis_ns.doc('delete_analysis')
        @analysis_ns.response(200, 'Análisis eliminado correctamente', model=success_response)
        @analysis_ns.response(404, 'Análisis no encontrado', model=error_response)
        def delete(self, conversation_id):
            """Elimina un análisis existente"""
            try:
                client_name = request.args.get('client_name')
                analysis_type = request.args.get('analysis_type')
                
                if not client_name:
                    return {'success': False, 'message': 'El parámetro client_name es obligatorio'}, 400
                
                # Implementar método de eliminación en el servicio
                # analysis_service.delete_analysis(client_name, conversation_id, analysis_type)
                
                return {
                    'success': True,
                    'message': 'Análisis eliminado correctamente'
                }, 200
                
            except ResourceNotFoundError as e:
                logger.error(f"Análisis no encontrado: {str(e)}")
                return {'success': False, 'message': str(e)}, 404
            except Exception as e:
                logger.error(f"Error al eliminar análisis: {str(e)}")
                return {'success': False, 'message': str(e)}, 500
    
    # Añadir el recurso al namespace
    analysis_ns.add_resource(AnalysisResource, '/<string:conversation_id>')
    
    return AnalysisResource