from flask_restx import Resource, fields
from flask import current_app, request
from api import api
from app import db
from models import SmartVOCClient, SmartVOCConversation
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import time
import json
import uuid
from datetime import datetime

# Crear un namespace para los recursos de SmartVOC
smartvoc_ns = api.namespace('smartvoc', description='Operaciones relacionadas con SmartVOC')

# Definir modelos de respuesta
client_model = api.model('SmartVOCClient', {
    'clientId': fields.Integer(required=True, description='ID del cliente'),
    'clientName': fields.String(required=True, description='Nombre del cliente'),
    'clientSlug': fields.String(required=True, description='Slug del cliente'),
    'createdAt': fields.String(required=False, description='Fecha de creación')
})

client_input_model = api.model('CreateSmartVOCClient', {
    'clientName': fields.String(required=True, description='Nombre del cliente'),
})

conversation_model = api.model('SmartVOCConversation', {
    'conversationId': fields.String(required=True, description='ID de la conversación'),
    'clientId': fields.Integer(required=True, description='ID del cliente'),
    'conversation': fields.Raw(description='Contenido de la conversación (array de mensajes)'),
    'metadata': fields.Raw(description='Metadatos de la conversación'),
    'deepAnalysisStage': fields.String(description='Etapa del análisis profundo'),
    'gscAnalysisStage': fields.String(description='Etapa del análisis GSC'),
    'batchCustomName': fields.String(description='Nombre personalizado del lote'),
    'createdAt': fields.String(description='Fecha de creación'),
    'deepAnalysisBatchId': fields.String(description='ID del lote de análisis profundo'),
    'gscAnalysisBatchId': fields.String(description='ID del lote de análisis GSC'),
    'analysis': fields.Raw(description='Análisis de la conversación'),
    'autoProcessingStatus': fields.String(description='Estado del procesamiento automático')
})

error_model = api.model('Error', {
    'error': fields.String(required=True, description='Mensaje de error')
})

success_model = api.model('Success', {
    'message': fields.String(required=True, description='Mensaje de éxito')
})

info_model = api.model('Info', {
    'message': fields.String(required=True, description='Mensaje informativo'),
    'clients': fields.List(fields.Raw, description='Lista de clientes (vacía si no hay ninguno)')
})

operation_model = api.model('Operation', {
    'operation': fields.String(required=True, description='Operación a realizar', 
                              enum=['get-all-smartvoc-clients', 'create-smartvoc-client', 
                                   'smartvoc-conversations']),
    'parameters': fields.Raw(required=False, description='Parámetros adicionales para la operación')
})

@smartvoc_ns.route('')
class SmartVOCResource(Resource):
    @smartvoc_ns.doc('smartvoc_operations')
    @smartvoc_ns.expect(operation_model)
    @smartvoc_ns.response(200, 'Éxito - Clientes', [client_model])
    @smartvoc_ns.response(200, 'Sin clientes', info_model)
    @smartvoc_ns.response(201, 'Cliente creado', success_model)
    @smartvoc_ns.response(400, 'Solicitud incorrecta', error_model)
    @smartvoc_ns.response(500, 'Error de servidor', error_model)
    def post(self):
        """Realiza operaciones relacionadas con SmartVOC según el parámetro 'operation'."""
        data = request.json
        operation = data.get('operation')
        
        if not operation:
            return {"error": "Se requiere especificar una operación"}, 400
            
        # Manejar diferentes operaciones
        if operation == 'get-all-smartvoc-clients':
            return self.get_all_smartvoc_clients()
        elif operation == 'create-smartvoc-client':
            return self.create_smartvoc_client(data.get('parameters', {}))
        elif operation == 'smartvoc-conversations':
            # Las operaciones CRUD de conversaciones se manejan mediante el método específico
            method = data.get('method', '').upper()
            if method == 'GET':
                return self.get_smartvoc_conversations(data.get('parameters', {}))
            elif method == 'POST':
                return self.create_smartvoc_conversation(data.get('parameters', {}))
            elif method == 'PUT':
                return self.update_smartvoc_conversation(data.get('parameters', {}))
            elif method == 'DELETE':
                return self.delete_smartvoc_conversation(data.get('parameters', {}))
            else:
                return {"error": f"Método '{method}' no soportado para operación 'smartvoc-conversations'"}, 400
        else:
            return {"error": f"Operación no soportada: {operation}"}, 400
    
    def get_all_smartvoc_clients(self):
        """Lista todos los clientes de SmartVOC registrados en la base de datos."""
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Verificar si la tabla existe
                inspector = inspect(db.engine)
                if not inspector.has_table('SmartVOCClients'):
                    return {
                        "message": "La tabla SmartVOCClients no existe. No hay clientes registrados.",
                        "clients": []
                    }, 200
                
                # Consultar los clientes usando el ORM
                clients = SmartVOCClient.query.all()
                
                if not clients:
                    return {
                        "message": "No hay clientes registrados en la base de datos.",
                        "clients": []
                    }, 200
                
                # Convertir los objetos a diccionarios
                clients_dict = [client.to_dict() for client in clients]
                return clients_dict, 200
                    
            except OperationalError as e:
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de conexión a la base de datos. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": "Error de conexión a la base de datos después de múltiples intentos"}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500

        return {"error": "No se pudieron recuperar los clientes después de múltiples intentos"}, 500
    
    def create_smartvoc_client(self, parameters):
        """Crea un nuevo cliente de SmartVOC con sus tablas relacionadas."""
        # Extraer el nombre del cliente de los parámetros
        client_name = parameters.get("clientName", "")
        
        if not client_name:
            return {"error": "El parámetro clientName es obligatorio"}, 400
        
        # Generar clientSlug en formato CamelCase
        client_slug = ''.join(word.capitalize() for word in client_name.split())
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Verificar si ya existe un cliente con ese nombre
                existing_client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if existing_client:
                    return {"error": f"Ya existe un cliente con el nombre '{client_name}'"}, 400
                
                # Crear la tabla principal si no existe
                inspector = inspect(db.engine)
                if not inspector.has_table('SmartVOCClients'):
                    create_tables_sql = """
                    CREATE TABLE SmartVOCClients (
                        clientId INTEGER PRIMARY KEY AUTOINCREMENT,
                        clientName VARCHAR(100) NOT NULL UNIQUE,
                        clientSlug VARCHAR(100) NOT NULL,
                        createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                    db.session.execute(text(create_tables_sql))
                    db.session.commit()
                
                # Crear el nuevo cliente
                new_client = SmartVOCClient(
                    clientName=client_name,
                    clientSlug=client_slug
                )
                db.session.add(new_client)
                db.session.flush()  # Para obtener el ID generado
                
                client_id = new_client.clientId
                
                # Crear tablas específicas del cliente
                # Tabla de detalles del cliente
                db.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS ClientDetails__{client_slug} (
                    clientId INTEGER NOT NULL,
                    clientName VARCHAR(100) NOT NULL,
                    clientWebsite VARCHAR(255),
                    clientDescription VARCHAR(500),
                    clientLanguageDialect VARCHAR(50),
                    clientKeywords VARCHAR(255),
                    clientSlug VARCHAR(255),
                    copilotTableName VARCHAR(255),
                    autoFieldGroup VARCHAR(255),
                    autoCategoryGroup VARCHAR(255),
                    autoAgentName VARCHAR(255)
                );
                """))
                
                # Insertar datos básicos en la tabla de detalles
                db.session.execute(text(f"""
                INSERT INTO ClientDetails__{client_slug} 
                (clientId, clientName, clientSlug) 
                VALUES (:clientId, :clientName, :clientSlug)
                """), {
                    "clientId": client_id,
                    "clientName": client_name,
                    "clientSlug": client_slug
                })
                
                # Tabla de conversaciones
                db.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS Conversations__{client_slug} (
                    conversationId VARCHAR(255) NOT NULL,
                    conversation TEXT,
                    metadata TEXT,
                    deepAnalysisStage VARCHAR(50),
                    gscAnalysisStage VARCHAR(50),
                    batchCustomName VARCHAR(255),
                    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    clientId INTEGER,
                    deepAnalysisBatchId VARCHAR(255),
                    gscAnalysisBatchId VARCHAR(255),
                    analysis TEXT,
                    autoProcessingStatus VARCHAR(255)
                );
                """))
                
                # Tabla de campos
                db.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS Fields__{client_slug} (
                    fieldGroupId INTEGER NOT NULL,
                    fieldAndCategories TEXT,
                    clientId INTEGER,
                    fieldName VARCHAR(100) NOT NULL,
                    clientName VARCHAR(100) NOT NULL,
                    generatedFieldsAndCategories TEXT
                );
                """))
                
                # Tabla de análisis generativos
                db.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS GenerativeAnalyses__{client_slug} (
                    conversationId VARCHAR(255) NOT NULL,
                    batchRunId TEXT,
                    deepAnalysis TEXT,
                    gscAnalysis TEXT,
                    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'PROCESSING',
                    type VARCHAR(50)
                );
                """))
                
                # Tabla de citas de campo/categoría para copilot
                db.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS CopilotFieldCategoryQuote__{client_slug} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversationId VARCHAR(255) NOT NULL,
                    conversationGroupId VARCHAR(255) NOT NULL,
                    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    field TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quote TEXT
                );
                """))
                
                # Confirmar todos los cambios
                db.session.commit()
                
                return {"message": f"Cliente {client_name} creado exitosamente"}, 201
                
            except SQLAlchemyError as e:
                # Revertir en caso de error
                db.session.rollback()
                current_app.logger.error(f"Error de SQL: {str(e)}")
                return {"error": f"Error al crear el cliente: {str(e)}"}, 500
            
            except OperationalError as e:
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de conexión a la base de datos. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": "Error de conexión a la base de datos después de múltiples intentos"}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": f"Error inesperado: {str(e)}"}, 500
        
        return {"error": "No se pudo crear el cliente después de múltiples intentos"}, 500
    
    def get_smartvoc_conversations(self, parameters):
        """Obtiene conversaciones según los parámetros proporcionados."""
        client_name = parameters.get("clientName", "")
        client_id = parameters.get("clientId", "")
        conversation_id = parameters.get("conversationId", "")
        batch_custom_name = parameters.get("batchCustomName", "")
        
        if not client_name:
            return {"error": "El parámetro clientName es obligatorio"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = SmartVOCConversation.get_table_name(client.clientSlug)
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {
                        "message": f"La tabla {table_name} no existe. No hay conversaciones para este cliente.",
                        "conversations": []
                    }, 200
                
                # Construir la consulta según los parámetros
                if conversation_id:
                    # Si se solicita una conversación específica, obtener todos los detalles
                    query = text(f"SELECT * FROM {table_name} WHERE conversationId = :conversationId")
                    result = db.session.execute(query, {"conversationId": conversation_id})
                    conversation = result.fetchone()
                    
                    if not conversation:
                        return {"error": "Conversación no encontrada"}, 404
                    
                    # Convertir a diccionario y procesar campos JSON
                    conversation_dict = SmartVOCConversation.to_dict(conversation)
                    return conversation_dict, 200
                    
                elif client_id:
                    # Listar conversaciones para un cliente
                    if batch_custom_name:
                        query = text(f"""
                            SELECT 
                                conversationId,
                                conversation,
                                deepAnalysisStage,
                                gscAnalysisStage,
                                batchCustomName,
                                createdAt,
                                deepAnalysisBatchId,
                                gscAnalysisBatchId,
                                autoProcessingStatus
                            FROM {table_name} 
                            WHERE clientId = :clientId 
                            AND batchCustomName = :batchCustomName
                        """)
                        result = db.session.execute(query, {
                            "clientId": client_id, 
                            "batchCustomName": batch_custom_name
                        })
                    else:
                        query = text(f"""
                            SELECT 
                                conversationId,
                                deepAnalysisStage,
                                gscAnalysisStage,
                                batchCustomName,
                                createdAt,
                                deepAnalysisBatchId,
                                gscAnalysisBatchId,
                                autoProcessingStatus
                            FROM {table_name} 
                            WHERE clientId = :clientId
                        """)
                        result = db.session.execute(query, {"clientId": client_id})
                    
                    # Procesar resultados
                    conversations = []
                    for row in result:
                        # Convertir a diccionario y procesar campos JSON si es necesario
                        conv_dict = dict(row)
                        if 'conversation' in conv_dict and conv_dict['conversation']:
                            try:
                                conv_dict["conversation"] = json.loads(conv_dict["conversation"])
                            except (json.JSONDecodeError, TypeError):
                                conv_dict["conversation"] = []
                        
                        # Formatear fechas
                        if 'createdAt' in conv_dict and conv_dict['createdAt']:
                            conv_dict['createdAt'] = conv_dict['createdAt'].isoformat()
                            
                        conversations.append(conv_dict)
                    
                    return conversations, 200
                else:
                    return {"error": "Se requiere especificar clientId o conversationId"}, 400
                
            except OperationalError as e:
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de conexión a la base de datos. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": "Error de conexión a la base de datos después de múltiples intentos"}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudieron recuperar las conversaciones después de múltiples intentos"}, 500
    
    def create_smartvoc_conversation(self, parameters):
        """Crea una nueva conversación para un cliente específico."""
        client_name = parameters.get("clientName", "")
        client_id = parameters.get("clientId", "")
        conversations = parameters.get("conversations") or parameters.get("conversation") or []
        metadata = parameters.get("metadata", {})
        deep_analysis_stage = parameters.get("deepAnalysisStage")
        gsc_analysis_stage = parameters.get("gscAnalysisStage")
        batch_custom_name = parameters.get("batchCustomName", "")
        created_at = parameters.get("createdAt")
        
        if not client_name or not client_id or not batch_custom_name:
            return {"error": "Los parámetros clientName, clientId y batchCustomName son obligatorios"}, 400
        
        # Generar un ID único para la conversación
        conversation_id = str(uuid.uuid4())
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = SmartVOCConversation.get_table_name(client.clientSlug)
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe. Primero debe crear el cliente correctamente"}, 400
                
                # Establecer la fecha de creación si no se proporciona
                if not created_at:
                    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                # Si cada elemento de 'conversations' no tiene 'conversationId', agregarlo
                if isinstance(conversations, list):
                    for conv in conversations:
                        if isinstance(conv, dict):
                            if "conversation_id" in conv:
                                conv["conversationId"] = conv["conversation_id"]
                            elif "conversationId" not in conv:
                                conv["conversationId"] = str(uuid.uuid4())
                
                # Insertar la conversación
                query = text(f"""
                    INSERT INTO {table_name} (
                        conversationId, 
                        clientId, 
                        conversation, 
                        metadata, 
                        deepAnalysisStage, 
                        gscAnalysisStage, 
                        batchCustomName, 
                        createdAt
                    )
                    VALUES (
                        :conversationId, 
                        :clientId, 
                        :conversation, 
                        :metadata, 
                        :deepAnalysisStage, 
                        :gscAnalysisStage, 
                        :batchCustomName, 
                        :createdAt
                    )
                """)
                
                db.session.execute(query, {
                    "conversationId": conversation_id,
                    "clientId": client_id,
                    "conversation": json.dumps(conversations),
                    "metadata": json.dumps(metadata),
                    "deepAnalysisStage": deep_analysis_stage,
                    "gscAnalysisStage": gsc_analysis_stage,
                    "batchCustomName": batch_custom_name,
                    "createdAt": created_at
                })
                
                db.session.commit()
                
                return {
                    "message": "Grupo de conversaciones subido exitosamente", 
                    "conversationId": conversation_id
                }, 201
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al crear la conversación: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo crear la conversación después de múltiples intentos"}, 500
    
    def update_smartvoc_conversation(self, parameters):
        """Actualiza una conversación existente."""
        client_name = parameters.get("clientName", "")
        conversation_id = parameters.get("conversationId", "")
        conversation_data = parameters.get("conversation")
        metadata = parameters.get("metadata")
        deep_analysis_stage = parameters.get("deepAnalysisStage")
        gsc_analysis_stage = parameters.get("gscAnalysisStage")
        batch_custom_name = parameters.get("batchCustomName")
        analysis = parameters.get("analysis")
        auto_processing_status = parameters.get("autoProcessingStatus")
        
        if not client_name or not conversation_id:
            return {"error": "Los parámetros clientName y conversationId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = SmartVOCConversation.get_table_name(client.clientSlug)
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe."}, 404
                
                # Verificar si la conversación existe
                check_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE conversationId = :conversationId")
                result = db.session.execute(check_query, {"conversationId": conversation_id}).scalar()
                
                if result == 0:
                    return {"error": "Conversación no encontrada"}, 404
                
                # Construir la consulta de actualización dinámicamente
                update_parts = []
                params = {"conversationId": conversation_id}
                
                if conversation_data is not None:
                    update_parts.append("conversation = :conversation")
                    params["conversation"] = json.dumps(conversation_data)
                
                if metadata is not None:
                    update_parts.append("metadata = :metadata")
                    params["metadata"] = json.dumps(metadata)
                
                if deep_analysis_stage is not None:
                    update_parts.append("deepAnalysisStage = :deepAnalysisStage")
                    params["deepAnalysisStage"] = deep_analysis_stage
                
                if gsc_analysis_stage is not None:
                    update_parts.append("gscAnalysisStage = :gscAnalysisStage")
                    params["gscAnalysisStage"] = gsc_analysis_stage
                
                if batch_custom_name is not None:
                    update_parts.append("batchCustomName = :batchCustomName")
                    params["batchCustomName"] = batch_custom_name
                
                if analysis is not None:
                    update_parts.append("analysis = :analysis")
                    params["analysis"] = json.dumps(analysis)
                
                if auto_processing_status is not None:
                    update_parts.append("autoProcessingStatus = :autoProcessingStatus")
                    params["autoProcessingStatus"] = auto_processing_status
                
                if not update_parts:
                    return {"error": "No se especificaron campos para actualizar"}, 400
                
                # Ejecutar la consulta de actualización
                update_query = text(f"""
                    UPDATE {table_name}
                    SET {', '.join(update_parts)}
                    WHERE conversationId = :conversationId
                """)
                
                db.session.execute(update_query, params)
                db.session.commit()
                
                return {"message": "Conversación actualizada exitosamente"}, 200
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al actualizar la conversación: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo actualizar la conversación después de múltiples intentos"}, 500
    
    def delete_smartvoc_conversation(self, parameters):
        """Elimina una conversación existente."""
        client_name = parameters.get("clientName", "")
        conversation_id = parameters.get("conversationId", "")
        
        if not client_name or not conversation_id:
            return {"error": "Los parámetros clientName y conversationId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = SmartVOCConversation.get_table_name(client.clientSlug)
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe."}, 404
                
                # Verificar si la conversación existe
                check_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE conversationId = :conversationId")
                result = db.session.execute(check_query, {"conversationId": conversation_id}).scalar()
                
                if result == 0:
                    return {"error": "Conversación no encontrada"}, 404
                
                # Ejecutar la eliminación
                delete_query = text(f"DELETE FROM {table_name} WHERE conversationId = :conversationId")
                db.session.execute(delete_query, {"conversationId": conversation_id})
                db.session.commit()
                
                return {"message": "Conversación eliminada exitosamente"}, 200
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al eliminar la conversación: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo eliminar la conversación después de múltiples intentos"}, 500 