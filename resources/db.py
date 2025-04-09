from flask_restx import Namespace, Resource, fields
import logging
from app import db
from models import RequestLog

# Configuración de logging
logger = logging.getLogger(__name__)

# Variables globales para el namespace y modelos
db_ns = None
db_test_model = None

def init_db_namespace(api):
    """Inicializa el namespace de DB y sus modelos"""
    global db_ns, db_test_model
    
    logger.info("Inicializando namespace de DB...")
    
    # Crear el modelo de respuesta para db test
    db_test_model = api.model('DBTest', {
        'status': fields.String(description='Estado de la conexión a la BD', example='success'),
        'message': fields.String(description='Mensaje con detalles de la prueba'),
        'tables': fields.List(fields.String, description='Lista de tablas encontradas')
    })
    
    # Definir la clase del recurso DBTest
    class DBTestResource(Resource):
        @db_ns.doc('test_db_connection')
        @db_ns.response(200, 'Success', db_test_model)
        @db_ns.response(500, 'Error de conexión')
        def get(self):
            """Verifica la conexión con la base de datos"""
            try:
                # Ejecutar una consulta simple para listar tablas
                result = db.engine.execute("SHOW TABLES")
                tables = [row[0] for row in result]
                
                return {
                    'status': 'success',
                    'message': 'Conexión a la base de datos exitosa',
                    'tables': tables
                }
            except Exception as e:
                logger.error(f"Error al probar la conexión a la BD: {str(e)}")
                return {
                    'status': 'error',
                    'message': f'Error de conexión: {str(e)}',
                    'tables': []
                }, 500
    
    logger.info("Namespace de DB inicializado correctamente")
    return DBTestResource 