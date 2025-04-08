# Este archivo permite que Python trate el directorio 'routes' como un paquete 

# Importación de blueprints para facilitar su registro en app.py
from routes.smartvoc_routes import bp as smartvoc_bp

# Lista de todos los blueprints disponibles
blueprints = [
    smartvoc_bp
] 