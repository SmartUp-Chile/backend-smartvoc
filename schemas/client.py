"""
Esquemas para validar datos del modelo SmartVOCClient.
"""
from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE, validate, validates_schema
import re

class ClientPathParamsSchema(Schema):
    """Esquema para validar parámetros de ruta de cliente."""
    client_id = fields.String(required=True, validate=validate.Length(min=1, max=50))

class ClientCreateSchema(Schema):
    """Esquema para validar datos de creación de cliente."""
    class Meta:
        # Ignorar campos extra que no estén en el esquema
        unknown = EXCLUDE
    
    # Campos requeridos
    clientName = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={
            "required": "El nombre del cliente es obligatorio",
            "invalid": "El nombre del cliente debe ser una cadena de texto",
            "null": "El nombre del cliente no puede ser nulo"
        }
    )
    
    # Campos opcionales
    clientWebsite = fields.URL(
        required=False,
        allow_none=True,
        error_messages={
            "invalid": "La URL del sitio web no es válida"
        }
    )
    clientDescription = fields.String(
        required=False, 
        allow_none=True,
        validate=validate.Length(max=1000),
        error_messages={
            "invalid": "La descripción debe ser una cadena de texto"
        }
    )
    clientLanguageDialect = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["es_CL", "es_MX", "es_AR", "es_CO", "es_ES"]),
        error_messages={
            "invalid": "El dialecto debe ser uno de los soportados"
        }
    )
    clientKeywords = fields.String(
        required=False, 
        allow_none=True,
        error_messages={
            "invalid": "Las palabras clave deben ser una cadena de texto"
        }
    )
    
    @validates("clientName")
    def validate_client_name(self, value):
        """Valida que el nombre del cliente sea válido."""
        if not value.strip():
            raise ValidationError("El nombre del cliente no puede estar vacío")
        
        # Nombre no puede contener caracteres especiales excepto espacios, guiones y puntos
        if not re.match(r'^[\w\s\-\.]+$', value):
            raise ValidationError("El nombre del cliente solo puede contener letras, números, espacios, guiones y puntos")

class ClientUpdateSchema(Schema):
    """Esquema para validar datos de actualización de cliente."""
    class Meta:
        # Ignorar campos extra que no estén en el esquema
        unknown = EXCLUDE
    
    # Todos los campos son opcionales en una actualización
    clientName = fields.String(
        required=False,
        validate=validate.Length(min=2, max=100),
        error_messages={
            "invalid": "El nombre del cliente debe ser una cadena de texto"
        }
    )
    clientWebsite = fields.URL(
        required=False,
        allow_none=True,
        error_messages={
            "invalid": "La URL del sitio web no es válida"
        }
    )
    clientDescription = fields.String(
        required=False, 
        allow_none=True,
        validate=validate.Length(max=1000),
        error_messages={
            "invalid": "La descripción debe ser una cadena de texto"
        }
    )
    clientLanguageDialect = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["es_CL", "es_MX", "es_AR", "es_CO", "es_ES"]),
        error_messages={
            "invalid": "El dialecto debe ser uno de los soportados"
        }
    )
    clientKeywords = fields.String(
        required=False, 
        allow_none=True,
        error_messages={
            "invalid": "Las palabras clave deben ser una cadena de texto"
        }
    )
    
    @validates_schema
    def validate_update_data(self, data, **kwargs):
        """Valida que haya al menos un campo para actualizar."""
        if not data:
            raise ValidationError("Debe proporcionar al menos un campo para actualizar")
    
    @validates("clientName")
    def validate_client_name(self, value):
        """Valida que el nombre del cliente sea válido."""
        if value and not value.strip():
            raise ValidationError("El nombre del cliente no puede estar vacío")
        
        # Nombre no puede contener caracteres especiales excepto espacios, guiones y puntos
        if value and not re.match(r'^[\w\s\-\.]+$', value):
            raise ValidationError("El nombre del cliente solo puede contener letras, números, espacios, guiones y puntos")

class ClientQueryParamsSchema(Schema):
    """Esquema para validar parámetros de consulta para clientes."""
    class Meta:
        unknown = EXCLUDE
    
    clientName = fields.String(required=False)
    limit = fields.Integer(required=False, validate=validate.Range(min=1, max=100), load_default=10)
    offset = fields.Integer(required=False, validate=validate.Range(min=0), load_default=0) 