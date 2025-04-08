from flask_restx import Resource, fields
from flask import current_app, request
from app import db
from models import SmartVOCClient, SmartVOCConversation, ClientDetails, FieldGroup, GenerativeAnalysis
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import time
import json
import uuid
from datetime import datetime

# Variables globales para modelos y namespace
smartvoc_ns = None
client_model = None
client_details_model = None
client_input_model = None
field_group_model = None
generative_analysis_model = None
conversation_model = None
error_model = None
success_model = None
info_model = None
operation_model = None

def init_smartvoc_models(api):
    """Inicializa los modelos y namespaces de SmartVOC"""
    global smartvoc_ns, client_model, client_details_model, client_input_model
    global field_group_model, generative_analysis_model, conversation_model
    global error_model, success_model, info_model, operation_model
    
    # Crear namespace
    smartvoc_ns = api.namespace('smartvoc', description='Operaciones relacionadas con SmartVOC')
    
    # Definir modelos
    client_model = api.model('SmartVOCClient', {
        'clientId': fields.Integer(required=True, description='ID del cliente'),
        'clientName': fields.String(required=True, description='Nombre del cliente'),
        'clientSlug': fields.String(required=True, description='Slug del cliente'),
        'createdAt': fields.String(required=False, description='Fecha de creación')
    })
    
    client_details_model = api.model('ClientDetails', {
        'clientId': fields.Integer(required=True, description='ID del cliente'),
        'clientName': fields.String(required=True, description='Nombre del cliente'),
        'clientWebsite': fields.String(description='Sitio web del cliente'),
        'clientDescription': fields.String(description='Descripción del cliente'),
        'clientLanguageDialect': fields.String(description='Dialecto de idioma del cliente'),
        'clientKeywords': fields.String(description='Palabras clave del cliente'),
        'clientSlug': fields.String(description='Slug del cliente'),
        'copilotTableName': fields.String(description='Nombre de la tabla de copiloto'),
        'autoFieldGroup': fields.String(description='Grupo de campos automático'),
        'autoCategoryGroup': fields.String(description='Grupo de categorías automático'),
        'autoAgentName': fields.String(description='Nombre del agente automático')
    })
    
    client_input_model = api.model('CreateSmartVOCClient', {
        'clientName': fields.String(required=True, description='Nombre del cliente'),
    })
    
    field_group_model = api.model('FieldGroup', {
        'fieldGroupId': fields.Integer(required=True, description='ID del grupo de campos'),
        'clientName': fields.String(required=True, description='Nombre del cliente'),
        'fieldAndCategories': fields.Raw(description='Campos y categorías'),
        'clientId': fields.Integer(required=True, description='ID del cliente'),
        'fieldName': fields.String(required=True, description='Nombre del campo'),
        'generatedFieldsAndCategories': fields.Raw(description='Campos y categorías generados')
    })
    
    generative_analysis_model = api.model('GenerativeAnalysis', {
        'conversationId': fields.String(required=True, description='ID de la conversación'),
        'batchRunId': fields.String(description='ID de la ejecución del lote'),
        'deepAnalysis': fields.Raw(description='Análisis profundo'),
        'gscAnalysis': fields.Raw(description='Análisis GSC'),
        'createdAt': fields.String(description='Fecha de creación'),
        'status': fields.String(description='Estado del análisis'),
        'analysisType': fields.String(description='Tipo de análisis')
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
                                    'smartvoc-conversations', 'client-details', 'field-groups',
                                    'generative-analysis']),
        'parameters': fields.Raw(required=False, description='Parámetros adicionales para la operación')
    })

class SmartVOCResource(Resource):
    def post(self):
        """Maneja las operaciones POST para SmartVOC."""
        parameters = request.get_json()
        operation = parameters.get("operation", "").lower()
        
        if operation == "client-details":
            return self.create_client_details(parameters)
        elif operation == "field-groups":
            return self.create_field_group(parameters)
        elif operation == "generative-analysis":
            return self.create_generative_analysis(parameters)
        else:
            return {"error": f"Operación no soportada: {operation}"}, 400
    
    def put(self):
        """Maneja las operaciones PUT para SmartVOC."""
        parameters = request.get_json()
        operation = parameters.get("operation", "").lower()
        
        if operation == "client-details":
            return self.update_client_details(parameters)
        elif operation == "field-groups":
            return self.update_field_group(parameters)
        elif operation == "generative-analysis":
            return self.update_generative_analysis(parameters)
        else:
            return {"error": f"Operación no soportada: {operation}"}, 400
    
    def get(self):
        """Maneja las operaciones GET para SmartVOC."""
        parameters = request.args.to_dict()
        operation = parameters.get("operation", "").lower()
        
        if operation == "client-details":
            return self.get_client_details(parameters)
        elif operation == "field-groups":
            return self.get_field_groups(parameters)
        elif operation == "generative-analysis":
            return self.get_generative_analyses(parameters)
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
                            try:
                                if hasattr(conv_dict['createdAt'], 'isoformat'):
                                    conv_dict['createdAt'] = conv_dict['createdAt'].isoformat()
                            except:
                                # Si ocurre algún error, dejamos la fecha como está
                                pass
                            
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
    
    def get_client_details(self, parameters):
        """Obtiene los detalles de un cliente específico."""
        client_name = parameters.get("clientName", "")
        
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
                table_name = f"ClientDetails__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {
                        "message": f"La tabla {table_name} no existe. No hay detalles para este cliente.",
                        "details": {}
                    }, 200
                
                # Obtener detalles del cliente
                query = text(f"SELECT * FROM {table_name} WHERE clientName = :clientName")
                result = db.session.execute(query, {"clientName": client_name})
                details = result.fetchone()
                
                if not details:
                    return {
                        "message": f"No se encontraron detalles para el cliente '{client_name}'",
                        "details": {}
                    }, 200
                
                # Convertir a diccionario
                details_dict = dict(details)
                return details_dict, 200
                
            except SQLAlchemyError as e:
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al obtener detalles del cliente: {str(e)}"}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudieron obtener los detalles del cliente después de múltiples intentos"}, 500
    
    def create_client_details(self, parameters):
        """Crea detalles para un cliente específico."""
        client_name = parameters.get("clientName", "")
        client_id = parameters.get("clientId", "")
        client_website = parameters.get("clientWebsite", "")
        client_description = parameters.get("clientDescription", "")
        client_language_dialect = parameters.get("clientLanguageDialect", "")
        client_keywords = parameters.get("clientKeywords", "")
        copilot_table_name = parameters.get("copilotTableName", "")
        auto_field_group = parameters.get("autoFieldGroup", "")
        auto_category_group = parameters.get("autoCategoryGroup", "")
        auto_agent_name = parameters.get("autoAgentName", "")
        
        if not client_name or not client_id:
            return {"error": "Los parámetros clientName y clientId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = f"ClientDetails__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    # Crear la tabla si no existe
                    db.session.execute(text(f"""
                        CREATE TABLE {table_name} (
                            clientId INT NOT NULL,
                            clientName NVARCHAR(100) NOT NULL,
                            clientWebsite NVARCHAR(255),
                            clientDescription NVARCHAR(500),
                            clientLanguageDialect NVARCHAR(50),
                            clientKeywords NVARCHAR(255),
                            clientSlug NVARCHAR(255),
                            copilotTableName NVARCHAR(255),
                            autoFieldGroup NVARCHAR(255) NULL,
                            autoCategoryGroup NVARCHAR(255) NULL,
                            autoAgentName NVARCHAR(255) NULL
                        )
                    """))
                    db.session.commit()
                
                # Insertar detalles del cliente
                query = text(f"""
                    INSERT INTO {table_name} (
                        clientId, clientName, clientWebsite, clientDescription,
                        clientLanguageDialect, clientKeywords, clientSlug,
                        copilotTableName, autoFieldGroup, autoCategoryGroup, autoAgentName
                    ) VALUES (
                        :clientId, :clientName, :clientWebsite, :clientDescription,
                        :clientLanguageDialect, :clientKeywords, :clientSlug,
                        :copilotTableName, :autoFieldGroup, :autoCategoryGroup, :autoAgentName
                    )
                """)
                
                db.session.execute(query, {
                    "clientId": client_id,
                    "clientName": client_name,
                    "clientWebsite": client_website,
                    "clientDescription": client_description,
                    "clientLanguageDialect": client_language_dialect,
                    "clientKeywords": client_keywords,
                    "clientSlug": client.clientSlug,
                    "copilotTableName": copilot_table_name,
                    "autoFieldGroup": auto_field_group,
                    "autoCategoryGroup": auto_category_group,
                    "autoAgentName": auto_agent_name
                })
                
                db.session.commit()
                return {"message": "Detalles del cliente creados exitosamente"}, 201
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al crear detalles del cliente: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudieron crear los detalles del cliente después de múltiples intentos"}, 500
    
    def update_client_details(self, parameters):
        """Actualiza los detalles de un cliente específico."""
        client_name = parameters.get("clientName", "")
        client_id = parameters.get("clientId", "")
        client_website = parameters.get("clientWebsite")
        client_description = parameters.get("clientDescription")
        client_language_dialect = parameters.get("clientLanguageDialect")
        client_keywords = parameters.get("clientKeywords")
        copilot_table_name = parameters.get("copilotTableName")
        auto_field_group = parameters.get("autoFieldGroup")
        auto_category_group = parameters.get("autoCategoryGroup")
        auto_agent_name = parameters.get("autoAgentName")
        
        if not client_name or not client_id:
            return {"error": "Los parámetros clientName y clientId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = f"ClientDetails__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe."}, 404
                
                # Construir la consulta de actualización dinámicamente
                update_parts = []
                params = {"clientId": client_id, "clientName": client_name}
                
                if client_website is not None:
                    update_parts.append("clientWebsite = :clientWebsite")
                    params["clientWebsite"] = client_website
                
                if client_description is not None:
                    update_parts.append("clientDescription = :clientDescription")
                    params["clientDescription"] = client_description
                
                if client_language_dialect is not None:
                    update_parts.append("clientLanguageDialect = :clientLanguageDialect")
                    params["clientLanguageDialect"] = client_language_dialect
                
                if client_keywords is not None:
                    update_parts.append("clientKeywords = :clientKeywords")
                    params["clientKeywords"] = client_keywords
                
                if copilot_table_name is not None:
                    update_parts.append("copilotTableName = :copilotTableName")
                    params["copilotTableName"] = copilot_table_name
                
                if auto_field_group is not None:
                    update_parts.append("autoFieldGroup = :autoFieldGroup")
                    params["autoFieldGroup"] = auto_field_group
                
                if auto_category_group is not None:
                    update_parts.append("autoCategoryGroup = :autoCategoryGroup")
                    params["autoCategoryGroup"] = auto_category_group
                
                if auto_agent_name is not None:
                    update_parts.append("autoAgentName = :autoAgentName")
                    params["autoAgentName"] = auto_agent_name
                
                if not update_parts:
                    return {"error": "No se proporcionaron campos para actualizar"}, 400
                
                # Ejecutar la actualización
                query = text(f"""
                    UPDATE {table_name}
                    SET {', '.join(update_parts)}
                    WHERE clientId = :clientId AND clientName = :clientName
                """)
                
                result = db.session.execute(query, params)
                db.session.commit()
                
                if result.rowcount == 0:
                    return {"error": "No se encontraron detalles para actualizar"}, 404
                
                return {"message": "Detalles del cliente actualizados exitosamente"}, 200
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al actualizar detalles del cliente: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudieron actualizar los detalles del cliente después de múltiples intentos"}, 500
    
    def get_field_groups(self, parameters):
        """Obtiene los grupos de campos para un cliente específico."""
        client_name = parameters.get("clientName", "")
        client_id = parameters.get("clientId", "")
        
        if not client_name or not client_id:
            return {"error": "Los parámetros clientName y clientId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = f"Fields__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {
                        "message": f"La tabla {table_name} no existe. No hay grupos de campos para este cliente.",
                        "fields": []
                    }, 200
                
                # Obtener grupos de campos
                query = text(f"SELECT * FROM {table_name} WHERE clientId = :clientId")
                result = db.session.execute(query, {"clientId": client_id})
                fields = []
                
                for row in result:
                    field = dict(row)
                    # Convertir campos JSON
                    if field.get('fieldAndCategories'):
                        try:
                            field['fieldAndCategories'] = json.loads(field['fieldAndCategories'])
                        except (TypeError, json.JSONDecodeError):
                            field['fieldAndCategories'] = []
                    
                    if field.get('generatedFieldsAndCategories'):
                        try:
                            field['generatedFieldsAndCategories'] = json.loads(field['generatedFieldsAndCategories'])
                        except (TypeError, json.JSONDecodeError):
                            field['generatedFieldsAndCategories'] = []
                    
                    fields.append(field)
                
                return {"fields": fields}, 200
                
            except SQLAlchemyError as e:
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al obtener grupos de campos: {str(e)}"}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudieron obtener los grupos de campos después de múltiples intentos"}, 500
    
    def create_field_group(self, parameters):
        """Crea un nuevo grupo de campos para un cliente específico."""
        client_name = parameters.get("clientName", "")
        client_id = parameters.get("clientId", "")
        field_name = parameters.get("fieldName", "")
        field_and_categories = parameters.get("fieldAndCategories", "[]")
        
        if not client_name or not client_id or not field_name:
            return {"error": "Los parámetros clientName, clientId y fieldName son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = f"Fields__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    # Crear la tabla si no existe
                    db.session.execute(text(f"""
                        CREATE TABLE {table_name} (
                            fieldGroupId INT NOT NULL,
                            fieldAndCategories NVARCHAR(MAX),
                            clientId INT,
                            fieldName NVARCHAR(100) NOT NULL,
                            clientName NVARCHAR(100) NOT NULL,
                            generatedFieldsAndCategories NVARCHAR(MAX)
                        )
                    """))
                    db.session.commit()
                
                # Obtener el siguiente fieldGroupId
                result = db.session.execute(text(f"SELECT MAX(fieldGroupId) FROM {table_name}"))
                max_id = result.scalar() or 0
                new_field_group_id = max_id + 1
                
                # Insertar grupo de campos
                query = text(f"""
                    INSERT INTO {table_name} (
                        fieldGroupId, fieldAndCategories, clientId, fieldName, clientName
                    ) VALUES (
                        :fieldGroupId, :fieldAndCategories, :clientId, :fieldName, :clientName
                    )
                """)
                
                db.session.execute(query, {
                    "fieldGroupId": new_field_group_id,
                    "fieldAndCategories": field_and_categories,
                    "clientId": client_id,
                    "fieldName": field_name,
                    "clientName": client_name
                })
                
                db.session.commit()
                return {"message": "Grupo de campos creado exitosamente", "fieldGroupId": new_field_group_id}, 201
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al crear grupo de campos: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo crear el grupo de campos después de múltiples intentos"}, 500
    
    def update_field_group(self, parameters):
        """Actualiza un grupo de campos existente."""
        client_name = parameters.get("clientName", "")
        field_group_id = parameters.get("fieldGroupId", "")
        field_name = parameters.get("fieldName")
        field_and_categories = parameters.get("fieldAndCategories")
        generated_fields_and_categories = parameters.get("generatedFieldsAndCategories")
        
        if not client_name or not field_group_id:
            return {"error": "Los parámetros clientName y fieldGroupId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = f"Fields__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe."}, 404
                
                # Construir la consulta de actualización dinámicamente
                update_parts = []
                params = {"fieldGroupId": field_group_id}
                
                if field_name is not None:
                    update_parts.append("fieldName = :fieldName")
                    params["fieldName"] = field_name
                
                if field_and_categories is not None:
                    update_parts.append("fieldAndCategories = :fieldAndCategories")
                    params["fieldAndCategories"] = field_and_categories
                
                if generated_fields_and_categories is not None:
                    update_parts.append("generatedFieldsAndCategories = :generatedFieldsAndCategories")
                    params["generatedFieldsAndCategories"] = generated_fields_and_categories
                
                if not update_parts:
                    return {"error": "No se proporcionaron campos para actualizar"}, 400
                
                # Ejecutar la actualización
                query = text(f"""
                    UPDATE {table_name}
                    SET {', '.join(update_parts)}
                    WHERE fieldGroupId = :fieldGroupId
                """)
                
                result = db.session.execute(query, params)
                db.session.commit()
                
                if result.rowcount == 0:
                    return {"error": "No se encontró el grupo de campos para actualizar"}, 404
                
                return {"message": "Grupo de campos actualizado exitosamente"}, 200
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al actualizar grupo de campos: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo actualizar el grupo de campos después de múltiples intentos"}, 500
    
    def delete_field_group(self, parameters):
        """Elimina un grupo de campos existente."""
        client_name = parameters.get("clientName", "")
        field_group_id = parameters.get("fieldGroupId", "")
        
        if not client_name or not field_group_id:
            return {"error": "Los parámetros clientName y fieldGroupId son obligatorios"}, 400
        
        max_retries = 3
        retry_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Obtener cliente para validar que existe y obtener el clientSlug
                client = SmartVOCClient.query.filter_by(clientName=client_name).first()
                if not client:
                    return {"error": f"No se encontró el cliente '{client_name}'"}, 404
                
                # Verificar si la tabla existe
                table_name = f"Fields__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe."}, 404
                
                # Eliminar grupo de campos
                query = text(f"DELETE FROM {table_name} WHERE fieldGroupId = :fieldGroupId")
                result = db.session.execute(query, {"fieldGroupId": field_group_id})
                db.session.commit()
                
                if result.rowcount == 0:
                    return {"error": "No se encontró el grupo de campos para eliminar"}, 404
                
                return {"message": "Grupo de campos eliminado exitosamente"}, 200
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al eliminar grupo de campos: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo eliminar el grupo de campos después de múltiples intentos"}, 500
    
    def get_generative_analyses(self, parameters):
        """Obtiene análisis generativos según los parámetros proporcionados."""
        client_name = parameters.get("clientName", "")
        conversation_id = parameters.get("conversationId", "")
        batch_run_id = parameters.get("batchRunId", "")
        analysis_type = parameters.get("analysisType", "")
        
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
                table_name = f"GenerativeAnalyses__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {
                        "message": f"La tabla {table_name} no existe. No hay análisis para este cliente.",
                        "analyses": []
                    }, 200
                
                # Construir la consulta según los parámetros
                query_parts = [f"SELECT * FROM {table_name}"]
                params = {}
                
                if conversation_id:
                    query_parts.append("WHERE conversationId = :conversationId")
                    params["conversationId"] = conversation_id
                
                if batch_run_id:
                    if conversation_id:
                        query_parts.append("AND batchRunId = :batchRunId")
                    else:
                        query_parts.append("WHERE batchRunId = :batchRunId")
                    params["batchRunId"] = batch_run_id
                
                if analysis_type:
                    if conversation_id or batch_run_id:
                        query_parts.append("AND type = :analysisType")
                    else:
                        query_parts.append("WHERE type = :analysisType")
                    params["analysisType"] = analysis_type
                
                # Ejecutar la consulta
                query = text(" ".join(query_parts))
                result = db.session.execute(query, params)
                analyses = []
                
                for row in result:
                    analysis = dict(row)
                    # Convertir campos JSON
                    if analysis.get('deepAnalysis'):
                        try:
                            analysis['deepAnalysis'] = json.loads(analysis['deepAnalysis'])
                        except (TypeError, json.JSONDecodeError):
                            analysis['deepAnalysis'] = {}
                    
                    if analysis.get('gscAnalysis'):
                        try:
                            analysis['gscAnalysis'] = json.loads(analysis['gscAnalysis'])
                        except (TypeError, json.JSONDecodeError):
                            analysis['gscAnalysis'] = {}
                    
                    analyses.append(analysis)
                
                return {"analyses": analyses}, 200
                
            except SQLAlchemyError as e:
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al obtener análisis generativos: {str(e)}"}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudieron obtener los análisis generativos después de múltiples intentos"}, 500
    
    def create_generative_analysis(self, parameters):
        """Crea un nuevo análisis generativo."""
        client_name = parameters.get("clientName", "")
        conversation_id = parameters.get("conversationId", "")
        batch_run_id = parameters.get("batchRunId", "")
        deep_analysis = parameters.get("deepAnalysis", "{}")
        gsc_analysis = parameters.get("gscAnalysis", "{}")
        analysis_type = parameters.get("analysisType", "DeepAnalysis")
        
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
                table_name = f"GenerativeAnalyses__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    # Crear la tabla si no existe
                    db.session.execute(text(f"""
                        CREATE TABLE {table_name} (
                            conversationId NVARCHAR(255) NOT NULL,
                            batchRunId NVARCHAR(MAX),
                            deepAnalysis NVARCHAR(MAX),
                            gscAnalysis NVARCHAR(MAX),
                            createdAt DATETIME,
                            status NVARCHAR(50) DEFAULT 'PROCESSING',
                            type NVARCHAR(50)
                        )
                    """))
                    db.session.commit()
                
                # Insertar análisis generativo
                query = text(f"""
                    INSERT INTO {table_name} (
                        conversationId, batchRunId, deepAnalysis, gscAnalysis, createdAt, status, type
                    ) VALUES (
                        :conversationId, :batchRunId, :deepAnalysis, :gscAnalysis, GETDATE(), 'PROCESSING', :analysisType
                    )
                """)
                
                db.session.execute(query, {
                    "conversationId": conversation_id,
                    "batchRunId": batch_run_id,
                    "deepAnalysis": deep_analysis,
                    "gscAnalysis": gsc_analysis,
                    "analysisType": analysis_type
                })
                
                db.session.commit()
                return {"message": "Análisis generativo creado exitosamente"}, 201
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al crear análisis generativo: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo crear el análisis generativo después de múltiples intentos"}, 500
    
    def update_generative_analysis(self, parameters):
        """Actualiza un análisis generativo existente."""
        client_name = parameters.get("clientName", "")
        conversation_id = parameters.get("conversationId", "")
        batch_run_id = parameters.get("batchRunId")
        deep_analysis = parameters.get("deepAnalysis")
        gsc_analysis = parameters.get("gscAnalysis")
        status = parameters.get("status")
        analysis_type = parameters.get("analysisType")
        
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
                table_name = f"GenerativeAnalyses__{client.clientSlug}"
                inspector = inspect(db.engine)
                if not inspector.has_table(table_name):
                    return {"error": f"La tabla {table_name} no existe."}, 404
                
                # Construir la consulta de actualización dinámicamente
                update_parts = []
                params = {"conversationId": conversation_id}
                
                if batch_run_id is not None:
                    update_parts.append("batchRunId = :batchRunId")
                    params["batchRunId"] = batch_run_id
                
                if deep_analysis is not None:
                    update_parts.append("deepAnalysis = :deepAnalysis")
                    params["deepAnalysis"] = deep_analysis
                
                if gsc_analysis is not None:
                    update_parts.append("gscAnalysis = :gscAnalysis")
                    params["gscAnalysis"] = gsc_analysis
                
                if status is not None:
                    update_parts.append("status = :status")
                    params["status"] = status
                
                if analysis_type is not None:
                    update_parts.append("type = :analysisType")
                    params["analysisType"] = analysis_type
                
                if not update_parts:
                    return {"error": "No se proporcionaron campos para actualizar"}, 400
                
                # Ejecutar la actualización
                query = text(f"""
                    UPDATE {table_name}
                    SET {', '.join(update_parts)}
                    WHERE conversationId = :conversationId
                """)
                
                result = db.session.execute(query, params)
                db.session.commit()
                
                if result.rowcount == 0:
                    return {"error": "No se encontró el análisis generativo para actualizar"}, 404
                
                return {"message": "Análisis generativo actualizado exitosamente"}, 200
                
            except SQLAlchemyError as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    current_app.logger.error(f"Error de SQL: {str(e)}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Número máximo de intentos alcanzado. Error: {str(e)}")
                    return {"error": f"Error al actualizar análisis generativo: {str(e)}"}, 500
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error inesperado: {str(e)}")
                return {"error": str(e)}, 500
                
        return {"error": "No se pudo actualizar el análisis generativo después de múltiples intentos"}, 500 