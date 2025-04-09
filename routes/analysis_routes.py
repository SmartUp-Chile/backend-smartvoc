from flask import Blueprint, request, jsonify
import logging
from services.analysis_service import AnalysisService
from exceptions.custom_exceptions import ResourceNotFoundError, ValidationError

# Configuración de logging
logger = logging.getLogger(__name__)

# Crear blueprint para rutas de análisis
bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

# Inicializar el servicio de análisis
analysis_service = AnalysisService()

@bp.route('/<client_name>/<conversation_id>', methods=['GET'])
def get_analysis(client_name, conversation_id):
    """Obtiene análisis para una conversación específica"""
    try:
        # Obtener tipo de análisis del query param si existe
        analysis_type = request.args.get('analysis_type')
        
        # Obtener análisis usando el servicio
        result = analysis_service.get_client_analyses(
            client_name=client_name,
            conversation_id=conversation_id,
            analysis_type=analysis_type
        )
        
        return jsonify(result)
    except ResourceNotFoundError as e:
        logger.error(f"Error al obtener análisis: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error interno al obtener análisis: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error interno: {str(e)}"
        }), 500

@bp.route('/<client_name>', methods=['POST'])
def create_analysis(client_name):
    """Crea un nuevo análisis para una conversación"""
    try:
        # Validar datos de entrada
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Se esperaba contenido JSON"
            }), 400
            
        data = request.get_json()
        
        # Crear análisis usando el servicio
        result = analysis_service.create_analysis(
            client_name=client_name,
            analysis_data=data
        )
        
        return jsonify({
            "success": True,
            "analysis": result
        }), 201
    except ValidationError as e:
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error interno al crear análisis: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error interno: {str(e)}"
        }), 500

@bp.route('/<client_name>/<conversation_id>/<analysis_type>', methods=['PUT'])
def update_analysis(client_name, conversation_id, analysis_type):
    """Actualiza un análisis existente"""
    try:
        # Validar datos de entrada
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Se esperaba contenido JSON"
            }), 400
            
        data = request.get_json()
        
        # Actualizar análisis usando el servicio
        result = analysis_service.update_analysis(
            client_name=client_name,
            conversation_id=conversation_id,
            analysis_type=analysis_type,
            analysis_data=data
        )
        
        return jsonify({
            "success": True,
            "analysis": result
        })
    except ResourceNotFoundError as e:
        logger.error(f"Análisis no encontrado: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except ValidationError as e:
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error interno al actualizar análisis: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error interno: {str(e)}"
        }), 500

@bp.route('/<client_name>/<conversation_id>/<analysis_type>', methods=['DELETE'])
def delete_analysis(client_name, conversation_id, analysis_type):
    """Elimina un análisis existente"""
    try:
        # Eliminar análisis usando el servicio
        result = analysis_service.delete_analysis(
            client_name=client_name,
            conversation_id=conversation_id,
            analysis_type=analysis_type
        )
        
        return jsonify({
            "success": True,
            "message": "Análisis eliminado correctamente"
        })
    except ResourceNotFoundError as e:
        logger.error(f"Análisis no encontrado: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error interno al eliminar análisis: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error interno: {str(e)}"
        }), 500 