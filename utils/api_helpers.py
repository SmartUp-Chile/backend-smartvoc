"""
Utilidades para ayudar en la gestión de la API.
Este módulo contiene funciones para manejar respuestas, errores y códigos de estado.
"""
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def handle_response(result, status_code=200):
    """
    Procesa el resultado de una operación y genera una respuesta HTTP apropiada.
    
    Args:
        result (dict): Resultado de la operación con claves como 'success', 'error', etc.
        status_code (int, opcional): Código de estado HTTP a usar si no se determina uno específico.
    
    Returns:
        tuple: (respuesta_json, código_estado)
    """
    # Si el resultado no es un diccionario, devolverlo tal cual
    if not isinstance(result, dict):
        return jsonify(result), status_code
        
    # Determinar el código de estado en base al resultado
    if 'success' in result and not result['success']:
        # Error en la operación
        if 'error' in result:
            error_message = result.get('error', 'Error desconocido')
            logger.error(f"Error en operación API: {error_message}")
            
            # Determinar código de estado por el tipo de error
            if 'No se encontró' in error_message or 'no existe' in error_message:
                status_code = 404
            elif 'inválido' in error_message or 'requerido' in error_message:
                status_code = 400
            elif 'ya existe' in error_message:
                status_code = 409
            else:
                status_code = 500
    
    # Asegurar que la respuesta tenga un indicador de éxito
    if 'success' not in result:
        result['success'] = status_code < 400
        
    return jsonify(result), status_code 