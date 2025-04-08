from flask_restx import Resource, Namespace, fields
from flask import request, jsonify
from models import Analysis, SmartVOCClient, db
from datetime import datetime

analysis_ns = Namespace('analysis', description='Operaciones relacionadas con el análisis de conversaciones')

analysis_model = analysis_ns.model('Analysis', {
    'id': fields.Integer(readonly=True, description='Identificador único del análisis'),
    'conversation_id': fields.String(required=True, description='ID de la conversación analizada'),
    'client_id': fields.String(required=True, description='ID del cliente'),
    'analysis_type': fields.String(required=True, description='Tipo de análisis realizado'),
    'result': fields.Raw(required=True, description='Resultados del análisis'),
    'created_at': fields.DateTime(readonly=True, description='Fecha de creación'),
    'updated_at': fields.DateTime(readonly=True, description='Fecha de última actualización')
})

@analysis_ns.route('/<string:conversation_id>')
class AnalysisResource(Resource):
    @analysis_ns.doc('get_analysis')
    @analysis_ns.response(200, 'Success', analysis_model)
    @analysis_ns.response(404, 'Analysis not found')
    def get(self, conversation_id):
        """Obtener el análisis de una conversación específica"""
        analysis = Analysis.query.filter_by(conversation_id=conversation_id).first()
        if not analysis:
            return {'message': 'Análisis no encontrado'}, 404
        return analysis.__dict__, 200

    @analysis_ns.doc('create_analysis')
    @analysis_ns.expect(analysis_model)
    @analysis_ns.response(201, 'Analysis created successfully')
    @analysis_ns.response(400, 'Invalid input')
    def post(self, conversation_id):
        """Crear un nuevo análisis para una conversación"""
        data = request.get_json()
        
        # Verificar si el cliente existe
        client = SmartVOCClient.query.filter_by(client_id=data['client_id']).first()
        if not client:
            return {'message': 'Cliente no encontrado'}, 404
            
        analysis = Analysis(
            conversation_id=conversation_id,
            client_id=data['client_id'],
            analysis_type=data['analysis_type'],
            result=data['result']
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return {'message': 'Análisis creado exitosamente', 'id': analysis.id}, 201

    @analysis_ns.doc('update_analysis')
    @analysis_ns.expect(analysis_model)
    @analysis_ns.response(200, 'Analysis updated successfully')
    @analysis_ns.response(404, 'Analysis not found')
    def put(self, conversation_id):
        """Actualizar un análisis existente"""
        analysis = Analysis.query.filter_by(conversation_id=conversation_id).first()
        if not analysis:
            return {'message': 'Análisis no encontrado'}, 404
            
        data = request.get_json()
        
        analysis.analysis_type = data.get('analysis_type', analysis.analysis_type)
        analysis.result = data.get('result', analysis.result)
        analysis.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {'message': 'Análisis actualizado exitosamente'}, 200

    @analysis_ns.doc('delete_analysis')
    @analysis_ns.response(200, 'Analysis deleted successfully')
    @analysis_ns.response(404, 'Analysis not found')
    def delete(self, conversation_id):
        """Eliminar un análisis"""
        analysis = Analysis.query.filter_by(conversation_id=conversation_id).first()
        if not analysis:
            return {'message': 'Análisis no encontrado'}, 404
            
        db.session.delete(analysis)
        db.session.commit()
        
        return {'message': 'Análisis eliminado exitosamente'}, 200 