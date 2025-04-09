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
from utils.validation import validate_with, validate_path_params
from utils.exceptions import ValidationError
from utils.error_handler import log_exception
from schemas.client import (
    ClientPathParamsSchema,
    ClientCreateSchema,
    ClientUpdateSchema,
    ClientQueryParamsSchema
)
from schemas.conversation import (
    ConversationPathParamsSchema,
    ConversationCreateSchema,
    ConversationUpdateSchema,
    ConversationQueryParamsSchema
)

# Crear el blueprint para rutas de SmartVOC
bp = Blueprint('smartvoc', __name__, url_prefix='/api/smartvoc')

@bp.route('/clients', methods=['GET'])
@validate_with(ClientQueryParamsSchema, location='args')
def get_clients(validated_data):
    """Obtiene todos los clientes de SmartVOC registrados en la base de datos."""
    response, status_code = SmartVOCService.get_clients(validated_data)
    return jsonify(response), status_code

@bp.route('/clients', methods=['POST'])
@validate_with(ClientCreateSchema)
def create_client(validated_data):
    """Crea un nuevo cliente de SmartVOC con sus tablas relacionadas."""
    response, status_code = SmartVOCService.create_client(validated_data)
    return jsonify(response), status_code

@bp.route('/clients/<client_id>', methods=['GET'])
@validate_path_params(ClientPathParamsSchema)
def get_client(client_id):
    """Obtiene los detalles de un cliente específico."""
    response, status_code = SmartVOCService.get_client(client_id)
    return jsonify(response), status_code

@bp.route('/clients/<client_id>', methods=['PUT'])
@validate_path_params(ClientPathParamsSchema)
@validate_with(ClientUpdateSchema)
def update_client(validated_data, client_id):
    """Actualiza los datos de un cliente existente."""
    response, status_code = SmartVOCService.update_client(client_id, validated_data)
    return jsonify(response), status_code

@bp.route('/clients/<client_id>', methods=['DELETE'])
@validate_path_params(ClientPathParamsSchema)
def delete_client(client_id):
    """Elimina un cliente y todas sus tablas asociadas."""
    response, status_code = SmartVOCService.delete_client(client_id)
    return jsonify(response), status_code

# Rutas para gestión de conversaciones
@bp.route('/conversations', methods=['GET'])
@validate_with(ConversationQueryParamsSchema, location='args')
def get_conversations(validated_data):
    """Obtiene conversaciones para un cliente específico."""
    response, status_code = SmartVOCService.get_conversations(validated_data)
    return jsonify(response), status_code

@bp.route('/conversations', methods=['POST'])
@validate_with(ConversationCreateSchema)
def create_conversation(validated_data):
    """Crea una nueva conversación para un cliente específico."""
    response, status_code = SmartVOCService.create_conversation(validated_data)
    return jsonify(response), status_code

@bp.route('/conversations/<conversation_id>', methods=['GET'])
@validate_path_params(ConversationPathParamsSchema)
def get_conversation(conversation_id):
    """Obtiene una conversación específica."""
    client_id = request.args.get('clientId')
    if not client_id:
        raise ValidationError(
            message="El parámetro clientId es obligatorio",
            details={"missing_fields": ["clientId"]}
        )
    response, status_code = SmartVOCService.get_conversation(client_id, conversation_id)
    return jsonify(response), status_code

@bp.route('/conversations/<conversation_id>', methods=['PUT'])
@validate_path_params(ConversationPathParamsSchema)
@validate_with(ConversationUpdateSchema)
def update_conversation(validated_data, conversation_id):
    """Actualiza una conversación existente."""
    response, status_code = SmartVOCService.update_conversation(conversation_id, validated_data)
    return jsonify(response), status_code

@bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@validate_path_params(ConversationPathParamsSchema)
def delete_conversation(conversation_id):
    """Elimina una conversación existente."""
    client_id = request.args.get('clientId')
    if not client_id:
        raise ValidationError(
            message="El parámetro clientId es obligatorio",
            details={"missing_fields": ["clientId"]}
        )
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