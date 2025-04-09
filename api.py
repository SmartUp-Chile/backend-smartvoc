from flask_restx import Api
import logging
from resources.health import health_ns, init_health_namespace
from resources.db import db_ns, init_db_namespace
from resources.smartvoc import smartvoc_ns, init_smartvoc_namespace
from resources.analysis import analysis_ns, init_analysis_namespace

# Configuración de logging
logger = logging.getLogger(__name__)

# Inicializar la API
api = Api(
    version='1.0',
    title='SmartVOC API',
    description='API para la gestión de conversaciones y análisis',
    doc='/api/docs',
    prefix='/api'
)

# Registrar namespaces
api.add_namespace(health_ns)
api.add_namespace(db_ns)
api.add_namespace(analysis_ns)

# Inicializar recursos (ahora la función init_analysis_namespace no necesita el parámetro api)
init_analysis_namespace()

# Inicializar los namespaces
def init_api():
    """
    Inicializa la API y registra los namespaces
    """
    # Inicializa los namespaces
    resources = {}
    
    # Health namespace
    resources['HealthResource'] = init_health_namespace()
    api.add_namespace(health_ns, path='/health')
    
    # DB namespace
    resources['DBResource'] = init_db_namespace()
    api.add_namespace(db_ns, path='/db')
    
    # SmartVOC namespace
    resources['SmartVOCResource'] = init_smartvoc_namespace()
    api.add_namespace(smartvoc_ns, path='/smartvoc')
    
    # Analysis namespace
    resources['AnalysisResource'] = init_analysis_namespace()
    api.add_namespace(analysis_ns, path='/analysis')
    
    # Registra los recursos
    smartvoc_ns.add_resource(resources['SmartVOCResource'], '')
    health_ns.add_resource(resources['HealthResource'], '')
    db_ns.add_resource(resources['DBResource'], '/test')
    analysis_ns.add_resource(resources['AnalysisResource'], '/<string:conversation_id>')
    
    return api 