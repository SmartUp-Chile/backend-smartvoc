"""
Esquemas para validar datos de análisis de conversaciones.
"""
from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE, validate, validates_schema

class AnalysisPathParamsSchema(Schema):
    """Esquema para validar parámetros de ruta de análisis."""
    client_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    conversation_id = fields.String(required=True, validate=validate.Length(min=1, max=255))

class AnalysisCreateSchema(Schema):
    """Esquema para validar datos de creación de análisis."""
    class Meta:
        # Ignorar campos extra que no estén en el esquema
        unknown = EXCLUDE
    
    # Parámetros para análisis automático con OpenAI
    performAIAnalysis = fields.Boolean(required=False, load_default=False)
    conversationData = fields.Dict(required=False)
    
    # Parámetros para análisis manual
    deepAnalysis = fields.Dict(required=False)
    gscAnalysis = fields.Dict(required=False)
    analysisType = fields.String(
        required=False, 
        validate=validate.OneOf(["standard", "sentiment", "intent", "entities", "summary", "custom"]),
        load_default="standard"
    )
    batchRunId = fields.String(required=False)
    
    @validates_schema
    def validate_analysis_data(self, data, **kwargs):
        """Valida que los datos de análisis sean coherentes."""
        # Si se solicita análisis automático, debe proporcionarse los datos de conversación
        if data.get('performAIAnalysis') and not data.get('conversationData'):
            raise ValidationError({"conversationData": ["Para realizar un análisis automático debe proporcionar los datos de la conversación"]})
        
        # Si no se solicita análisis automático, debe proporcionarse al menos un tipo de análisis
        if not data.get('performAIAnalysis') and not any(key in data for key in ['deepAnalysis', 'gscAnalysis']):
            raise ValidationError({"_schema": ["Debe proporcionar al menos un tipo de análisis (deepAnalysis o gscAnalysis)"]})

class AnalysisUpdateSchema(Schema):
    """Esquema para validar datos de actualización de análisis."""
    class Meta:
        # Ignorar campos extra que no estén en el esquema
        unknown = EXCLUDE
    
    # Parámetros para análisis automático con OpenAI
    performAIAnalysis = fields.Boolean(required=False)
    conversationData = fields.Dict(required=False)
    
    # Parámetros para actualización manual
    deepAnalysis = fields.Dict(required=False)
    gscAnalysis = fields.Dict(required=False)
    analysisType = fields.String(
        required=False, 
        validate=validate.OneOf(["standard", "sentiment", "intent", "entities", "summary", "custom"])
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(["PROCESSING", "COMPLETED", "FAILED"])
    )
    
    @validates_schema
    def validate_update_data(self, data, **kwargs):
        """Valida que haya al menos un campo para actualizar."""
        update_fields = ['deepAnalysis', 'gscAnalysis', 'analysisType', 'status', 'performAIAnalysis']
        if not any(key in data for key in update_fields):
            raise ValidationError({"_schema": ["Debe proporcionar al menos un campo para actualizar"]})
        
        # Si se solicita análisis automático, debe proporcionarse los datos de conversación
        if data.get('performAIAnalysis') and not data.get('conversationData'):
            raise ValidationError({"conversationData": ["Para realizar un análisis automático debe proporcionar los datos de la conversación"]})

class AnalysisQueryParamsSchema(Schema):
    """Esquema para validar parámetros de consulta para análisis."""
    class Meta:
        unknown = EXCLUDE
    
    conversationId = fields.String(required=False)
    batchRunId = fields.String(required=False)
    analysisType = fields.String(required=False)
    
    # No necesita validación adicional porque todos los campos son opcionales 