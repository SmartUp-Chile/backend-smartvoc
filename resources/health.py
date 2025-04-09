from flask_restx import Namespace, Resource, fields
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

# Variables globales para el namespace y modelos
health_ns = None
health_model = None

def init_health_namespace(api):
    """Inicializa el namespace de health y sus modelos."""
    global health_ns, health_model
    
    logger.info("Inicializando namespace de Health...")
    
    # Crear el modelo de respuesta para health
    health_model = api.model('Health', {
        'status': fields.String(description='Estado del servicio', example='running'),
        'version': fields.String(description='Versión de la API', example='1.0.0'),
        'timestamp': fields.DateTime(description='Hora actual del servidor')
    })
    
    # Definir la clase del recurso Health
    class HealthResource(Resource):
        @health_ns.doc('get_health')
        @health_ns.response(200, 'Success', health_model)
        def get(self):
            """Verifica el estado de salud de la API"""
            from datetime import datetime
            return {
                'status': 'running',
                'version': '1.0.0',
                'timestamp': datetime.now()
            }
    
    logger.info("Namespace de Health inicializado correctamente")
    return HealthResource 