"""
Esquemas para validar datos de conversaciones.
"""
from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE, validate, validates_schema

class ConversationPathParamsSchema(Schema):
    """Esquema para validar parámetros de ruta de conversación."""
    conversation_id = fields.String(required=True, validate=validate.Length(min=1, max=255))

class ConversationCreateSchema(Schema):
    """Esquema para validar datos de creación de conversación."""
    class Meta:
        # Ignorar campos extra que no estén en el esquema
        unknown = EXCLUDE
    
    # Campos requeridos
    clientId = fields.String(
        required=True, 
        validate=validate.Length(min=1, max=50),
        error_messages={
            "required": "El ID del cliente es obligatorio",
            "invalid": "El ID del cliente debe ser una cadena de texto",
            "null": "El ID del cliente no puede ser nulo"
        }
    )
    
    # Campos opcionales
    conversationId = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255),
        error_messages={
            "invalid": "El ID de la conversación debe ser una cadena de texto"
        }
    )
    conversation = fields.Dict(
        required=False,
        error_messages={
            "invalid": "La conversación debe ser un objeto JSON"
        }
    )
    metadata = fields.Dict(
        required=False,
        error_messages={
            "invalid": "Los metadatos deben ser un objeto JSON"
        }
    )

class ConversationUpdateSchema(Schema):
    """Esquema para validar datos de actualización de conversación."""
    class Meta:
        # Ignorar campos extra que no estén en el esquema
        unknown = EXCLUDE
    
    # Campos requeridos para identificar la conversación
    clientId = fields.String(
        required=True, 
        validate=validate.Length(min=1, max=50),
        error_messages={
            "required": "El ID del cliente es obligatorio",
            "invalid": "El ID del cliente debe ser una cadena de texto",
            "null": "El ID del cliente no puede ser nulo"
        }
    )
    
    # Campos actualizables
    conversation = fields.Dict(
        required=False,
        error_messages={
            "invalid": "La conversación debe ser un objeto JSON"
        }
    )
    metadata = fields.Dict(
        required=False,
        error_messages={
            "invalid": "Los metadatos deben ser un objeto JSON"
        }
    )
    
    @validates_schema
    def validate_update_data(self, data, **kwargs):
        """Valida que haya al menos un campo actualizable."""
        if not any(key in data for key in ['conversation', 'metadata']):
            raise ValidationError("Debe proporcionar al menos un campo para actualizar")

class ConversationQueryParamsSchema(Schema):
    """Esquema para validar parámetros de consulta para conversaciones."""
    class Meta:
        unknown = EXCLUDE
    
    clientId = fields.String(required=False)
    clientName = fields.String(required=False)
    conversationId = fields.String(required=False)
    limit = fields.Integer(required=False, validate=validate.Range(min=1, max=100), load_default=10)
    offset = fields.Integer(required=False, validate=validate.Range(min=0), load_default=0)
    
    @validates_schema
    def validate_client_params(self, data, **kwargs):
        """Valida que se proporcione al menos un parámetro de cliente."""
        if not any(key in data for key in ['clientId', 'clientName']):
            raise ValidationError({"_schema": ["Debe proporcionar clientId o clientName"]}) 