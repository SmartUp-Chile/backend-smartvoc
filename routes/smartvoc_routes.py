from flask import Blueprint, request, jsonify, current_app
from app import db
from models import SmartVOCClient, ClientDetails, FieldGroup, GenerativeAnalysis, Analysis, DynamicTableManager
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import json
import time
from datetime import datetime
import uuid
from utils.smartvoc_service import SmartVOCService

# Crear el blueprint para rutas de SmartVOC
bp = Blueprint('smartvoc', __name__, url_prefix='/api/smartvoc')

@bp.route('/clients', methods=['GET'])
def get_clients():
    """Obtiene todos los clientes de SmartVOC registrados en la base de datos."""
    try:
        # Verificar si la tabla existe
        inspector = inspect(db.engine)
        if not inspector.has_table('smartvoc_clients'):
            return jsonify({
                "message": "La tabla de clientes no existe. No hay clientes registrados.",
                "clients": []
            }), 200
        
        # Consultar los clientes usando el ORM
        clients = SmartVOCClient.query.all()
        
        if not clients:
            return jsonify({
                "message": "No hay clientes registrados en la base de datos.",
                "clients": []
            }), 200
        
        # Convertir los objetos a diccionarios
        clients_dict = [client.to_dict() for client in clients]
        return jsonify(clients_dict), 200
    except Exception as e:
        current_app.logger.error(f"Error al obtener clientes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/clients', methods=['POST'])
def create_client():
    """Crea un nuevo cliente de SmartVOC con sus tablas relacionadas."""
    data = request.json
    
    # Validar datos de entrada
    if not data or not data.get('clientName'):
        return jsonify({"error": "El parámetro clientName es obligatorio"}), 400
    
    client_name = data.get('clientName')
    
    # Usar el servicio para crear el cliente
    result = SmartVOCService.create_client(client_name)
    
    if result['success']:
        return jsonify({
            "message": result['message'],
            "client": result['client']
        }), 201
    else:
        return jsonify({"error": result['error']}), 400

@bp.route('/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    """Obtiene los detalles de un cliente específico."""
    # Usar el servicio para obtener el cliente
    result = SmartVOCService.get_client(client_id=client_id)
    
    if result['success']:
        return jsonify(result['client']), 200
    else:
        return jsonify({"error": result['error']}), 404

@bp.route('/clients/<client_id>', methods=['PUT'])
def update_client(client_id):
    """Actualiza los datos de un cliente existente."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400
    
    # Usar el servicio para actualizar el cliente
    result = SmartVOCService.update_client(client_id, data)
    
    if result['success']:
        return jsonify({
            "message": result['message'],
            "client": result['client']
        }), 200
    else:
        return jsonify({"error": result['error']}), 404

@bp.route('/clients/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Elimina un cliente y todas sus tablas asociadas."""
    # Usar el servicio para eliminar el cliente
    result = SmartVOCService.delete_client(client_id)
    
    if result['success']:
        return jsonify({"message": result['message']}), 200
    else:
        return jsonify({"error": result['error']}), 404

# Rutas para gestión de conversaciones
@bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Obtiene conversaciones para un cliente específico."""
    client_id = request.args.get('clientId')
    client_name = request.args.get('clientName')
    
    if not client_id and not client_name:
        return jsonify({"error": "Debe proporcionar clientId o clientName"}), 400
    
    try:
        # Obtener el cliente
        client = None
        if client_id:
            client = SmartVOCClient.query.filter_by(client_id=client_id).first()
        elif client_name:
            client = SmartVOCClient.query.filter_by(client_name=client_name).first()
        
        if not client:
            return jsonify({"error": "Cliente no encontrado"}), 404
        
        # Verificar si existe la tabla de conversaciones
        table_name = f"Conversations__{client.client_slug}"
        if not DynamicTableManager.table_exists(table_name):
            return jsonify({
                "message": f"No hay conversaciones para el cliente '{client.client_name}'",
                "conversations": []
            }), 200
        
        # Obtener parámetros de filtrado y paginación
        conversation_id = request.args.get('conversationId')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # Construir la consulta
        query = f"SELECT * FROM {table_name}"
        if conversation_id:
            query += f" WHERE conversation_id = '{conversation_id}'"
        query += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
        
        # Ejecutar la consulta
        result = DynamicTableManager.execute_query(query)
        conversations = [SmartVOCConversation.to_dict(row) for row in result]
        
        return jsonify({
            "conversations": conversations,
            "total": len(conversations),
            "limit": limit,
            "offset": offset
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error al obtener conversaciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/conversations', methods=['POST'])
def create_conversation():
    """Crea una nueva conversación para un cliente específico."""
    data = request.json
    
    # Validar datos de entrada
    if not data:
        return jsonify({"error": "No se proporcionaron datos para la conversación"}), 400
    
    client_id = data.get('clientId')
    if not client_id:
        return jsonify({"error": "El parámetro clientId es obligatorio"}), 400
    
    # Usar el servicio para crear la conversación
    result = SmartVOCService.create_conversation(client_id, data)
    
    if result['success']:
        return jsonify({
            "message": result['message'],
            "conversationId": result['conversationId']
        }), 201
    else:
        return jsonify({"error": result['error']}), 400

@bp.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Obtiene una conversación específica."""
    client_id = request.args.get('clientId')
    
    if not client_id:
        return jsonify({"error": "El parámetro clientId es obligatorio"}), 400
    
    # Usar el servicio para obtener la conversación
    result = SmartVOCService.get_conversation(client_id, conversation_id)
    
    if result['success']:
        return jsonify(result['conversation']), 200
    else:
        return jsonify({"error": result['error']}), 404

# Importación adicional para evitar errores
from models import SmartVOCConversation

@bp.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar la salud del servicio."""
    return jsonify({
        "status": "ok",
        "message": "El servicio SmartVOC está funcionando correctamente"
    }), 200

@bp.route('/db-test', methods=['GET'])
def db_test():
    """Endpoint para probar la conexión a la base de datos."""
    try:
        # Intentar consultar la tabla de clientes
        inspector = inspect(db.engine)
        if inspector.has_table('smartvoc_clients'):
            return jsonify({
                "status": "ok",
                "message": "Conexión exitosa a la base de datos"
            }), 200
        else:
            return jsonify({
                "status": "warning",
                "message": "Conexión exitosa pero la tabla SmartVOCClients no existe"
            }), 200
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al conectar a la base de datos: {str(e)}"
        }), 500 