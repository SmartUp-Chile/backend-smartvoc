from flask import Blueprint, jsonify, request
from app import db

# Crear un Blueprint para las rutas de SmartVOC
smartvoc_bp = Blueprint('smartvoc', __name__, url_prefix='/api')

@smartvoc_bp.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar la salud del servicio."""
    return jsonify({
        "status": "ok",
        "service": "smartvoc"
    }), 200

@smartvoc_bp.route('/db-test', methods=['GET'])
def db_test():
    """Endpoint para probar la conexión a la base de datos."""
    try:
        # Intentar ejecutar una consulta simple para verificar la conexión
        # Usamos el motor de la base de datos principal
        db.session.execute('SELECT 1')
        
        # Si queremos probar una base de datos específica de las múltiples configuradas:
        if 'db_smartvoc' in db.engines:
            db.engines['db_smartvoc'].execute('SELECT 1')
            db_status = "conectada"
        else:
            db_status = "no configurada"
            
        return jsonify({
            "status": "ok",
            "service": "smartvoc",
            "database": db_status
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "service": "smartvoc",
            "error": str(e)
        }), 500 