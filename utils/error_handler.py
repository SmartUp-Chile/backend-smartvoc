"""
Manejador global de errores.

Este módulo proporciona funciones para registrar y manejar excepciones
de forma centralizada en toda la aplicación.
"""
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from marshmallow import ValidationError as MarshmallowValidationError
import traceback
import sys
import logging
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from exceptions.custom_exceptions import (
    BaseException,
    ValidationError, 
    ResourceNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)

def configure_error_handlers(app):
    """Configura los manejadores de errores para la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    
    @app.errorhandler(BaseException)
    def handle_api_error(error):
        """Maneja las excepciones de tipo APIError."""
        return jsonify({
            "success": False,
            "error": str(error),
            "errorCode": error.error_code
        }), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Maneja errores 404 de rutas no encontradas."""
        if isinstance(error, HTTPException):
            return jsonify({
                "success": False,
                "error": "La ruta solicitada no existe",
                "errorCode": "NOT_FOUND"
            }), 404
        return handle_generic_error(error)
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Maneja errores de método HTTP no permitido."""
        return jsonify({
            "success": False,
            "error": "El método HTTP no está permitido para esta ruta",
            "errorCode": "METHOD_NOT_ALLOWED"
        }), 405
    
    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(error):
        """Maneja errores de validación de Marshmallow."""
        return jsonify({
            "success": False,
            "error": "Error de validación de datos",
            "errorCode": "VALIDATION_ERROR",
            "details": error.messages
        }), 400
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """Maneja errores de SQLAlchemy."""
        # Mapear el error de SQLAlchemy a nuestra jerarquía de excepciones
        result = _handle_sqlalchemy_error(error)
        
        # Registrar el error en logs
        current_app.logger.error(
            f"Error de base de datos: {str(error)}\n"
            f"Detalles: {traceback.format_exc()}"
        )
        
        return result
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Maneja cualquier excepción no capturada específicamente."""
        # En desarrollo, podemos mostrar más detalles
        if app.config.get('DEBUG', False):
            error_details = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc().split('\n')
            }
            
            return jsonify({
                "success": False,
                "error": "Error interno del servidor",
                "errorCode": "INTERNAL_ERROR",
                "details": error_details
            }), 500
        
        # En producción, solo mostramos un mensaje genérico
        current_app.logger.error(
            f"Error no manejado: {str(error)}\n"
            f"Tipo: {type(error).__name__}\n"
            f"Detalles: {traceback.format_exc()}"
        )
        
        return jsonify({
            "success": False,
            "error": "Error interno del servidor",
            "errorCode": "INTERNAL_ERROR"
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

def parse_exceptions(exception):
    """
    Maneja excepciones y genera respuestas de error estandarizadas.
    
    Args:
        exception: La excepción capturada
        
    Returns:
        tuple: (respuesta_json, código_estado)
    """
    # Excepciones personalizadas
    if isinstance(exception, BaseException):
        logger.error(f"Error personalizado: {str(exception)}")
        return {
            "success": False,
            "error": str(exception),
            "errorCode": exception.error_code
        }, exception.status_code
    
    # Errores de validación de JSON Schema
    if isinstance(exception, JsonSchemaValidationError):
        logger.error(f"Error de validación JSON Schema: {str(exception)}")
        return {
            "success": False,
            "error": str(exception),
            "errorCode": "VALIDATION_ERROR"
        }, 400
    
    # Errores de SQLAlchemy
    if isinstance(exception, SQLAlchemyError):
        return _handle_sqlalchemy_error(exception)
    
    # Errores genéricos
    logger.error(f"Error no manejado: {type(exception).__name__}: {str(exception)}")
    
    # En modo desarrollo, incluir más detalles del error
    if current_app.config.get('DEBUG', False):
        return {
            "success": False,
            "error": f"{type(exception).__name__}: {str(exception)}",
            "errorCode": "SERVER_ERROR",
            "details": {
                "type": type(exception).__name__,
                "message": str(exception)
            }
        }, 500
    else:
        # En producción, mensaje genérico
        return {
            "success": False,
            "error": "Error interno del servidor",
            "errorCode": "SERVER_ERROR"
        }, 500

def _handle_sqlalchemy_error(exception):
    """
    Maneja específicamente errores de SQLAlchemy.
    
    Args:
        exception: Excepción de SQLAlchemy
        
    Returns:
        tuple: (respuesta_json, código_estado)
    """
    # Log del error para debugging
    logger.error(f"Error de base de datos: {str(exception)}")
    
    # Errores de integridad (violación de constraints, duplicados, etc.)
    if isinstance(exception, IntegrityError):
        if 'unique constraint' in str(exception).lower() or 'duplicate' in str(exception).lower():
            return {
                "success": False,
                "error": "El recurso ya existe en la base de datos",
                "errorCode": "DUPLICATE_RESOURCE"
            }, 409
        return {
            "success": False, 
            "error": "Error de integridad en la base de datos",
            "errorCode": "INTEGRITY_ERROR"
        }, 400
    
    # Errores operacionales (tabla no existe, conexión fallida, etc.)
    if isinstance(exception, OperationalError):
        if 'no such table' in str(exception).lower():
            return {
                "success": False,
                "error": "La tabla solicitada no existe",
                "errorCode": "TABLE_NOT_FOUND"
            }, 404
        return {
            "success": False,
            "error": "Error de operación en la base de datos",
            "errorCode": "DATABASE_ERROR"
        }, 500
    
    # Otros errores de SQLAlchemy
    return {
        "success": False,
        "error": "Error en la operación de base de datos",
        "errorCode": "DATABASE_ERROR"
    }, 500 