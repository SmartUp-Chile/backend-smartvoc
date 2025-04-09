"""
Excepciones personalizadas para la API de SmartVOC.
"""

class BaseException(Exception):
    """Excepción base para todas las excepciones personalizadas."""
    def __init__(self, message, error_code=None, status_code=None):
        self.message = message
        self.error_code = error_code or 'generic_error'
        self.status_code = status_code or 500
        super().__init__(self.message)

class ValidationError(BaseException):
    """Excepción para errores de validación de datos."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'validation_error', 400)

class ResourceNotFoundError(BaseException):
    """Excepción para recursos no encontrados."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'not_found', 404)

class DuplicateResourceError(BaseException):
    """Excepción para recursos duplicados."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'duplicate_resource', 409)

class DatabaseError(BaseException):
    """Excepción para errores de base de datos."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'database_error', 500)

class ConfigurationError(BaseException):
    """Excepción para errores de configuración."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'configuration_error', 500)

class AuthenticationError(BaseException):
    """Excepción para errores de autenticación."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'authentication_error', 401)

class AuthorizationError(BaseException):
    """Excepción para errores de autorización."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'authorization_error', 403)

class ExternalServiceError(BaseException):
    """Excepción para errores en servicios externos."""
    def __init__(self, message, error_code=None):
        super().__init__(message, error_code or 'external_service_error', 502) 