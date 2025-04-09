"""
Paquete de excepciones personalizadas para la API de SmartVOC.
"""

from exceptions.custom_exceptions import (
    BaseException,
    ValidationError,
    ResourceNotFoundError,
    DuplicateResourceError,
    DatabaseError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError
)

__all__ = [
    'BaseException',
    'ValidationError',
    'ResourceNotFoundError',
    'DuplicateResourceError',
    'DatabaseError',
    'ConfigurationError',
    'AuthenticationError',
    'AuthorizationError',
    'ExternalServiceError'
] 