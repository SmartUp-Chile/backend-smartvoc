from flask_restx import Resource

class HealthResource(Resource):
    def get(self):
        """Verifica el estado del servicio."""
        from api import health_ns as ns, health_model
        
        @ns.doc('get_health_status')
        @ns.response(200, 'Éxito', health_model)
        def decorated_get():
            return {
                "status": "ok",
                "message": "El servicio está funcionando correctamente con hot reload activado"
            }
        
        return decorated_get() 