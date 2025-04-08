"""
Servicio para el análisis de conversaciones.
Este módulo contiene todas las funcionalidades relacionadas con 
el análisis de conversaciones utilizando diferentes servicios de IA.
"""
import os
import json
import logging
from datetime import datetime
from sqlalchemy import text, MetaData, Table, Column, Integer, String, DateTime, JSON, create_engine
from sqlalchemy.exc import SQLAlchemyError, NoSuchTableError

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Servicio para el análisis de conversaciones.
    Esta clase maneja todas las operaciones relacionadas con el análisis
    de conversaciones, incluyendo la creación, recuperación y actualización de análisis.
    """
    
    def __init__(self, db_session):
        """
        Inicializa el servicio de análisis.
        
        Args:
            db_session: Sesión de base de datos SQLAlchemy
        """
        self.db_session = db_session
        
    def _get_analysis_table_name(self, client_name):
        """
        Obtiene el nombre de la tabla de análisis para un cliente específico.
        Normaliza el nombre del cliente reemplazando espacios por guiones bajos
        y eliminando caracteres especiales.
        
        Args:
            client_name: Nombre del cliente
            
        Returns:
            str: Nombre de la tabla de análisis
        """
        # Normalizar el nombre del cliente para SQL
        normalized_name = client_name.replace(" ", "_").replace("-", "_")
        # Eliminar cualquier otro carácter especial
        normalized_name = ''.join(c for c in normalized_name if c.isalnum() or c == '_')
        return f"GenerativeAnalyses__{normalized_name}"
    
    def _ensure_analysis_table_exists(self, client_name):
        """
        Asegura que la tabla de análisis existe para el cliente especificado.
        Si no existe, la crea.
        
        Args:
            client_name: Nombre del cliente
            
        Returns:
            bool: True si la tabla existía o fue creada exitosamente, False en caso contrario
        """
        table_name = self._get_analysis_table_name(client_name)
        
        # Verificar si la tabla ya existe
        try:
            self.db_session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
            logger.info(f"Tabla {table_name} ya existe")
            return True
        except SQLAlchemyError:
            # La tabla no existe, crearla
            try:
                metadata = MetaData()
                Table(
                    table_name,
                    metadata,
                    Column('id', Integer, primary_key=True, autoincrement=True),
                    Column('conversationId', String(255), nullable=False, index=True),
                    Column('batchRunId', String(255), nullable=True, index=True),
                    Column('analysisType', String(50), nullable=False),
                    Column('createdAt', DateTime, default=datetime.utcnow),
                    Column('updatedAt', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
                    Column('deepAnalysis', JSON, nullable=True),
                    Column('gscAnalysis', JSON, nullable=True),
                    Column('status', String(50), default='pending')
                )
                
                engine = self.db_session.get_bind()
                metadata.create_all(engine)
                logger.info(f"Tabla {table_name} creada exitosamente")
                return True
            except SQLAlchemyError as e:
                logger.error(f"Error al crear la tabla {table_name}: {str(e)}")
                return False
    
    def get_client_analyses(self, client_name, conversation_id=None, batch_run_id=None, analysis_type=None):
        """
        Obtiene los análisis para un cliente específico.
        
        Args:
            client_name: Nombre del cliente
            conversation_id: ID de la conversación (opcional)
            batch_run_id: ID del lote de ejecución (opcional)
            analysis_type: Tipo de análisis (opcional)
            
        Returns:
            list: Lista de análisis que coinciden con los criterios
            None: Si ocurre un error
        """
        try:
            # Verificar si el cliente existe
            client_result = self.db_session.execute(
                text("SELECT clientId FROM smartvoc_clients WHERE clientName = :name"),
                {"name": client_name}
            ).fetchone()
            
            if not client_result:
                logger.warning(f"Cliente {client_name} no encontrado")
                return []
                
            table_name = self._get_analysis_table_name(client_name)
            
            try:
                # Construir la consulta base
                query = f"SELECT * FROM {table_name}"
                params = {}
                conditions = []
                
                # Agregar filtros si se proporcionan
                if conversation_id:
                    conditions.append("conversationId = :conversation_id")
                    params["conversation_id"] = conversation_id
                
                if batch_run_id:
                    conditions.append("batchRunId = :batch_run_id")
                    params["batch_run_id"] = batch_run_id
                
                if analysis_type:
                    conditions.append("analysisType = :analysis_type")
                    params["analysis_type"] = analysis_type
                
                # Agregar condiciones a la consulta
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # Ejecutar la consulta
                result = self.db_session.execute(text(query), params).fetchall()
                
                # Convertir los resultados a diccionarios y manejar campos JSON
                analyses = []
                for row in result:
                    analysis = dict(row._mapping)
                    
                    # Convertir campos JSON si no son None
                    if analysis.get('deepAnalysis'):
                        analysis['deepAnalysis'] = json.loads(analysis['deepAnalysis']) \
                            if isinstance(analysis['deepAnalysis'], str) else analysis['deepAnalysis']
                    
                    if analysis.get('gscAnalysis'):
                        analysis['gscAnalysis'] = json.loads(analysis['gscAnalysis']) \
                            if isinstance(analysis['gscAnalysis'], str) else analysis['gscAnalysis']
                    
                    # Convertir fechas a formato ISO
                    if analysis.get('createdAt'):
                        analysis['createdAt'] = analysis['createdAt'].isoformat()
                    
                    if analysis.get('updatedAt'):
                        analysis['updatedAt'] = analysis['updatedAt'].isoformat()
                    
                    analyses.append(analysis)
                
                return analyses
            
            except NoSuchTableError:
                logger.info(f"Tabla {table_name} no existe para el cliente {client_name}")
                return []
                
        except SQLAlchemyError as e:
            logger.error(f"Error al recuperar análisis para {client_name}: {str(e)}")
            return None
    
    def create_analysis(self, client_name, conversation_id, analysis_data, batch_run_id=None, analysis_type="standard"):
        """
        Crea un nuevo análisis para una conversación.
        
        Args:
            client_name: Nombre del cliente
            conversation_id: ID de la conversación
            analysis_data: Datos del análisis
            batch_run_id: ID del lote de ejecución (opcional)
            analysis_type: Tipo de análisis (por defecto "standard")
            
        Returns:
            dict: Análisis creado
            None: Si ocurre un error
        """
        try:
            # Verificar si el cliente existe
            client_result = self.db_session.execute(
                text("SELECT clientId FROM smartvoc_clients WHERE clientName = :name"),
                {"name": client_name}
            ).fetchone()
            
            if not client_result:
                logger.warning(f"Cliente {client_name} no encontrado")
                return None
            
            # Asegurar que la tabla existe
            if not self._ensure_analysis_table_exists(client_name):
                return None
            
            table_name = self._get_analysis_table_name(client_name)
            
            # Preparar datos de análisis
            deep_analysis = analysis_data.get('deepAnalysis')
            gsc_analysis = analysis_data.get('gscAnalysis')
            
            # Convertir a JSON si son diccionarios
            if isinstance(deep_analysis, dict):
                deep_analysis = json.dumps(deep_analysis)
            
            if isinstance(gsc_analysis, dict):
                gsc_analysis = json.dumps(gsc_analysis)
            
            # Verificar si ya existe un análisis para esta conversación
            existing = self.db_session.execute(
                text(f"SELECT id FROM {table_name} WHERE conversationId = :conversation_id"),
                {"conversation_id": conversation_id}
            ).fetchone()
            
            if existing:
                logger.warning(f"Ya existe un análisis para la conversación {conversation_id}, use update_analysis")
                return None
            
            # Crear el análisis
            now = datetime.utcnow()
            query = text(f"""
                INSERT INTO {table_name} 
                (conversationId, batchRunId, analysisType, createdAt, updatedAt, deepAnalysis, gscAnalysis, status)
                VALUES 
                (:conversation_id, :batch_run_id, :analysis_type, :created_at, :updated_at, :deep_analysis, :gsc_analysis, :status)
            """)
            
            self.db_session.execute(query, {
                "conversation_id": conversation_id,
                "batch_run_id": batch_run_id,
                "analysis_type": analysis_type,
                "created_at": now,
                "updated_at": now,
                "deep_analysis": deep_analysis,
                "gsc_analysis": gsc_analysis,
                "status": "completed"
            })
            
            self.db_session.commit()
            
            # Obtener el análisis creado
            analysis = self.get_client_analyses(client_name, conversation_id=conversation_id)
            return analysis[0] if analysis else None
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error al crear análisis para {conversation_id}: {str(e)}")
            return None
    
    def update_analysis(self, client_name, conversation_id, analysis_data):
        """
        Actualiza un análisis existente.
        
        Args:
            client_name: Nombre del cliente
            conversation_id: ID de la conversación
            analysis_data: Datos actualizados del análisis
            
        Returns:
            dict: Análisis actualizado
            None: Si ocurre un error
        """
        try:
            # Verificar si el cliente existe
            client_result = self.db_session.execute(
                text("SELECT clientId FROM smartvoc_clients WHERE clientName = :name"),
                {"name": client_name}
            ).fetchone()
            
            if not client_result:
                logger.warning(f"Cliente {client_name} no encontrado")
                return None
            
            table_name = self._get_analysis_table_name(client_name)
            
            # Verificar si existe la tabla
            try:
                # Verificar si existe el análisis
                existing = self.db_session.execute(
                    text(f"SELECT id FROM {table_name} WHERE conversationId = :conversation_id"),
                    {"conversation_id": conversation_id}
                ).fetchone()
                
                if not existing:
                    logger.warning(f"No existe un análisis para la conversación {conversation_id}")
                    return None
                
                # Preparar conjuntos de actualizaciones
                updates = []
                params = {"conversation_id": conversation_id, "updated_at": datetime.utcnow()}
                
                # Actualizar sólo los campos proporcionados
                if 'deepAnalysis' in analysis_data:
                    deep_analysis = analysis_data['deepAnalysis']
                    if isinstance(deep_analysis, dict):
                        deep_analysis = json.dumps(deep_analysis)
                    updates.append("deepAnalysis = :deep_analysis")
                    params["deep_analysis"] = deep_analysis
                
                if 'gscAnalysis' in analysis_data:
                    gsc_analysis = analysis_data['gscAnalysis']
                    if isinstance(gsc_analysis, dict):
                        gsc_analysis = json.dumps(gsc_analysis)
                    updates.append("gscAnalysis = :gsc_analysis")
                    params["gsc_analysis"] = gsc_analysis
                
                if 'status' in analysis_data:
                    updates.append("status = :status")
                    params["status"] = analysis_data['status']
                
                if 'analysisType' in analysis_data:
                    updates.append("analysisType = :analysis_type")
                    params["analysis_type"] = analysis_data['analysisType']
                
                if 'batchRunId' in analysis_data:
                    updates.append("batchRunId = :batch_run_id")
                    params["batch_run_id"] = analysis_data['batchRunId']
                
                # Siempre actualizar updatedAt
                updates.append("updatedAt = :updated_at")
                
                # Ejecutar la actualización si hay campos para actualizar
                if updates:
                    update_query = f"UPDATE {table_name} SET {', '.join(updates)} WHERE conversationId = :conversation_id"
                    self.db_session.execute(text(update_query), params)
                    self.db_session.commit()
                
                # Obtener el análisis actualizado
                analysis = self.get_client_analyses(client_name, conversation_id=conversation_id)
                return analysis[0] if analysis else None
                
            except NoSuchTableError:
                logger.warning(f"Tabla {table_name} no existe para el cliente {client_name}")
                return None
                
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error al actualizar análisis para {conversation_id}: {str(e)}")
            return None
    
    def delete_analysis(self, client_name, conversation_id):
        """
        Elimina un análisis existente.
        
        Args:
            client_name: Nombre del cliente
            conversation_id: ID de la conversación
            
        Returns:
            bool: True si se eliminó exitosamente, False en caso contrario
        """
        try:
            # Verificar si el cliente existe
            client_result = self.db_session.execute(
                text("SELECT clientId FROM smartvoc_clients WHERE clientName = :name"),
                {"name": client_name}
            ).fetchone()
            
            if not client_result:
                logger.warning(f"Cliente {client_name} no encontrado")
                return False
            
            table_name = self._get_analysis_table_name(client_name)
            
            # Verificar si existe la tabla
            try:
                # Verificar si existe el análisis
                existing = self.db_session.execute(
                    text(f"SELECT id FROM {table_name} WHERE conversationId = :conversation_id"),
                    {"conversation_id": conversation_id}
                ).fetchone()
                
                if not existing:
                    logger.warning(f"No existe un análisis para la conversación {conversation_id}")
                    return False
                
                # Eliminar el análisis
                delete_query = f"DELETE FROM {table_name} WHERE conversationId = :conversation_id"
                self.db_session.execute(text(delete_query), {"conversation_id": conversation_id})
                self.db_session.commit()
                return True
                
            except NoSuchTableError:
                logger.warning(f"Tabla {table_name} no existe para el cliente {client_name}")
                return False
                
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error al eliminar análisis para {conversation_id}: {str(e)}")
            return False 