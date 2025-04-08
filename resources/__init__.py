# Importaciones directas para evitar importación circular
__all__ = ['HealthResource', 'DBTestResource', 'SmartVOCResource', 'AnalysisResource']

# Las clases se importarán en el momento adecuado, no al cargar el módulo
def register_resources():
    from .health import HealthResource
    from .db import DBTestResource 
    from .smartvoc import SmartVOCResource
    from .analysis import AnalysisResource
    
    return {
        'HealthResource': HealthResource,
        'DBTestResource': DBTestResource,
        'SmartVOCResource': SmartVOCResource,
        'AnalysisResource': AnalysisResource
    } 