"""
Excepciones personalizadas para el sistema.

Este módulo define una jerarquía de excepciones específicas para la aplicación,
permitiendo un manejo más preciso de los errores.
"""

class APIError(Exception):
    """Excepción base para todos los errores de la API."""
    status_code = 500
    error_code = 'internal_error'
    default_message = 'Error interno del servidor'
    
    def __init__(self, message=None, status_code=None, error_code=None, details=None):
        self.message = message or self.default_message
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convierte la excepción a un diccionario para la respuesta JSON."""
        error_dict = {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code
        }
        
        if self.details:
            error_dict["details"] = self.details
            
        return error_dict


# Errores de validación
class ValidationError(APIError):
    """Errores relacionados con la validación de datos de entrada."""
    status_code = 400
    error_code = 'validation_error'
    default_message = 'Los datos proporcionados no son válidos'


# Errores de autenticación
class AuthenticationError(APIError):
    """Errores relacionados con la autenticación."""
    status_code = 401
    error_code = 'authentication_error'
    default_message = 'Error de autenticación'


class AuthorizationError(APIError):
    """Errores relacionados con la autorización y permisos."""
    status_code = 403
    error_code = 'forbidden'
    default_message = 'No tiene permisos para realizar esta acción'


# Errores de recursos
class ResourceNotFoundError(APIError):
    """Error cuando no se encuentra un recurso solicitado."""
    status_code = 404
    error_code = 'not_found'
    default_message = 'El recurso solicitado no existe'


class ResourceAlreadyExistsError(APIError):
    """Error cuando se intenta crear un recurso que ya existe."""
    status_code = 409
    error_code = 'resource_exists'
    default_message = 'El recurso ya existe'


class ResourceConflictError(APIError):
    """Error cuando hay un conflicto al intentar modificar un recurso."""
    status_code = 409
    error_code = 'resource_conflict'
    default_message = 'Conflicto al modificar el recurso'


# Errores de servicio
class DatabaseError(APIError):
    """Errores relacionados con la base de datos."""
    status_code = 500
    error_code = 'database_error'
    default_message = 'Error en la base de datos'


class ExternalServiceError(APIError):
    """Errores relacionados con servicios externos."""
    status_code = 502
    error_code = 'external_service_error'
    default_message = 'Error en un servicio externo'


class RateLimitError(APIError):
    """Error cuando se supera el límite de peticiones."""
    status_code = 429
    error_code = 'rate_limit_exceeded'
    default_message = 'Ha superado el límite de peticiones permitidas'


# Mapeo de excepciones comunes de SQLAlchemy
class SQLAlchemyErrorMapping:
    """Mapea errores específicos de SQLAlchemy a nuestras excepciones personalizadas."""
    
    @staticmethod
    def map_exception(sqlalchemy_error):
        """Mapea un error de SQLAlchemy a una excepción personalizada."""
        from sqlalchemy.exc import IntegrityError, NoResultFound, DataError, OperationalError
        
        error_msg = str(sqlalchemy_error)
        
        if isinstance(sqlalchemy_error, IntegrityError):
            if 'unique constraint' in error_msg.lower():
                return ResourceAlreadyExistsError(
                    message='Ya existe un recurso con esos datos',
                    details={'original_error': error_msg}
                )
            return DatabaseError(
                message='Error de integridad en la base de datos',
                details={'original_error': error_msg}
            )
            
        if isinstance(sqlalchemy_error, NoResultFound):
            return ResourceNotFoundError(
                message='No se encontró el recurso solicitado',
                details={'original_error': error_msg}
            )
            
        if isinstance(sqlalchemy_error, DataError):
            return ValidationError(
                message='Datos inválidos para la base de datos',
                details={'original_error': error_msg}
            )
            
        if isinstance(sqlalchemy_error, OperationalError):
            return DatabaseError(
                message='Error operacional en la base de datos',
                details={'original_error': error_msg}
            )
            
        # Fallback a error genérico de base de datos
        return DatabaseError(
            message='Error en la base de datos',
            details={'original_error': error_msg}
        ) 