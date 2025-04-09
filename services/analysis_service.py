"""
Servicios para la gestión de análisis de conversaciones
"""
import logging
from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, inspect
from flask import current_app
from jsonschema import validate, ValidationError

from db import db_session, engine
from models import RequestLog
from schemas.analysis_schema import analysis_schema, analysis_update_schema
from exceptions.custom_exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self):
        self.table_name = 'conversation_analyses'
    
    def _ensure_table_exists(self, client_name):
        """Asegura que la tabla de análisis para un cliente existe en la base de datos"""
        try:
            # Primero comprobamos si existe la tabla para este cliente
            table_name = f"{client_name.lower().replace(' ', '_')}_{self.table_name}"
            
            inspector = inspect(engine)
            if not inspector.has_table(table_name):
                logger.info(f"Creando tabla {table_name}...")
                query = text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(100) NOT NULL,
                    analysis_type VARCHAR(50) NOT NULL,
                    result JSONB NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(conversation_id, analysis_type)
                )
                """)
                db_session.execute(query)
                db_session.commit()
                logger.info(f"Tabla {table_name} creada correctamente")
            return table_name
        except SQLAlchemyError as e:
            logger.error(f"Error al verificar/crear tabla para cliente {client_name}: {str(e)}")
            db_session.rollback()
            raise
    
    def get_client_analyses(self, client_name, conversation_id=None, analysis_type=None):
        """Obtiene los análisis para un cliente específico, opcionalmente filtrado por conversación y tipo"""
        try:
            table_name = self._ensure_table_exists(client_name)
            
            params = {}
            query_str = f"SELECT * FROM {table_name}"
            
            # Aplicar filtros si se proporcionan
            conditions = []
            if conversation_id:
                conditions.append("conversation_id = :conversation_id")
                params['conversation_id'] = conversation_id
                
            if analysis_type:
                conditions.append("analysis_type = :analysis_type")
                params['analysis_type'] = analysis_type
                
            if conditions:
                query_str += " WHERE " + " AND ".join(conditions)
                
            query_str += " ORDER BY created_at DESC"
            
            query = text(query_str)
            result = db_session.execute(query, params)
            
            analyses = []
            for row in result:
                analysis = {
                    'id': row.id,
                    'conversation_id': row.conversation_id,
                    'analysis_type': row.analysis_type,
                    'result': row.result,
                    'metadata': row.metadata,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at
                }
                analyses.append(analysis)
                
            # Registrar solicitud
            self._log_request("get_client_analyses", {
                "client_name": client_name,
                "conversation_id": conversation_id,
                "analysis_type": analysis_type,
                "result_count": len(analyses)
            })
            
            return {
                "success": True,
                "analyses": analyses
            }
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener análisis para cliente {client_name}: {str(e)}")
            raise ResourceNotFoundError(f"Error al obtener análisis: {str(e)}")
    
    def create_analysis(self, client_name, analysis_data):
        """Crea un nuevo análisis para un cliente"""
        try:
            # Validar datos requeridos
            if not analysis_data.get('conversation_id'):
                raise ValidationError("El ID de conversación es obligatorio")
            if not analysis_data.get('analysis_type'):
                raise ValidationError("El tipo de análisis es obligatorio")
            if not analysis_data.get('result'):
                raise ValidationError("El resultado del análisis es obligatorio")
                
            table_name = self._ensure_table_exists(client_name)
            
            # Verificar si ya existe un análisis para esta conversación y tipo
            exists_query = text(f"""
            SELECT COUNT(*) as count FROM {table_name} 
            WHERE conversation_id = :conversation_id AND analysis_type = :analysis_type
            """)
            exists_result = db_session.execute(exists_query, {
                'conversation_id': analysis_data.get('conversation_id'),
                'analysis_type': analysis_data.get('analysis_type')
            })
            
            count = exists_result.scalar()
            if count and count > 0:
                # Realizar actualización en su lugar
                return self.update_analysis(
                    client_name, 
                    analysis_data.get('conversation_id'),
                    analysis_data.get('analysis_type'),
                    analysis_data
                )
            
            # Convertir objetos a JSON string si es necesario
            result_data = analysis_data.get('result')
            if isinstance(result_data, dict):
                result_data = json.dumps(result_data)
                
            metadata = analysis_data.get('metadata', {})
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
            
            # Insertar nuevo análisis
            insert_query = text(f"""
            INSERT INTO {table_name} (conversation_id, analysis_type, result, metadata)
            VALUES (:conversation_id, :analysis_type, :result, :metadata)
            RETURNING *
            """)
            
            params = {
                'conversation_id': analysis_data.get('conversation_id'),
                'analysis_type': analysis_data.get('analysis_type'),
                'result': result_data,
                'metadata': metadata
            }
            
            insert_result = db_session.execute(insert_query, params)
            row = insert_result.fetchone()
            db_session.commit()
            
            new_analysis = {
                'id': row.id,
                'conversation_id': row.conversation_id,
                'analysis_type': row.analysis_type,
                'result': row.result,
                'metadata': row.metadata,
                'created_at': row.created_at,
                'updated_at': row.updated_at
            }
            
            logger.info(f"Análisis creado con éxito para conversación: {new_analysis['conversation_id']}")
            return new_analysis
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Error al crear análisis: {str(e)}")
            raise ValidationError(f"Error al crear análisis: {str(e)}")
    
    def update_analysis(self, client_name, conversation_id, analysis_type, analysis_data):
        """Actualiza un análisis existente para un cliente"""
        try:
            table_name = self._ensure_table_exists(client_name)
            
            # Verificar que el análisis exista
            check_query = text(f"""
            SELECT * FROM {table_name} 
            WHERE conversation_id = :conversation_id AND analysis_type = :analysis_type
            """)
            check_result = db_session.execute(check_query, {
                'conversation_id': conversation_id,
                'analysis_type': analysis_type
            })
            
            existing_analysis = check_result.fetchone()
            if not existing_analysis:
                raise ResourceNotFoundError(f"Análisis no encontrado para conversación {conversation_id} y tipo {analysis_type}")
            
            # Preparar campos a actualizar
            update_fields = []
            params = {
                'conversation_id': conversation_id,
                'analysis_type': analysis_type
            }
            
            if 'result' in analysis_data:
                update_fields.append("result = :result")
                result_data = analysis_data['result']
                if isinstance(result_data, dict):
                    result_data = json.dumps(result_data)
                params['result'] = result_data
            
            if 'metadata' in analysis_data:
                update_fields.append("metadata = :metadata")
                metadata = analysis_data['metadata']
                if isinstance(metadata, dict):
                    metadata = json.dumps(metadata)
                params['metadata'] = metadata
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            if not update_fields:
                # No hay cambios, devolver el análisis existente
                return {
                    'id': existing_analysis.id,
                    'conversation_id': existing_analysis.conversation_id,
                    'analysis_type': existing_analysis.analysis_type,
                    'result': existing_analysis.result,
                    'metadata': existing_analysis.metadata,
                    'created_at': existing_analysis.created_at,
                    'updated_at': existing_analysis.updated_at
                }
            
            # Actualizar análisis
            update_query = text(f"""
            UPDATE {table_name}
            SET {', '.join(update_fields)}
            WHERE conversation_id = :conversation_id AND analysis_type = :analysis_type
            RETURNING *
            """)
            update_result = db_session.execute(update_query, params)
            row = update_result.fetchone()
            db_session.commit()
            
            updated_analysis = {
                'id': row.id,
                'conversation_id': row.conversation_id,
                'analysis_type': row.analysis_type,
                'result': row.result,
                'metadata': row.metadata,
                'created_at': row.created_at,
                'updated_at': row.updated_at
            }
            
            logger.info(f"Análisis actualizado con éxito para conversación: {updated_analysis['conversation_id']}")
            return updated_analysis
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Error al actualizar análisis: {str(e)}")
            raise ValidationError(f"Error al actualizar análisis: {str(e)}")
    
    def delete_analysis(self, client_name, conversation_id, analysis_type=None):
        """Elimina un análisis existente para un cliente"""
        try:
            table_name = self._ensure_table_exists(client_name)
            
            params = {
                'conversation_id': conversation_id
            }
            
            # Construir la consulta dependiendo de si se proporciona el tipo de análisis
            if analysis_type:
                query_str = f"""
                DELETE FROM {table_name}
                WHERE conversation_id = :conversation_id AND analysis_type = :analysis_type
                """
                params['analysis_type'] = analysis_type
            else:
                query_str = f"""
                DELETE FROM {table_name}
                WHERE conversation_id = :conversation_id
                """
            
            # Ejecutar la consulta
            delete_query = text(query_str)
            delete_result = db_session.execute(delete_query, params)
            db_session.commit()
            
            # Verificar si se ha eliminado algo
            if delete_result.rowcount == 0:
                raise ResourceNotFoundError(f"No se encontró análisis para la conversación {conversation_id}")
            
            # Registrar la operación
            self._log_request("delete_analysis", {
                "client_name": client_name,
                "conversation_id": conversation_id,
                "analysis_type": analysis_type,
                "deleted_count": delete_result.rowcount
            })
            
            return True
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Error al eliminar análisis: {str(e)}")
            raise ValidationError(f"Error al eliminar análisis: {str(e)}")

    def get_analyses_list(self, params):
        """
        Obtiene una lista paginada de análisis según criterios de filtrado
        
        Args:
            params (dict): Parámetros de filtrado y paginación
                - client_name (str): Nombre del cliente
                - start_date (str): Fecha de inicio (YYYY-MM-DD)
                - end_date (str): Fecha de fin (YYYY-MM-DD)
                - page (int): Número de página
                - page_size (int): Tamaño de página
                - status (str): Estado del análisis (complete, pending, error)
                
        Returns:
            dict: Resultado con la lista paginada de análisis
        """
        try:
            client_name = params.get('client_name')
            if not client_name:
                return {
                    "success": False,
                    "error": "Se requiere el parámetro client_name"
                }
                
            # Convertir parámetros
            page = int(params.get('page', 1))
            page_size = int(params.get('page_size', 10))
            status = params.get('status')
            
            # Fechas
            start_date = params.get('start_date')
            end_date = params.get('end_date')
            
            # Obtener análisis con filtros aplicados
            result = self.get_client_analyses(client_name)
            if not result.get('success'):
                return result
                
            analyses = result.get('analyses', [])
            
            # Aplicar filtro de fechas si se proporciona
            if start_date or end_date:
                filtered_analyses = []
                
                for analysis in analyses:
                    created_at = analysis.get('createdAt')
                    if not created_at:
                        continue
                        
                    # Convertir a objeto datetime si es string
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            continue
                            
                    # Filtrar por fecha de inicio
                    if start_date:
                        try:
                            start_datetime = datetime.fromisoformat(start_date)
                            if created_at < start_datetime:
                                continue
                        except (ValueError, TypeError):
                            pass
                            
                    # Filtrar por fecha de fin
                    if end_date:
                        try:
                            end_datetime = datetime.fromisoformat(end_date)
                            # Ajustar al final del día
                            end_datetime = end_datetime + timedelta(days=1) - timedelta(microseconds=1)
                            if created_at > end_datetime:
                                continue
                        except (ValueError, TypeError):
                            pass
                            
                    filtered_analyses.append(analysis)
                    
                analyses = filtered_analyses
                
            # Aplicar filtro de estado si se proporciona
            if status:
                if status == 'complete':
                    analyses = [a for a in analyses if a.get('isComplete')]
                elif status == 'pending':
                    analyses = [a for a in analyses if a.get('isComplete') is False and a.get('errorMessage') is None]
                elif status == 'error':
                    analyses = [a for a in analyses if a.get('errorMessage') is not None]
            
            # Calcular páginas para la paginación
            total = len(analyses)
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
            
            # Validar página solicitada
            if page < 1:
                page = 1
            elif page > total_pages and total_pages > 0:
                page = total_pages
                
            # Aplicar paginación
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total)
            
            page_items = analyses[start_idx:end_idx] if 0 <= start_idx < total else []
            
            # Construir enlaces para paginación
            base_url = f"/api/analysis/batch?client_name={client_name}"
            if status:
                base_url += f"&status={status}"
            if start_date:
                base_url += f"&start_date={start_date}"
            if end_date:
                base_url += f"&end_date={end_date}"
                
            links = {
                "self": f"{base_url}&page={page}&page_size={page_size}"
            }
            
            # Enlace a página anterior
            if page > 1:
                links["prev"] = f"{base_url}&page={page-1}&page_size={page_size}"
            else:
                links["prev"] = None
                
            # Enlace a página siguiente
            if page < total_pages:
                links["next"] = f"{base_url}&page={page+1}&page_size={page_size}"
            else:
                links["next"] = None
            
            return {
                "success": True,
                "items": page_items,
                "total": total,
                "page": page,
                "pageSize": page_size,
                "totalPages": total_pages,
                "links": links
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lista de análisis: {str(e)}")
            return {
                "success": False,
                "error": f"Error al procesar la solicitud: {str(e)}"
            }

    def start_batch_processing(self, client_name, conversation_ids, options=None):
        """
        Inicia el procesamiento de un lote de análisis para múltiples conversaciones
        
        Args:
            client_name (str): Nombre del cliente
            conversation_ids (list): Lista de IDs de conversaciones
            options (dict, opcional): Opciones de procesamiento
                - priority (int): Prioridad del lote (1-5)
                - notifyOnComplete (bool): Notificar al completar
                - analysisType (str): Tipo de análisis a realizar
                
        Returns:
            str: ID del trabajo de procesamiento por lotes
        """
        try:
            # Validar parámetros
            if not client_name:
                raise ValidationError("Se requiere el nombre del cliente")
                
            if not conversation_ids or not isinstance(conversation_ids, list):
                raise ValidationError("Se requiere una lista válida de IDs de conversaciones")
                
            # Generar ID de lote
            batch_id = str(uuid.uuid4())
            
            # Procesar opciones
            options = options or {}
            priority = options.get('priority', 3)
            analysis_type = options.get('analysisType', 'basic')
            
            # Crear análisis pendientes para cada conversación
            for conversation_id in conversation_ids:
                # Datos del análisis
                analysis_data = {
                    "clientName": client_name,
                    "conversationId": conversation_id,
                    "batchRunId": batch_id,
                    "analysisType": analysis_type,
                    "isComplete": False,
                    "metadata": {
                        "priority": priority,
                        "queuedAt": datetime.now().isoformat(),
                        "totalInBatch": len(conversation_ids),
                        "notifyOnComplete": options.get('notifyOnComplete', False)
                    }
                }
                
                # Crear análisis
                self.create_analysis(client_name, analysis_data)
            
            # Registrar inicio del procesamiento por lotes
            self._log_request("start_batch_processing", {
                "client_name": client_name,
                "batch_id": batch_id,
                "conversation_count": len(conversation_ids),
                "priority": priority,
                "analysis_type": analysis_type
            })
            
            # En una implementación real, aquí se iniciaría un procesamiento asíncrono
            # por ejemplo, mediante un trabajador de Celery o una cola de tareas
            
            return batch_id
            
        except ValidationError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Error al iniciar procesamiento por lotes: {str(e)}")
            raise Exception(f"Error al iniciar procesamiento por lotes: {str(e)}")

    def _log_request(self, operation, details):
        """
        Registra las solicitudes de análisis en la tabla de logs
        
        Args:
            operation (str): Operación realizada
            details (dict): Detalles de la operación
        """
        try:
            request_log = RequestLog(
                operation=operation,
                details=json.dumps(details),
                timestamp=datetime.now()
            )
            db_session.add(request_log)
            db_session.commit()
        except Exception as e:
            logger.error(f"Error al registrar solicitud: {str(e)}")
            db_session.rollback()

# Funciones de compatibilidad con versiones anteriores
def get_client_analyses(client_name, conversation_id=None, analysis_type=None):
    service = AnalysisService()
    return service.get_client_analyses(client_name, conversation_id, analysis_type)

def create_analysis(client_name, analysis_data):
    service = AnalysisService()
    return service.create_analysis(client_name, analysis_data)

def update_analysis(client_name, conversation_id, analysis_type, analysis_data):
    service = AnalysisService()
    return service.update_analysis(client_name, conversation_id, analysis_type, analysis_data)

def delete_analysis(client_name, conversation_id, analysis_type=None):
    service = AnalysisService()
    return service.delete_analysis(client_name, conversation_id, analysis_type)

def log_request(operation, details):
    service = AnalysisService()
    service._log_request(operation, details) 