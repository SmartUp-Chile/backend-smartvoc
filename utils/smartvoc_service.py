from flask import current_app
from app import db
from models import SmartVOCClient, ClientDetails, FieldGroup, GenerativeAnalysis, Analysis, DynamicTableManager
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import json
import uuid
from datetime import datetime

class SmartVOCService:
    """Servicio para manejar operaciones de SmartVOC."""
    
    @staticmethod
    def create_client(client_name):
        """Crea un nuevo cliente de SmartVOC con sus tablas relacionadas."""
        # Generar client_slug en formato CamelCase
        client_slug = ''.join(word.capitalize() for word in client_name.split())
        # Generar client_id único
        client_id = str(uuid.uuid4())
        # Generar API key
        api_key = str(uuid.uuid4())
        
        try:
            # Verificar si ya existe un cliente con ese nombre
            existing_client = SmartVOCClient.query.filter_by(client_name=client_name).first()
            if existing_client:
                return {
                    "success": False,
                    "error": f"Ya existe un cliente con el nombre '{client_name}'"
                }
            
            # Crear el nuevo cliente
            new_client = SmartVOCClient(
                client_id=client_id,
                client_name=client_name,
                client_slug=client_slug,
                api_key=api_key
            )
            
            db.session.add(new_client)
            db.session.commit()
            
            # Crear tablas específicas del cliente
            DynamicTableManager.create_conversation_table(client_slug)
            DynamicTableManager.create_quote_table(client_slug)
            
            return {
                "success": True,
                "message": f"Cliente '{client_name}' creado con éxito",
                "client": new_client.to_dict()
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos al crear cliente: {str(e)}")
            return {
                "success": False,
                "error": f"Error de base de datos: {str(e)}"
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al crear cliente: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_client(client_id=None, client_name=None):
        """Obtiene los detalles de un cliente específico."""
        try:
            client = None
            if client_id:
                client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            elif client_name:
                client = SmartVOCClient.query.filter_by(client_name=client_name).first()
            
            if not client:
                return {
                    "success": False,
                    "error": "Cliente no encontrado"
                }
            
            # Obtener detalles adicionales si existen
            details = ClientDetails.query.filter_by(client_id=client.client_id).first()
            
            result = client.to_dict()
            if details:
                result.update(details.to_dict())
            
            return {
                "success": True,
                "client": result
            }
        except Exception as e:
            current_app.logger.error(f"Error al obtener cliente: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def update_client(client_id, data):
        """Actualiza los datos de un cliente existente."""
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": f"No se encontró un cliente con el ID '{client_id}'"
                }
            
            # Actualizar campos del cliente
            if 'clientName' in data:
                client.client_name = data['clientName']
            
            # Actualizar detalles del cliente si existen
            details = ClientDetails.query.filter_by(client_id=client_id).first()
            
            if details:
                # Actualizar campos de detalles
                for key, value in data.items():
                    if hasattr(details, key.lower()):
                        setattr(details, key.lower(), value)
            else:
                # Crear detalles si no existen
                details = ClientDetails(
                    client_id=client_id,
                    client_name=client.client_name,
                    client_slug=client.client_slug
                )
                
                # Establecer campos de detalles
                for key, value in data.items():
                    if hasattr(details, key.lower()):
                        setattr(details, key.lower(), value)
                
                db.session.add(details)
            
            client.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Cliente '{client.client_name}' actualizado con éxito",
                "client": client.to_dict()
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos al actualizar cliente: {str(e)}")
            return {
                "success": False,
                "error": f"Error de base de datos: {str(e)}"
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al actualizar cliente: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def delete_client(client_id):
        """Elimina un cliente y todas sus tablas asociadas."""
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": f"No se encontró un cliente con el ID '{client_id}'"
                }
            
            client_name = client.client_name
            client_slug = client.client_slug
            
            # Eliminar datos relacionados
            ClientDetails.query.filter_by(client_id=client_id).delete()
            FieldGroup.query.filter_by(client_id=client_id).delete()
            GenerativeAnalysis.query.filter_by(client_id=client_id).delete()
            Analysis.query.filter_by(client_id=client_id).delete()
            
            # Eliminar tablas dinámicas si existen
            if DynamicTableManager.table_exists(f"Conversations__{client_slug}"):
                db.session.execute(text(f"DROP TABLE IF EXISTS Conversations__{client_slug}"))
            
            if DynamicTableManager.table_exists(f"CopilotFieldCategoryQuote__{client_slug}"):
                db.session.execute(text(f"DROP TABLE IF EXISTS CopilotFieldCategoryQuote__{client_slug}"))
            
            # Eliminar el cliente
            db.session.delete(client)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Cliente '{client_name}' eliminado con éxito"
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos al eliminar cliente: {str(e)}")
            return {
                "success": False,
                "error": f"Error de base de datos: {str(e)}"
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al eliminar cliente: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def create_conversation(client_id, conversation_data):
        """Crea una nueva conversación para un cliente específico."""
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": f"No se encontró un cliente con el ID '{client_id}'"
                }
            
            client_slug = client.client_slug
            table_name = f"Conversations__{client_slug}"
            
            # Verificar si existe la tabla de conversaciones
            if not DynamicTableManager.table_exists(table_name):
                # Crear la tabla si no existe
                if not DynamicTableManager.create_conversation_table(client_slug):
                    return {
                        "success": False,
                        "error": f"Error al crear la tabla de conversaciones para el cliente '{client.client_name}'"
                    }
            
            # Generar ID de conversación si no se proporciona
            conversation_id = conversation_data.get('conversationId', str(uuid.uuid4()))
            
            # Preparar datos de la conversación
            conversation = conversation_data.get('conversation', {})
            metadata = conversation_data.get('metadata', {})
            
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
                "success": True,
                "message": f"Conversación creada con éxito para el cliente '{client.client_name}'",
                "conversationId": conversation_id
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear conversación: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_conversation(client_id, conversation_id):
        """Obtiene una conversación específica para un cliente."""
        try:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": f"No se encontró un cliente con el ID '{client_id}'"
                }
            
            client_slug = client.client_slug
            table_name = f"Conversations__{client_slug}"
            
            # Verificar si existe la tabla de conversaciones
            if not DynamicTableManager.table_exists(table_name):
                return {
                    "success": False,
                    "error": f"No hay tabla de conversaciones para el cliente '{client.client_name}'"
                }
            
            # Consultar la conversación
            query = f"SELECT * FROM {table_name} WHERE conversation_id = :conversation_id"
            result = DynamicTableManager.execute_query(query, {'conversation_id': conversation_id})
            
            rows = result.fetchall()
            if not rows:
                return {
                    "success": False,
                    "error": f"No se encontró la conversación con ID '{conversation_id}'"
                }
            
            # Convertir a diccionario
            from models import SmartVOCConversation
            conversation = SmartVOCConversation.to_dict(rows[0])
            
            return {
                "success": True,
                "conversation": conversation
            }
        except Exception as e:
            current_app.logger.error(f"Error al obtener conversación: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 