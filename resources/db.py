from flask_restx import Resource
from api import db_ns as ns, db_test_model, db_error_model
from app import db
from models import RequestLog

@ns.route('/test')
class DBTestResource(Resource):
    @ns.doc('test_database_connection')
    @ns.response(200, 'Conexión exitosa', db_test_model)
    @ns.response(500, 'Error de conexión', db_error_model)
    def get(self):
        """Prueba la conexión a la base de datos."""
        try:
            # Intentar ejecutar una consulta simple para verificar la conexión
            result = db.session.execute('SELECT 1').scalar()
            
            # Obtener el número de solicitudes registradas
            request_count = RequestLog.query.count()
                
            return {
                "status": "ok",
                "main_db": "conectada",
                "request_count": request_count
            }, 200
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }, 500 