"""
Utilidades para la creación de modelos de API.
Este módulo contiene funciones para crear y manejar modelos de datos para la API.
"""
from flask_restx import fields

def create_response_model(namespace, name, model_fields):
    """
    Crea un modelo de respuesta con estructura estándar.
    
    Args:
        namespace: El espacio de nombres de Flask-RESTX donde registrar el modelo
        name (str): Nombre del modelo a crear
        model_fields (dict): Campos específicos del modelo
        
    Returns:
        Model: El modelo creado
    """
    # Campos base para todos los modelos de respuesta
    base_fields = {
        'success': fields.Boolean(default=True, description='Indica si la operación fue exitosa'),
    }
    
    # Combinar campos base con campos específicos
    combined_fields = {**base_fields, **model_fields}
    
    # Crear y retornar el modelo
    return namespace.model(name, combined_fields)

def create_pagination_models(namespace):
    """
    Crea modelos para paginación.
    
    Args:
        namespace: El espacio de nombres de Flask-RESTX donde registrar los modelos
        
    Returns:
        tuple: (modelo_paginación, modelo_enlaces)
    """
    # Modelo para enlaces de paginación
    pagination_links = namespace.model('PaginationLinks', {
        'self': fields.String(description='Enlace a la página actual'),
        'next': fields.String(description='Enlace a la página siguiente', nullable=True),
        'prev': fields.String(description='Enlace a la página anterior', nullable=True),
        'first': fields.String(description='Enlace a la primera página'),
        'last': fields.String(description='Enlace a la última página')
    })
    
    # Modelo para información de paginación
    pagination = namespace.model('Pagination', {
        'page': fields.Integer(description='Página actual', example=1),
        'per_page': fields.Integer(description='Elementos por página', example=10),
        'total_pages': fields.Integer(description='Total de páginas', example=5),
        'total_items': fields.Integer(description='Total de elementos', example=42)
    })
    
    return pagination, pagination_links 