from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Table, MetaData, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from db import Base, db_session
from flask import current_app
import logging

# Base ya está definida en db.py, no es necesario crear una nueva instancia
# Base = declarative_base()

# Logger de fallback en caso que current_app no esté disponible
logger = logging.getLogger(__name__)

def log_error(message):
    """Función de utilidad para logging"""
    try:
        current_app.logger.error(message)
    except Exception:
        logger.error(message)

class RequestLog(Base):
    """Modelo para registrar las solicitudes HTTP."""
    __tablename__ = 'request_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    endpoint = Column(String(255))
    method = Column(String(10))
    request_data = Column(Text)
    response_data = Column(Text)
    status_code = Column(Integer)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    response_time = Column(Integer, nullable=True)

class SmartVOCClient(Base):
    """Modelo para manejar los clientes de SmartVOC."""
    __tablename__ = 'smartvoc_clients'
    
    clientId = Column(Integer, primary_key=True, autoincrement=True)
    clientName = Column(String(100), nullable=False, unique=True)
    clientSlug = Column(String(100), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convierte el objeto a un diccionario."""
        return {
            'clientId': self.clientId,
            'clientName': self.clientName,
            'clientSlug': self.clientSlug,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None
        }

class ClientDetails(Base):
    """Modelo para detalles adicionales de clientes."""
    __tablename__ = 'client_details'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(50), ForeignKey('smartvoc_clients.clientId'), nullable=False)
    client_name = Column(String(100), nullable=False)
    client_website = Column(String(255))
    client_description = Column(Text)
    client_language_dialect = Column(String(50))
    client_keywords = Column(String(255))
    client_slug = Column(String(255))
    copilot_table_name = Column(String(255))
    auto_field_group = Column(String(255))
    auto_category_group = Column(String(255))
    auto_agent_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("SmartVOCClient", backref="details")
    
    def to_dict(self):
        """Convierte el objeto a un diccionario."""
        return {
            'clientId': self.client_id,
            'clientName': self.client_name,
            'clientWebsite': self.client_website,
            'clientDescription': self.client_description,
            'clientLanguageDialect': self.client_language_dialect,
            'clientKeywords': self.client_keywords,
            'clientSlug': self.client_slug,
            'copilotTableName': self.copilot_table_name,
            'autoFieldGroup': self.auto_field_group,
            'autoCategoryGroup': self.auto_category_group,
            'autoAgentName': self.auto_agent_name,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class FieldGroup(Base):
    """Modelo para grupos de campos y categorías."""
    __tablename__ = 'field_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    field_group_id = Column(Integer, nullable=False)
    client_id = Column(String(50), ForeignKey('smartvoc_clients.clientId'), nullable=False)
    field_name = Column(String(100), nullable=False)
    client_name = Column(String(100), nullable=False)
    field_and_categories = Column(JSON)
    generated_fields_and_categories = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("SmartVOCClient", backref="field_groups")
    
    def to_dict(self):
        """Convierte el objeto a un diccionario."""
        return {
            'fieldGroupId': self.field_group_id,
            'clientId': self.client_id,
            'clientName': self.client_name,
            'fieldName': self.field_name,
            'fieldAndCategories': self.field_and_categories,
            'generatedFieldsAndCategories': self.generated_fields_and_categories,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class GenerativeAnalysis(Base):
    """Modelo para análisis generativos de conversaciones."""
    __tablename__ = 'generative_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(255), nullable=False)
    batch_run_id = Column(String(255))
    deep_analysis = Column(JSON)
    gsc_analysis = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='PROCESSING')  # PROCESSING, COMPLETED, FAILED
    analysis_type = Column(String(50))  # DeepAnalysis, CategoryAssignment
    client_id = Column(String(50), ForeignKey('smartvoc_clients.clientId'), nullable=False)
    
    client = relationship("SmartVOCClient", backref="generative_analyses")
    
    def to_dict(self):
        """Convierte el objeto a un diccionario."""
        return {
            'conversationId': self.conversation_id,
            'batchRunId': self.batch_run_id,
            'deepAnalysis': self.deep_analysis,
            'gscAnalysis': self.gsc_analysis,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'analysisType': self.analysis_type,
            'clientId': self.client_id
        }

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), nullable=False)
    client_id = Column(String(50), ForeignKey('smartvoc_clients.clientId'), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # e.g., 'sentiment', 'intent', 'entities'
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("SmartVOCClient", backref="analyses")
    
    def to_dict(self):
        """Convierte el objeto a un diccionario."""
        return {
            'conversationId': self.conversation_id,
            'clientId': self.client_id,
            'analysisType': self.analysis_type,
            'result': self.result,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
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
            try:
                if hasattr(result['createdAt'], 'isoformat'):
                    result['createdAt'] = result['createdAt'].isoformat()
            except:
                # Si ocurre algún error, dejamos la fecha como está
                pass
            
        return result

class DynamicTableManager:
    """Clase para manejar la creación y gestión de tablas dinámicas."""
    
    @staticmethod
    def create_conversation_table(client_slug):
        """Crea una tabla dinámica de conversaciones para un cliente específico."""
        table_name = f"Conversations__{client_slug}"
        metadata = MetaData()
        
        # Definir la estructura de la tabla
        table = Table(
            table_name, 
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('conversation_id', String(255), nullable=False),
            Column('client_id', String(50), nullable=False),
            Column('conversation', JSON),
            Column('metadata', JSON),
            Column('deep_analysis_stage', String(50)),
            Column('gsc_analysis_stage', String(50)),
            Column('batch_custom_name', String(255)),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('deep_analysis_batch_id', String(255)),
            Column('gsc_analysis_batch_id', String(255)),
            Column('analysis', JSON),
            Column('auto_processing_status', String(50))
        )
        
        # Crear la tabla en la base de datos
        try:
            engine = db_session.get_bind()
            metadata.create_all(engine)
            return True
        except Exception as e:
            db_session.rollback()
            log_error(f"Error al crear la tabla {table_name}: {str(e)}")
            return False
    
    @staticmethod
    def create_quote_table(client_slug):
        """Crea una tabla dinámica de citas categorizadas para un cliente específico."""
        table_name = f"CopilotFieldCategoryQuote__{client_slug}"
        metadata = MetaData()
        
        # Definir la estructura de la tabla
        table = Table(
            table_name, 
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('conversation_id', String(255), nullable=False),
            Column('conversation_group_id', String(255)),
            Column('field', String(255), nullable=False),
            Column('category', String(255), nullable=False),
            Column('quote', Text, nullable=False),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Crear la tabla en la base de datos
        try:
            engine = db_session.get_bind()
            metadata.create_all(engine)
            return True
        except Exception as e:
            db_session.rollback()
            log_error(f"Error al crear la tabla {table_name}: {str(e)}")
            return False
    
    @staticmethod
    def table_exists(table_name):
        """Verifica si una tabla existe en la base de datos."""
        try:
            engine = db_session.get_bind()
            inspector = inspect(engine)
            return inspector.has_table(table_name)
        except Exception as e:
            log_error(f"Error al verificar si la tabla {table_name} existe: {str(e)}")
            return False
    
    @staticmethod
    def execute_query(query, params=None):
        """Ejecuta una consulta SQL directamente."""
        try:
            if params:
                result = db_session.execute(text(query), params)
            else:
                result = db_session.execute(text(query))
            db_session.commit()
            return result
        except Exception as e:
            db_session.rollback()
            log_error(f"Error al ejecutar la consulta: {str(e)}")
            raise 