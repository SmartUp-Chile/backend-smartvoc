from flask_restx import Resource, fields
from flask import current_app, request
from api import api
from app import db
from models import SmartVOCClient
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import time
import json
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
                              enum=['get-all-smartvoc-clients', 'create-smartvoc-client']),
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