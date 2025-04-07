from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class RequestLog(Base):
    """Modelo para registrar las solicitudes HTTP."""
    __tablename__ = 'request_logs'
    
    id = None
    endpoint = None
    method = None
    status_code = None
    response_time = None
    ip_address = None
    user_agent = None
    created_at = None
    
    def __init__(self, endpoint, method, status_code, response_time, ip_address, user_agent):
        self.endpoint = endpoint
        self.method = method
        self.status_code = status_code
        self.response_time = response_time
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<RequestLog {self.endpoint} {self.method} {self.status_code}>"
        
class SmartVOCClient(Base):
    """Modelo para manejar los clientes de SmartVOC."""
    __tablename__ = 'SmartVOCClients'
    
    clientId = None
    clientName = None 
    clientSlug = None
    createdAt = None
    
    def __init__(self, clientName, clientSlug):
        self.clientName = clientName
        self.clientSlug = clientSlug
        self.createdAt = datetime.utcnow()
    
    def __repr__(self):
        return f"<SmartVOCClient {self.clientName}>"
    
    def to_dict(self):
        """Convierte el objeto a un diccionario para serialización JSON."""
        return {
            'clientId': self.clientId,
            'clientName': self.clientName,
            'clientSlug': self.clientSlug,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None
        }

class SmartVOCConversation:
    """Clase para manejar las conversaciones de SmartVOC.
    
    Esta es una representación genérica, ya que las conversaciones
    reales se almacenan en tablas dinámicas específicas para cada cliente.
    """
    
    @staticmethod
    def get_table_name(client_slug):
        """Obtiene el nombre de la tabla para un cliente específico."""
        return f"Conversations__{client_slug}"
    
    @staticmethod
    def to_dict(row):
        """Convierte una fila de la base de datos a un diccionario."""
        result = dict(row)
        
        # Convertir campos JSON
        for field in ['conversation', 'metadata', 'analysis']:
            if field in result and result[field]:
                try:
                    result[field] = json.loads(result[field])
                except (TypeError, json.JSONDecodeError):
                    result[field] = {}
        
        # Formatear fechas
        if 'createdAt' in result and result['createdAt']:
            result['createdAt'] = result['createdAt'].isoformat()
            
        return result 