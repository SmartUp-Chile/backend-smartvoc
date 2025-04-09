"""
Esquemas de validación para análisis de conversaciones
"""

analysis_schema = {
    "type": "object",
    "required": ["clientName", "conversationId"],
    "properties": {
        "clientName": {
            "type": "string",
            "description": "Nombre del cliente"
        },
        "conversationId": {
            "type": "string",
            "description": "ID de la conversación analizada"
        },
        "batchRunId": {
            "type": ["string", "null"],
            "description": "ID del lote de procesamiento (opcional)"
        },
        "analysisType": {
            "type": "string",
            "enum": ["basic", "deep", "sentiment", "summary", "topics", "gsc"],
            "default": "basic",
            "description": "Tipo de análisis realizado"
        },
        "isComplete": {
            "type": "boolean",
            "default": False,
            "description": "Indica si el análisis está completo"
        },
        "statusCode": {
            "type": ["integer", "null"],
            "description": "Código de estado del procesamiento"
        },
        "errorMessage": {
            "type": ["string", "null"],
            "description": "Mensaje de error en caso de fallo"
        },
        "processingTimeMs": {
            "type": ["number", "null"],
            "description": "Tiempo de procesamiento en milisegundos"
        },
        "sentiment": {
            "type": ["object", "null"],
            "description": "Análisis de sentimiento",
            "properties": {
                "score": {
                    "type": "number",
                    "description": "Puntuación de sentimiento (-1 a 1)"
                },
                "magnitude": {
                    "type": "number",
                    "description": "Magnitud del sentimiento"
                },
                "label": {
                    "type": "string",
                    "description": "Etiqueta del sentimiento (positivo, negativo, neutral)"
                }
            }
        },
        "topics": {
            "type": ["array", "null"],
            "description": "Temas identificados en la conversación",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre del tema"
                    },
                    "score": {
                        "type": "number",
                        "description": "Puntuación de relevancia del tema"
                    },
                    "mentions": {
                        "type": "integer",
                        "description": "Número de menciones del tema"
                    }
                }
            }
        },
        "summary": {
            "type": ["string", "null"],
            "description": "Resumen de la conversación"
        },
        "deepAnalysis": {
            "type": ["object", "null"],
            "description": "Análisis profundo de la conversación",
            "additionalProperties": True
        },
        "gscAnalysis": {
            "type": ["object", "null"],
            "description": "Análisis GSC de la conversación",
            "additionalProperties": True
        },
        "metadata": {
            "type": ["object", "null"],
            "description": "Metadatos adicionales del análisis",
            "additionalProperties": True
        }
    },
    "additionalProperties": False
}

analysis_update_schema = {
    "type": "object",
    "properties": {
        "analysisType": {
            "type": "string",
            "enum": ["basic", "deep", "sentiment", "summary", "topics", "gsc"],
            "description": "Tipo de análisis realizado"
        },
        "isComplete": {
            "type": "boolean",
            "description": "Indica si el análisis está completo"
        },
        "statusCode": {
            "type": ["integer", "null"],
            "description": "Código de estado del procesamiento"
        },
        "errorMessage": {
            "type": ["string", "null"],
            "description": "Mensaje de error en caso de fallo"
        },
        "processingTimeMs": {
            "type": ["number", "null"],
            "description": "Tiempo de procesamiento en milisegundos"
        },
        "sentiment": {
            "type": ["object", "null"],
            "description": "Análisis de sentimiento",
            "properties": {
                "score": {
                    "type": "number",
                    "description": "Puntuación de sentimiento (-1 a 1)"
                },
                "magnitude": {
                    "type": "number",
                    "description": "Magnitud del sentimiento"
                },
                "label": {
                    "type": "string",
                    "description": "Etiqueta del sentimiento (positivo, negativo, neutral)"
                }
            }
        },
        "topics": {
            "type": ["array", "null"],
            "description": "Temas identificados en la conversación",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre del tema"
                    },
                    "score": {
                        "type": "number",
                        "description": "Puntuación de relevancia del tema"
                    },
                    "mentions": {
                        "type": "integer",
                        "description": "Número de menciones del tema"
                    }
                }
            }
        },
        "summary": {
            "type": ["string", "null"],
            "description": "Resumen de la conversación"
        },
        "deepAnalysis": {
            "type": ["object", "null"],
            "description": "Análisis profundo de la conversación",
            "additionalProperties": True
        },
        "gscAnalysis": {
            "type": ["object", "null"],
            "description": "Análisis GSC de la conversación",
            "additionalProperties": True
        },
        "metadata": {
            "type": ["object", "null"],
            "description": "Metadatos adicionales del análisis",
            "additionalProperties": True
        }
    },
    "additionalProperties": False
} 