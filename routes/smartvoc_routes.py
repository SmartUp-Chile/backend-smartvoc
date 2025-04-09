from flask import Blueprint, request, jsonify, current_app
from db import db_session
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
    response, status_code = SmartVOCService.get_clients()
    return jsonify(response), status_code

@bp.route('/clients', methods=['POST'])
def create_client():
    """Crea un nuevo cliente de SmartVOC con sus tablas relacionadas."""
    data = request.json
    response, status_code = SmartVOCService.create_client(data)
    return jsonify(response), status_code

@bp.route('/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    """Obtiene los detalles de un cliente específico."""
    response, status_code = SmartVOCService.get_client(client_id)
    return jsonify(response), status_code

@bp.route('/clients/<client_id>', methods=['PUT'])
def update_client(client_id):
    """Actualiza los datos de un cliente existente."""
    data = request.json
    response, status_code = SmartVOCService.update_client(client_id, data)
    return jsonify(response), status_code

@bp.route('/clients/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Elimina un cliente y todas sus tablas asociadas."""
    response, status_code = SmartVOCService.delete_client(client_id)
    return jsonify(response), status_code

# Rutas para gestión de conversaciones
@bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Obtiene conversaciones para un cliente específico."""
    params = {
        'client_id': request.args.get('clientId'),
        'client_name': request.args.get('clientName'),
        'conversation_id': request.args.get('conversationId'),
        'limit': request.args.get('limit', 10),
        'offset': request.args.get('offset', 0)
    }
    response, status_code = SmartVOCService.get_conversations(params)
    return jsonify(response), status_code

@bp.route('/conversations', methods=['POST'])
def create_conversation():
    """Crea una nueva conversación para un cliente específico."""
    data = request.json
    response, status_code = SmartVOCService.create_conversation(data)
    return jsonify(response), status_code

@bp.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Obtiene una conversación específica."""
    client_id = request.args.get('clientId')
    response, status_code = SmartVOCService.get_conversation(client_id, conversation_id)
    return jsonify(response), status_code

@bp.route('/conversations/<conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    """Actualiza una conversación existente."""
    data = request.json
    response, status_code = SmartVOCService.update_conversation(conversation_id, data)
    return jsonify(response), status_code

@bp.route('/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Elimina una conversación existente."""
    client_id = request.args.get('clientId')
    response, status_code = SmartVOCService.delete_conversation(client_id, conversation_id)
    return jsonify(response), status_code

@bp.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar la salud del servicio."""
    response, status_code = SmartVOCService.health_check()
    return jsonify(response), status_code

@bp.route('/db-test', methods=['GET'])
def db_test():
    """Endpoint para probar la conexión a la base de datos."""
    response, status_code = SmartVOCService.db_test()
    return jsonify(response), status_code 