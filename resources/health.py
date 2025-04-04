from flask_restx import Resource
from api import health_ns as ns, health_model

@ns.route('/')
class HealthResource(Resource):
    @ns.doc('get_health_status')
    @ns.response(200, 'Éxito', health_model)
    def get(self):
        """Verifica el estado del servicio."""
        return {
            "status": "ok",
            "message": "El servicio está funcionando correctamente con hot reload activado"
        } 