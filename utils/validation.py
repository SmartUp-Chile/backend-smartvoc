"""
Utilidades para validación de datos.

Este módulo proporciona funciones y decoradores para validar
datos de entrada en las rutas de la API.
"""
from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from utils.exceptions import ValidationError
from utils.error_handler import log_exception

def validate_with(schema_cls, location='json', **schema_kwargs):
    """
    Decorador para validar datos de entrada usando un esquema Marshmallow.
    
    Args:
        schema_cls: Clase del esquema de Marshmallow
        location: Ubicación de los datos a validar (json, args, form, etc.)
        **schema_kwargs: Argumentos adicionales para el esquema
        
    Returns:
        Decorador para validar datos de entrada
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Obtener los datos según la ubicación
            if location == 'json':
                data = request.get_json()
            elif location == 'args':
                data = request.args.to_dict()
            elif location == 'form':
                data = request.form.to_dict()
            else:
                data = request.get_json()  # Default a JSON
                
            # Si no hay datos, crear un diccionario vacío
            if data is None:
                data = {}
                
            # Crear instancia del esquema y validar
            schema = schema_cls(**schema_kwargs)
            try:
                # Validar y deserializar los datos
                validated_data = schema.load(data)
                # Agregar los datos validados a kwargs para la función decorada
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except MarshmallowValidationError as err:
                # Convertir a nuestra excepción personalizada
                log_exception(err)
                raise ValidationError(
                    message="Error de validación de datos",
                    details=err.messages
                )
                
        return wrapper
    return decorator

def validate_path_params(schema_cls, **schema_kwargs):
    """
    Decorador para validar parámetros de ruta usando un esquema Marshmallow.
    
    Args:
        schema_cls: Clase del esquema de Marshmallow
        **schema_kwargs: Argumentos adicionales para el esquema
        
    Returns:
        Decorador para validar parámetros de ruta
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Extraer parámetros de ruta
            path_params = {k: v for k, v in kwargs.items()}
            
            # Crear instancia del esquema y validar
            schema = schema_cls(**schema_kwargs)
            try:
                # Validar y deserializar los datos
                validated_params = schema.load(path_params)
                # Actualizar kwargs con los parámetros validados
                kwargs.update(validated_params)
                return f(*args, **kwargs)
            except MarshmallowValidationError as err:
                # Convertir a nuestra excepción personalizada
                log_exception(err)
                raise ValidationError(
                    message="Error de validación en parámetros de ruta",
                    details=err.messages
                )
                
        return wrapper
    return decorator 