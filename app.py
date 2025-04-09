from flask import Flask, jsonify, request
from sqlalchemy import Column, Integer, String, DateTime, Text
import os
from datetime import datetime
import logging
import json
from utils.analysis_service import AnalysisService
from utils.openai_service import OpenAIService
from utils.conversation_controller import ConversationController
from sqlalchemy import inspect
from db import db_session, Base, init_db, shutdown_session, engine
from routes import blueprints
from models import RequestLog, SmartVOCClient

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicialización de la aplicación
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///smartvoc.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de servicios
analysis_service = AnalysisService(db_session)
conversation_controller = ConversationController(db_session)

# Registrar blueprint después de definir los modelos
for blueprint in blueprints:
    app.register_blueprint(blueprint)

# Crear tablas
@app.before_first_request
def setup_database():
    init_db()

# Middleware para loggear peticiones
@app.before_request
def log_request():
    start_time = datetime.utcnow()
    request.start_time = start_time

@app.after_request
def log_response(response):
    try:
        request_data = None
        if request.is_json:
            request_data = json.dumps(request.get_json())
        
        end_time = datetime.utcnow()
        processing_time = (end_time - request.start_time).total_seconds() * 1000
        
        log = RequestLog(
            method=request.method,
            path=request.path,
            ip=request.remote_addr,
            timestamp=request.start_time,
            user_agent=request.user_agent.string,
            response_status=response.status_code,
            processing_time=int(processing_time),
            request_data=request_data
        )
        
        db_session.add(log)
        db_session.commit()
    except Exception as e:
        logger.error(f"Error al registrar la petición: {str(e)}")
        db_session.rollback()
    
    return response

# Limpiar sesión al finalizar
@app.teardown_appcontext
def shutdown_session_handler(exception=None):
    shutdown_session(exception)

# Rutas básicas
@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado de la API."""
    return jsonify({"status": "ok", "message": "El servicio está funcionando correctamente"})

@app.route('/api/db/test', methods=['GET'])
def db_test():
    """Prueba la conexión a la base de datos."""
    try:
        # Intentar ejecutar una consulta simple para verificar la conexión
        result = db_session.execute('SELECT 1').scalar()
        
        # Obtener el número de solicitudes registradas
        request_count = RequestLog.query.count()
            
        return jsonify({
            "status": "ok",
            "main_db": "conectada",
            "request_count": request_count
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Ruta para listar clientes de SmartVOC
@app.route('/api/smartvoc/clients', methods=['GET'])
def get_smartvoc_clients():
    try:
        clients = SmartVOCClient.query.all()
        if not clients:
            return jsonify({
                "message": "No hay clientes registrados en la base de datos.",
                "clients": []
            }), 200
        
        clients_dict = [client.to_dict() for client in clients]
        return jsonify(clients_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para crear un cliente de SmartVOC
@app.route('/api/smartvoc/clients', methods=['POST'])
def create_smartvoc_client():
    data = request.get_json()
    client_name = data.get("clientName", "")
    
    if not client_name:
        return jsonify({"error": "El parámetro clientName es obligatorio"}), 400
    
    # Generar clientSlug en formato CamelCase
    client_slug = ''.join(word.capitalize() for word in client_name.split())
    
    try:
        # Verificar si ya existe un cliente con ese nombre
        existing_client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if existing_client:
            return jsonify({"error": f"Ya existe un cliente con el nombre '{client_name}'"}), 400
        
        # Crear el nuevo cliente
        new_client = SmartVOCClient(
            clientName=client_name,
            clientSlug=client_slug
        )
        db_session.add(new_client)
        db_session.commit()
        
        return jsonify({"message": f"Cliente {client_name} creado exitosamente"}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

# Endpoints para conversaciones
@app.route('/api/smartvoc/conversations', methods=['GET'])
def get_conversations():
    """Obtiene todas las conversaciones de un cliente."""
    try:
        # Obtener parámetros de consulta
        client_name = request.args.get('clientName')
        
        if not client_name:
            return jsonify({"error": "El parámetro clientName es obligatorio"}), 400
        
        # Verificar si el cliente existe
        client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if not client:
            return jsonify({"error": f"No se encontró el cliente '{client_name}'"}), 404
        
        # Buscar el nombre de la tabla de conversaciones para este cliente
        table_name = f"{client.clientSlug.lower()}_conversations"
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return jsonify({"message": f"No hay conversaciones registradas para el cliente {client_name}", "conversations": []}), 200
        
        # Consultar conversaciones
        query = f"SELECT * FROM {table_name}"
        result = engine.execute(query)
        conversations = [dict(row) for row in result]
        
        return jsonify({"conversations": conversations, "count": len(conversations)}), 200
    except Exception as e:
        logger.error(f"Error al obtener conversaciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartvoc/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Obtiene una conversación específica."""
    try:
        # Obtener parámetros de consulta
        client_name = request.args.get('clientName')
        
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros clientName y conversation_id son obligatorios"}), 400
        
        # Verificar si el cliente existe
        client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if not client:
            return jsonify({"error": f"No se encontró el cliente '{client_name}'"}), 404
        
        # Buscar el nombre de la tabla de conversaciones para este cliente
        table_name = f"{client.clientSlug.lower()}_conversations"
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return jsonify({"error": f"No hay conversaciones registradas para el cliente {client_name}"}), 404
        
        # Consultar la conversación específica
        query = f"SELECT * FROM {table_name} WHERE conversationId = '{conversation_id}'"
        result = engine.execute(query).first()
        
        if not result:
            return jsonify({"error": f"No se encontró la conversación con ID {conversation_id}"}), 404
        
        conversation = dict(result)
        
        return jsonify(conversation), 200
    except Exception as e:
        logger.error(f"Error al obtener conversación: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartvoc/conversations', methods=['POST'])
def create_conversation():
    """Crea una nueva conversación para un cliente."""
    try:
        data = request.get_json()
        client_name = data.get('clientName')
        metadata = data.get('metadata', {})
        conversation_id = data.get('conversationId')
        
        if not client_name:
            return jsonify({"error": "El parámetro clientName es obligatorio"}), 400
        
        # Verificar si el cliente existe
        client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if not client:
            return jsonify({"error": f"No se encontró el cliente '{client_name}'"}), 404
        
        # Generar un ID de conversación si no se proporciona
        if not conversation_id:
            conversation_id = f"conv_{int(datetime.utcnow().timestamp())}_{client.clientId}"
        
        # Crear tabla de conversaciones si no existe
        table_name = f"{client.clientSlug.lower()}_conversations"
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversationId TEXT UNIQUE NOT NULL,
            metadata TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        engine.execute(create_table_query)
        
        # Insertar la conversación
        metadata_json = json.dumps(metadata)
        insert_query = f"""
        INSERT INTO {table_name} (conversationId, metadata)
        VALUES (?, ?)
        """
        engine.execute(insert_query, (conversation_id, metadata_json))
        
        return jsonify({
            "message": "Conversación creada exitosamente",
            "conversationId": conversation_id,
            "clientName": client_name
        }), 201
    except Exception as e:
        logger.error(f"Error al crear conversación: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartvoc/conversations/<conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    """Actualiza una conversación existente."""
    try:
        data = request.get_json()
        client_name = data.get('clientName')
        metadata = data.get('metadata', {})
        
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros clientName y conversation_id son obligatorios"}), 400
        
        # Verificar si el cliente existe
        client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if not client:
            return jsonify({"error": f"No se encontró el cliente '{client_name}'"}), 404
        
        # Verificar si la tabla de conversaciones existe
        table_name = f"{client.clientSlug.lower()}_conversations"
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return jsonify({"error": f"No hay conversaciones registradas para el cliente {client_name}"}), 404
        
        # Verificar si la conversación existe
        check_query = f"SELECT conversationId FROM {table_name} WHERE conversationId = ?"
        result = engine.execute(check_query, (conversation_id,)).first()
        
        if not result:
            return jsonify({"error": f"No se encontró la conversación con ID {conversation_id}"}), 404
        
        # Actualizar la conversación
        metadata_json = json.dumps(metadata)
        update_query = f"UPDATE {table_name} SET metadata = ? WHERE conversationId = ?"
        engine.execute(update_query, (metadata_json, conversation_id))
        
        return jsonify({
            "message": f"Conversación {conversation_id} actualizada exitosamente",
            "conversationId": conversation_id,
            "clientName": client_name
        }), 200
    except Exception as e:
        logger.error(f"Error al actualizar conversación: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartvoc/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Elimina una conversación existente."""
    try:
        # Obtener parámetros de consulta
        client_name = request.args.get('clientName')
        
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros clientName y conversation_id son obligatorios"}), 400
        
        # Verificar si el cliente existe
        client = SmartVOCClient.query.filter_by(clientName=client_name).first()
        if not client:
            return jsonify({"error": f"No se encontró el cliente '{client_name}'"}), 404
        
        # Verificar si la tabla de conversaciones existe
        table_name = f"{client.clientSlug.lower()}_conversations"
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return jsonify({"error": f"No hay conversaciones registradas para el cliente {client_name}"}), 404
        
        # Verificar si la conversación existe
        check_query = f"SELECT conversationId FROM {table_name} WHERE conversationId = ?"
        result = engine.execute(check_query, (conversation_id,)).first()
        
        if not result:
            return jsonify({"error": f"No se encontró la conversación con ID {conversation_id}"}), 404
        
        # Eliminar la conversación
        delete_query = f"DELETE FROM {table_name} WHERE conversationId = ?"
        engine.execute(delete_query, (conversation_id,))
        
        return jsonify({
            "message": f"Conversación {conversation_id} eliminada exitosamente",
            "conversationId": conversation_id,
            "clientName": client_name
        }), 200
    except Exception as e:
        logger.error(f"Error al eliminar conversación: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoints para análisis de conversaciones
@app.route('/api/analysis/<client_name>/<conversation_id>', methods=['GET'])
def get_analysis(client_name, conversation_id):
    """Obtiene el análisis de una conversación específica."""
    try:
        # Validar parámetros
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros client_name y conversation_id son obligatorios"}), 400
        
        # Obtener análisis
        analysis = analysis_service.get_client_analyses(client_name, conversation_id=conversation_id)
        
        if analysis is None:
            return jsonify({"error": "Error al recuperar el análisis"}), 500
            
        if not analysis:
            return jsonify({"message": f"No se encontró análisis para la conversación {conversation_id} del cliente {client_name}"}), 404
            
        return jsonify(analysis[0]), 200
    except Exception as e:
        logger.error(f"Error al obtener análisis: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/<client_name>/<conversation_id>', methods=['POST'])
def create_analysis(client_name, conversation_id):
    """Crea un nuevo análisis para una conversación."""
    try:
        # Validar parámetros
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros client_name y conversation_id son obligatorios"}), 400
        
        # Obtener datos del análisis
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requieren datos para crear el análisis"}), 400
        
        # Verificar si se debe realizar análisis con OpenAI
        perform_ai_analysis = data.pop('performAIAnalysis', False)
        conversation_data = data.pop('conversationData', None)
        
        if perform_ai_analysis and conversation_data:
            # Análisis automático con OpenAI
            analysis_type = data.get('analysisType', 'standard')
            
            analysis = conversation_controller.analyze_conversation(
                client_name=client_name,
                conversation_id=conversation_id,
                conversation_data=conversation_data,
                analysis_type=analysis_type
            )
            
            if analysis is None:
                return jsonify({"error": "Error al analizar la conversación con OpenAI"}), 500
                
            return jsonify({"message": "Análisis creado exitosamente con OpenAI", "analysis": analysis}), 201
        else:
            # Análisis manual (datos proporcionados por el usuario)
            batch_run_id = data.get('batchRunId')
            analysis_type = data.get('analysisType', 'standard')
            
            # Crear análisis con los datos proporcionados
            analysis = analysis_service.create_analysis(
                client_name=client_name,
                conversation_id=conversation_id,
                analysis_data=data,
                batch_run_id=batch_run_id,
                analysis_type=analysis_type
            )
            
            if analysis is None:
                return jsonify({"error": "Error al crear el análisis o ya existe un análisis para esta conversación"}), 400
                
            return jsonify({"message": "Análisis creado exitosamente", "analysis": analysis}), 201
    except Exception as e:
        logger.error(f"Error al crear análisis: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/<client_name>/<conversation_id>', methods=['PUT'])
def update_analysis(client_name, conversation_id):
    """Actualiza un análisis existente."""
    try:
        # Validar parámetros
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros client_name y conversation_id son obligatorios"}), 400
        
        # Obtener datos del análisis
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requieren datos para actualizar el análisis"}), 400
        
        # Verificar si se debe realizar un nuevo análisis con OpenAI
        perform_ai_analysis = data.pop('performAIAnalysis', False)
        conversation_data = data.pop('conversationData', None)
        
        if perform_ai_analysis and conversation_data:
            # Análisis automático con OpenAI
            analysis_type = data.get('analysisType', 'standard')
            
            # Realizar el análisis
            analysis_result = conversation_controller.openai_service.analyze_conversation(
                conversation_data, 
                analysis_type
            )
            
            if not analysis_result:
                return jsonify({"error": "Error al analizar la conversación con OpenAI"}), 500
                
            # Actualizar con los resultados del análisis
            data['deepAnalysis'] = analysis_result
            
        # Actualizar análisis
        analysis = analysis_service.update_analysis(
            client_name=client_name,
            conversation_id=conversation_id,
            analysis_data=data
        )
        
        if analysis is None:
            return jsonify({"error": "Error al actualizar el análisis o no existe un análisis para esta conversación"}), 404
            
        return jsonify({"message": "Análisis actualizado exitosamente", "analysis": analysis}), 200
    except Exception as e:
        logger.error(f"Error al actualizar análisis: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/<client_name>/<conversation_id>', methods=['DELETE'])
def delete_analysis(client_name, conversation_id):
    """Elimina un análisis existente."""
    try:
        # Validar parámetros
        if not client_name or not conversation_id:
            return jsonify({"error": "Los parámetros client_name y conversation_id son obligatorios"}), 400
        
        # Eliminar análisis
        result = analysis_service.delete_analysis(
            client_name=client_name,
            conversation_id=conversation_id
        )
        
        if not result:
            return jsonify({"error": "Error al eliminar el análisis o no existe un análisis para esta conversación"}), 404
            
        return jsonify({"message": f"Análisis para la conversación {conversation_id} eliminado exitosamente"}), 200
    except Exception as e:
        logger.error(f"Error al eliminar análisis: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoints para listar análisis (permite filtrado)
@app.route('/api/analysis/<client_name>', methods=['GET'])
def list_analyses(client_name):
    """Lista los análisis para un cliente específico, con opción de filtrado."""
    try:
        # Validar parámetros
        if not client_name:
            return jsonify({"error": "El parámetro client_name es obligatorio"}), 400
        
        # Parámetros de filtrado opcionales
        conversation_id = request.args.get('conversationId')
        batch_run_id = request.args.get('batchRunId')
        analysis_type = request.args.get('analysisType')
        
        # Obtener análisis
        analyses = analysis_service.get_client_analyses(
            client_name=client_name,
            conversation_id=conversation_id,
            batch_run_id=batch_run_id,
            analysis_type=analysis_type
        )
        
        if analyses is None:
            return jsonify({"error": "Error al recuperar los análisis"}), 500
            
        if not analyses:
            message = f"No se encontraron análisis para el cliente {client_name}"
            if conversation_id:
                message += f" con ID de conversación {conversation_id}"
            if batch_run_id:
                message += f" y ID de lote {batch_run_id}"
            if analysis_type:
                message += f" de tipo {analysis_type}"
            
            return jsonify({"message": message, "analyses": []}), 200
            
        return jsonify({"analyses": analyses, "count": len(analyses)}), 200
    except Exception as e:
        logger.error(f"Error al listar análisis: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoints para procesamiento por lotes
@app.route('/api/batch-analysis/<client_name>', methods=['POST'])
def start_batch_analysis(client_name):
    """Inicia un análisis por lotes para múltiples conversaciones."""
    try:
        # Validar parámetros
        if not client_name:
            return jsonify({"error": "El parámetro client_name es obligatorio"}), 400
        
        # Obtener datos del análisis
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requieren datos para iniciar el análisis por lotes"}), 400
        
        # Obtener conversaciones y tipo de análisis
        conversations = data.get('conversations', [])
        analysis_type = data.get('analysisType', 'standard')
        
        if not conversations:
            return jsonify({"error": "No se proporcionaron conversaciones para analizar"}), 400
        
        # Iniciar el análisis por lotes
        batch_id = conversation_controller.start_batch_analysis(
            client_name=client_name,
            conversations=conversations,
            analysis_type=analysis_type
        )
        
        if not batch_id:
            return jsonify({"error": "Error al iniciar el análisis por lotes"}), 500
            
        return jsonify({
            "message": "Análisis por lotes iniciado exitosamente",
            "batchId": batch_id,
            "status": conversation_controller.get_batch_status(batch_id)
        }), 202  # 202 Accepted
    except Exception as e:
        logger.error(f"Error al iniciar análisis por lotes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch-analysis/<batch_id>/status', methods=['GET'])
def get_batch_status(batch_id):
    """Obtiene el estado de un análisis por lotes."""
    try:
        # Validar parámetros
        if not batch_id:
            return jsonify({"error": "El parámetro batch_id es obligatorio"}), 400
        
        # Obtener estado del lote
        status = conversation_controller.get_batch_status(batch_id)
        
        if not status:
            return jsonify({"error": f"No se encontró información para el lote {batch_id}"}), 404
            
        return jsonify({"batchId": batch_id, "status": status}), 200
    except Exception as e:
        logger.error(f"Error al obtener estado del lote: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch-analysis', methods=['GET'])
def list_batch_statuses():
    """Lista todos los estados de análisis por lotes."""
    try:
        # Parámetro opcional: filtrar por cliente
        client_name = request.args.get('clientName')
        
        # Obtener estados de los lotes
        statuses = conversation_controller.get_all_batch_statuses(client_name)
        
        if not statuses:
            message = "No hay procesos de análisis por lotes"
            if client_name:
                message += f" para el cliente {client_name}"
            return jsonify({"message": message, "batches": {}}), 200
            
        return jsonify({"batches": statuses, "count": len(statuses)}), 200
    except Exception as e:
        logger.error(f"Error al listar estados de lotes: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Iniciar el servidor de desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000) 