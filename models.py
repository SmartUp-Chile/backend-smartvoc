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