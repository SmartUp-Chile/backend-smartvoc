from flask import current_app
from db import db_session
from models import SmartVOCClient, ClientDetails, FieldGroup, GenerativeAnalysis, Analysis, DynamicTableManager
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import json
import uuid
from datetime import datetime
from utils.exceptions import (
    APIError,
    ValidationError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    DatabaseError
)
from utils.error_handler import log_exception

class SmartVOCService:
    """Servicio para manejar operaciones de SmartVOC."""
    
    @staticmethod
    def get_clients(params=None):
        """Obtiene todos los clientes de SmartVOC registrados en la base de datos."""
        try:
            query = SmartVOCClient.query
            
            # Aplicar filtros si se proporcionan
            if params:
                if 'clientName' in params:
                    query = query.filter(SmartVOCClient.clientName.like(f"%{params['clientName']}%"))
                    
                # Aplicar paginación
                limit = params.get('limit', 10)
                offset = params.get('offset', 0)
                query = query.limit(limit).offset(offset)
            
            clients = query.all()
            
            if not clients:
                return {
                    "message": "No hay clientes registrados en la base de datos.",
                    "clients": []
                }, 200
            
            clients_dict = [client.to_dict() for client in clients]
            return clients_dict, 200
        except SQLAlchemyError as e:
            log_exception(e)
            raise DatabaseError(
                message="Error al consultar clientes en la base de datos",
                details={"original_error": str(e)}
            )
        except Exception as e:
            log_exception(e)
            raise APIError(
                message="Error al obtener clientes",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def create_client(data):
        """Crea un nuevo cliente de SmartVOC con sus tablas relacionadas."""
        # Validar datos
        if not data or not data.get('clientName'):
            raise ValidationError(
                message="El parámetro clientName es obligatorio",
                details={"missing_fields": ["clientName"]}
            )
            
        client_name = data.get('clientName')
        # Generar client_slug en formato CamelCase
        client_slug = ''.join(word.capitalize() for word in client_name.split())
        
        try:
            # Verificar si ya existe un cliente con ese nombre
            existing_client = SmartVOCClient.query.filter_by(clientName=client_name).first()
            if existing_client:
                raise ResourceAlreadyExistsError(
                    message=f"Ya existe un cliente con el nombre '{client_name}'",
                    details={"client_name": client_name}
                )
            
            # Crear el nuevo cliente
            new_client = SmartVOCClient(
                clientName=client_name,
                clientSlug=client_slug
            )
            
            db_session.add(new_client)
            db_session.commit()
            
            # Crear tablas específicas del cliente
            DynamicTableManager.create_conversation_table(client_slug)
            DynamicTableManager.create_quote_table(client_slug)
            
            return {
                "message": f"Cliente '{client_name}' creado con éxito",
                "client": new_client.to_dict()
            }, 201
        except ResourceAlreadyExistsError:
            db_session.rollback()
            raise
        except SQLAlchemyError as e:
            db_session.rollback()
            log_exception(e)
            raise DatabaseError(
                message="Error de base de datos al crear el cliente",
                details={"original_error": str(e)}
            )
        except Exception as e:
            db_session.rollback()
            log_exception(e)
            raise APIError(
                message="Error inesperado al crear el cliente",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def get_client(client_id=None, client_name=None):
        """Obtiene los detalles de un cliente específico."""
        try:
            client = None
            if client_id:
                client = SmartVOCClient.query.filter_by(clientId=client_id).first()
            elif client_name:
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
            
            if not client:
                raise ResourceNotFoundError(
                    message="Cliente no encontrado",
                    details={
                        "client_id": client_id,
                        "client_name": client_name
                    }
                )
            
            # Obtener detalles adicionales si existen
            details = ClientDetails.query.filter_by(client_id=client.clientId).first()
            
            result = client.to_dict()
            if details:
                result.update(details.to_dict())
            
            return result, 200
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            log_exception(e)
            raise DatabaseError(
                message="Error de base de datos al obtener el cliente",
                details={"original_error": str(e)}
            )
        except Exception as e:
            log_exception(e)
            raise APIError(
                message="Error inesperado al obtener el cliente",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def update_client(client_id, data):
        """Actualiza los datos de un cliente existente."""
        # Validar datos
        if not data:
            raise ValidationError(
                message="No se proporcionaron datos para actualizar",
                details={"missing_fields": ["data"]}
            )
            
        try:
            client = SmartVOCClient.query.filter_by(clientId=client_id).first()
            if not client:
                raise ResourceNotFoundError(
                    message=f"No se encontró un cliente con el ID '{client_id}'",
                    details={"client_id": client_id}
                )
            
            # Actualizar campos del cliente
            if 'clientName' in data:
                client.clientName = data['clientName']
            
            # Actualizar detalles del cliente si existen
            details = ClientDetails.query.filter_by(client_id=client_id).first()
            
            if details:
                # Actualizar campos de detalles
                if 'clientWebsite' in data:
                    details.client_website = data['clientWebsite']
                if 'clientDescription' in data:
                    details.client_description = data['clientDescription']
                if 'clientLanguageDialect' in data:
                    details.client_language_dialect = data['clientLanguageDialect']
                if 'clientKeywords' in data:
                    details.client_keywords = data['clientKeywords']
            else:
                # Crear detalles si no existen
                details = ClientDetails(
                    client_id=client_id,
                    client_name=client.clientName,
                    client_slug=client.clientSlug
                )
                
                # Establecer campos de detalles
                if 'clientWebsite' in data:
                    details.client_website = data['clientWebsite']
                if 'clientDescription' in data:
                    details.client_description = data['clientDescription']
                if 'clientLanguageDialect' in data:
                    details.client_language_dialect = data['clientLanguageDialect']
                if 'clientKeywords' in data:
                    details.client_keywords = data['clientKeywords']
                
                db_session.add(details)
            
            db_session.commit()
            
            return {
                "message": f"Cliente '{client.clientName}' actualizado con éxito",
                "client": client.to_dict()
            }, 200
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            db_session.rollback()
            log_exception(e)
            raise DatabaseError(
                message="Error de base de datos al actualizar el cliente",
                details={"original_error": str(e)}
            )
        except Exception as e:
            db_session.rollback()
            log_exception(e)
            raise APIError(
                message="Error inesperado al actualizar el cliente",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def delete_client(client_id):
        """Elimina un cliente y todas sus tablas asociadas."""
        try:
            client = SmartVOCClient.query.filter_by(clientId=client_id).first()
            if not client:
                raise ResourceNotFoundError(
                    message=f"No se encontró un cliente con el ID '{client_id}'",
                    details={"client_id": client_id}
                )
            
            client_name = client.clientName
            client_slug = client.clientSlug
            
            # Eliminar datos relacionados
            ClientDetails.query.filter_by(client_id=client_id).delete()
            FieldGroup.query.filter_by(client_id=client_id).delete()
            GenerativeAnalysis.query.filter_by(client_id=client_id).delete()
            Analysis.query.filter_by(client_id=client_id).delete()
            
            # Eliminar tablas dinámicas si existen
            if DynamicTableManager.table_exists(f"Conversations__{client_slug}"):
                db_session.execute(text(f"DROP TABLE IF EXISTS Conversations__{client_slug}"))
            
            if DynamicTableManager.table_exists(f"CopilotFieldCategoryQuote__{client_slug}"):
                db_session.execute(text(f"DROP TABLE IF EXISTS CopilotFieldCategoryQuote__{client_slug}"))
            
            # Eliminar el cliente
            db_session.delete(client)
            db_session.commit()
            
            return {"message": f"Cliente '{client_name}' eliminado con éxito"}, 200
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            db_session.rollback()
            log_exception(e)
            raise DatabaseError(
                message="Error de base de datos al eliminar el cliente",
                details={"original_error": str(e)}
            )
        except Exception as e:
            db_session.rollback()
            log_exception(e)
            raise APIError(
                message="Error inesperado al eliminar el cliente",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def get_conversations(params):
        """Obtiene conversaciones para un cliente específico."""
        client_id = params.get('client_id')
        client_name = params.get('client_name')
        conversation_id = params.get('conversation_id')
        limit = int(params.get('limit', 10))
        offset = int(params.get('offset', 0))
        
        if not client_id and not client_name:
            return {"error": "Debe proporcionar clientId o clientName"}, 400
        
        try:
            # Obtener el cliente
            client = None
            if client_id:
                client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            elif client_name:
                client = SmartVOCClient.query.filter_by(client_name=client_name).first()
            
            if not client:
                return {"error": "Cliente no encontrado"}, 404
            
            # Verificar si existe la tabla de conversaciones
            table_name = f"Conversations__{client.client_slug}"
            if not DynamicTableManager.table_exists(table_name):
                return {
                    "message": f"No hay conversaciones para el cliente '{client.client_name}'",
                    "conversations": []
                }, 200
            
            # Construir la consulta
            query = f"SELECT * FROM {table_name}"
            if conversation_id:
                query += f" WHERE conversation_id = '{conversation_id}'"
            query += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
            
            # Ejecutar la consulta
            result = DynamicTableManager.execute_query(query)
            from models import SmartVOCConversation
            conversations = [SmartVOCConversation.to_dict(row) for row in result]
            
            return {
                "conversations": conversations,
                "total": len(conversations),
                "limit": limit,
                "offset": offset
            }, 200
        except Exception as e:
            current_app.logger.error(f"Error al obtener conversaciones: {str(e)}")
            return {"error": str(e)}, 500
    
    @staticmethod
    def create_conversation(data):
        """Crea una nueva conversación para un cliente específico."""
        # Validar datos
        if not data:
            return {"error": "No se proporcionaron datos para la conversación"}, 400
        
        client_id = data.get('clientId')
        if not client_id:
            return {"error": "El parámetro clientId es obligatorio"}, 400
        
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {"error": f"No se encontró un cliente con el ID '{client_id}'"}, 404
            
            client_slug = client.client_slug
            table_name = f"Conversations__{client_slug}"
            
            # Verificar si existe la tabla de conversaciones
            if not DynamicTableManager.table_exists(table_name):
                # Crear la tabla si no existe
                if not DynamicTableManager.create_conversation_table(client_slug):
                    return {"error": f"Error al crear la tabla de conversaciones para el cliente '{client.client_name}'"}, 500
            
            # Generar ID de conversación si no se proporciona
            conversation_id = data.get('conversationId', str(uuid.uuid4()))
            
            # Preparar datos de la conversación
            conversation = data.get('conversation', {})
            metadata = data.get('metadata', {})
            
            # Insertar la conversación
            query = f"""
            INSERT INTO {table_name} (
                conversation_id, client_id, conversation, metadata, 
                created_at, deep_analysis_stage, gsc_analysis_stage
            ) VALUES (
                :conversation_id, :client_id, :conversation, :metadata,
                :created_at, :deep_analysis_stage, :gsc_analysis_stage
            )
            """
            
            params = {
                'conversation_id': conversation_id,
                'client_id': client_id,
                'conversation': json.dumps(conversation),
                'metadata': json.dumps(metadata),
                'created_at': datetime.utcnow(),
                'deep_analysis_stage': 'NONE',
                'gsc_analysis_stage': 'NONE'
            }
            
            DynamicTableManager.execute_query(query, params)
            
            return {
                "message": f"Conversación creada con éxito para el cliente '{client.client_name}'",
                "conversationId": conversation_id
            }, 201
        except Exception as e:
            db_session.rollback()
            current_app.logger.error(f"Error al crear conversación: {str(e)}")
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_conversation(client_id, conversation_id):
        """Obtiene una conversación específica para un cliente."""
        # Validar parámetros
        if not client_id:
            return {"error": "El parámetro clientId es obligatorio"}, 400
            
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {"error": f"No se encontró un cliente con el ID '{client_id}'"}, 404
            
            client_slug = client.client_slug
            table_name = f"Conversations__{client_slug}"
            
            # Verificar si existe la tabla de conversaciones
            if not DynamicTableManager.table_exists(table_name):
                return {"error": f"No hay tabla de conversaciones para el cliente '{client.client_name}'"}, 404
            
            # Consultar la conversación
            query = f"SELECT * FROM {table_name} WHERE conversation_id = :conversation_id"
            result = DynamicTableManager.execute_query(query, {'conversation_id': conversation_id})
            
            rows = result.fetchall()
            if not rows:
                return {"error": f"No se encontró la conversación con ID '{conversation_id}'"}, 404
            
            # Convertir a diccionario
            from models import SmartVOCConversation
            conversation = SmartVOCConversation.to_dict(rows[0])
            
            return conversation, 200
        except Exception as e:
            current_app.logger.error(f"Error al obtener conversación: {str(e)}")
            return {"error": str(e)}, 500
    
    @staticmethod
    def update_conversation(conversation_id, data):
        """Actualiza una conversación existente."""
        # Validar datos
        if not data:
            return {"error": "No se proporcionaron datos para actualizar"}, 400
            
        client_id = data.get('clientId')
        if not client_id:
            return {"error": "El parámetro clientId es obligatorio"}, 400
            
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {"error": f"No se encontró un cliente con el ID '{client_id}'"}, 404
                
            client_slug = client.client_slug
            table_name = f"Conversations__{client_slug}"
            
            # Verificar si existe la tabla
            if not DynamicTableManager.table_exists(table_name):
                return {"error": f"No hay tabla de conversaciones para el cliente '{client.client_name}'"}, 404
                
            # Verificar si la conversación existe
            check_query = f"SELECT conversation_id FROM {table_name} WHERE conversation_id = :conversation_id"
            result = DynamicTableManager.execute_query(check_query, {'conversation_id': conversation_id})
            
            if not result.fetchone():
                return {"error": f"No se encontró la conversación con ID '{conversation_id}'"}, 404
                
            # Preparar datos de actualización
            metadata = data.get('metadata', {})
            metadata_json = json.dumps(metadata)
            
            # Actualizar la conversación
            update_query = f"UPDATE {table_name} SET metadata = :metadata WHERE conversation_id = :conversation_id"
            DynamicTableManager.execute_query(update_query, {
                'metadata': metadata_json,
                'conversation_id': conversation_id
            })
            
            return {
                "message": f"Conversación {conversation_id} actualizada exitosamente",
                "conversationId": conversation_id,
                "clientName": client.client_name
            }, 200
        except Exception as e:
            db_session.rollback()
            current_app.logger.error(f"Error al actualizar conversación: {str(e)}")
            return {"error": str(e)}, 500
    
    @staticmethod
    def delete_conversation(client_id, conversation_id):
        """Elimina una conversación existente."""
        # Validar parámetros
        if not client_id or not conversation_id:
            return {"error": "Los parámetros clientId y conversation_id son obligatorios"}, 400
            
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {"error": f"No se encontró un cliente con el ID '{client_id}'"}, 404
                
            client_slug = client.client_slug
            table_name = f"Conversations__{client_slug}"
            
            # Verificar si existe la tabla
            if not DynamicTableManager.table_exists(table_name):
                return {"error": f"No hay tabla de conversaciones para el cliente '{client.client_name}'"}, 404
                
            # Verificar si la conversación existe
            check_query = f"SELECT conversation_id FROM {table_name} WHERE conversation_id = :conversation_id"
            result = DynamicTableManager.execute_query(check_query, {'conversation_id': conversation_id})
            
            if not result.fetchone():
                return {"error": f"No se encontró la conversación con ID '{conversation_id}'"}, 404
                
            # Eliminar la conversación
            delete_query = f"DELETE FROM {table_name} WHERE conversation_id = :conversation_id"
            DynamicTableManager.execute_query(delete_query, {'conversation_id': conversation_id})
            
            return {
                "message": f"Conversación {conversation_id} eliminada exitosamente",
                "conversationId": conversation_id,
                "clientName": client.client_name
            }, 200
        except Exception as e:
            db_session.rollback()
            current_app.logger.error(f"Error al eliminar conversación: {str(e)}")
            return {"error": str(e)}, 500
    
    @staticmethod
    def health_check():
        """Endpoint para verificar la salud del servicio."""
        return {
            "status": "ok",
            "message": "El servicio SmartVOC está funcionando correctamente"
        }, 200
    
    @staticmethod
    def db_test():
        """Endpoint para probar la conexión a la base de datos."""
        try:
            # Intentar consultar la tabla de clientes
            inspector = inspect(db_session.get_bind())
            if inspector.has_table('smartvoc_clients'):
                return {
                    "status": "ok",
                    "message": "Conexión exitosa a la base de datos"
                }, 200
            else:
                return {
                    "status": "warning",
                    "message": "Conexión exitosa pero la tabla SmartVOCClients no existe"
                }, 200
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error al conectar a la base de datos: {str(e)}"
            }, 500 