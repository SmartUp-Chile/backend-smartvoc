"""
Manejador global de errores.

Este módulo proporciona funciones para registrar y manejar excepciones
de forma centralizada en toda la aplicación.
"""
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError as MarshmallowValidationError
import traceback
import sys

from utils.exceptions import (
    APIError, 
    ValidationError, 
    ResourceNotFoundError,
    SQLAlchemyErrorMapping
)

def configure_error_handlers(app):
    """Configura los manejadores de errores para la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Maneja las excepciones de tipo APIError."""
        return jsonify(error.to_dict()), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Maneja errores 404 de rutas no encontradas."""
        if isinstance(error, HTTPException):
            return jsonify({
                "error": "not_found",
                "message": "La ruta solicitada no existe",
                "status_code": 404
            }), 404
        return handle_generic_error(error)
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Maneja errores de método HTTP no permitido."""
        return jsonify({
            "error": "method_not_allowed",
            "message": "El método HTTP no está permitido para esta ruta",
            "status_code": 405
        }), 405
    
    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(error):
        """Maneja errores de validación de Marshmallow."""
        validation_error = ValidationError(
            message="Error de validación de datos",
            details=error.messages
        )
        return jsonify(validation_error.to_dict()), validation_error.status_code
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """Maneja errores de SQLAlchemy."""
        # Mapear el error de SQLAlchemy a nuestra jerarquía de excepciones
        api_error = SQLAlchemyErrorMapping.map_exception(error)
        
        # Registrar el error en logs
        current_app.logger.error(
            f"Error de base de datos: {str(error)}\n"
            f"Detalles: {traceback.format_exc()}"
        )
        
        return jsonify(api_error.to_dict()), api_error.status_code
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Maneja cualquier excepción no capturada específicamente."""
        # En desarrollo, podemos mostrar más detalles
        if app.config.get('DEBUG', False):
            error_details = {
                "error": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc().split('\n')
            }
            
            return jsonify({
                "error": "internal_error",
                "message": "Error interno del servidor",
                "details": error_details,
                "status_code": 500
            }), 500
        
        # En producción, solo mostramos un mensaje genérico
        current_app.logger.error(
            f"Error no manejado: {str(error)}\n"
            f"Tipo: {type(error).__name__}\n"
            f"Detalles: {traceback.format_exc()}"
        )
        
        return jsonify({
            "error": "internal_error",
            "message": "Error interno del servidor",
            "status_code": 500
        }), 500

def log_exception(exception):
    """Registra una excepción en los logs de la aplicación.
    
    Args:
        exception: La excepción a registrar
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    # Formatear el traceback como texto
    traceback_details = ''.join(traceback.format_exception(
        exc_type, exc_value, exc_traceback
    ))
    
    # Registrar en el log
    try:
        current_app.logger.error(
            f"Excepción: {type(exception).__name__}\n"
            f"Mensaje: {str(exception)}\n"
            f"Traceback: {traceback_details}"
        )
    except RuntimeError:
        # Fallback si no hay contexto de aplicación
        print(f"ERROR: {type(exception).__name__}: {str(exception)}")
        print(f"Traceback: {traceback_details}") 