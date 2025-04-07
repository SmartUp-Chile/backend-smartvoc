from app import db
from datetime import datetime

# Modelo simple para probar la conexión a la base de datos
class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RequestLog {self.endpoint} {self.timestamp}>'

# Modelo para los clientes de SmartVOC
class SmartVOCClient(db.Model):
    __tablename__ = 'SmartVOCClients'
    
    clientId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    clientName = db.Column(db.String(100), nullable=False, unique=True)
    clientSlug = db.Column(db.String(100), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SmartVOCClient {self.clientName}>'
        
    def to_dict(self):
        return {
            'clientId': self.clientId,
            'clientName': self.clientName,
            'clientSlug': self.clientSlug,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None
        } 