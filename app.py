from flask import Flask, jsonify
import logging
from routes.smartvoc_routes import bp as smartvoc_bp
from routes.analysis_routes import bp as analysis_bp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Registrar blueprints
app.register_blueprint(smartvoc_bp)
app.register_blueprint(analysis_bp)

# Ruta de salud básica
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Servicio funcionando correctamente"
    })

# Punto de entrada principal
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 