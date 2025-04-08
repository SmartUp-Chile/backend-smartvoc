"""
Controlador para el análisis de conversaciones.
Este módulo coordina el proceso de análisis de conversaciones,
integrando los servicios de análisis y OpenAI.
"""
import logging
import json
import uuid
import threading
from datetime import datetime

from utils.analysis_service import AnalysisService
from utils.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ConversationController:
    """
    Controlador para el análisis de conversaciones.
    Esta clase coordina el proceso de análisis de conversaciones,
    utilizando los servicios de análisis y OpenAI.
    """
    
    def __init__(self, db_session):
        """
        Inicializa el controlador de conversaciones.
        
        Args:
            db_session: Sesión de base de datos SQLAlchemy
        """
        self.db_session = db_session
        self.analysis_service = AnalysisService(db_session)
        self.openai_service = OpenAIService()
        self.batch_processes = {}  # Almacena información sobre procesos por lotes en curso
    
    def analyze_conversation(self, client_name, conversation_id, conversation_data, analysis_type="standard"):
        """
        Analiza una conversación individual y almacena los resultados.
        
        Args:
            client_name: Nombre del cliente
            conversation_id: ID de la conversación
            conversation_data: Datos de la conversación
            analysis_type: Tipo de análisis a realizar
            
        Returns:
            dict: Resultados del análisis
            None: Si ocurre un error
        """
        try:
            # Realizar el análisis con OpenAI
            analysis_result = self.openai_service.analyze_conversation(conversation_data, analysis_type)
            
            if not analysis_result:
                logger.error(f"Error al analizar la conversación {conversation_id}")
                return None
            
            # Crear el registro de análisis
            analysis_data = {
                "deepAnalysis": analysis_result,
                "status": "completed"
            }
            
            # Almacenar los resultados del análisis
            stored_analysis = self.analysis_service.create_analysis(
                client_name=client_name,
                conversation_id=conversation_id,
                analysis_data=analysis_data,
                analysis_type=analysis_type
            )
            
            return stored_analysis
            
        except Exception as e:
            logger.error(f"Error en el proceso de análisis para {conversation_id}: {str(e)}")
            return None
    
    def start_batch_analysis(self, client_name, conversations, analysis_type="standard"):
        """
        Inicia un análisis por lotes en un hilo separado.
        
        Args:
            client_name: Nombre del cliente
            conversations: Lista de conversaciones a analizar
            analysis_type: Tipo de análisis a realizar
            
        Returns:
            str: ID del proceso por lotes
            None: Si ocurre un error
        """
        try:
            if not conversations:
                logger.warning("No se proporcionaron conversaciones para el análisis por lotes")
                return None
            
            # Generar un ID único para el lote
            batch_id = str(uuid.uuid4())
            
            # Inicializar el estado del proceso
            self.batch_processes[batch_id] = {
                "total": len(conversations),
                "completed": 0,
                "failed": 0,
                "status": "starting",
                "client_name": client_name,
                "start_time": datetime.utcnow().isoformat(),
                "analysis_type": analysis_type
            }
            
            # Iniciar el procesamiento en un hilo separado
            thread = threading.Thread(
                target=self._process_batch,
                args=(batch_id, client_name, conversations, analysis_type)
            )
            thread.daemon = True
            thread.start()
            
            return batch_id
            
        except Exception as e:
            logger.error(f"Error al iniciar el análisis por lotes: {str(e)}")
            return None
    
    def _process_batch(self, batch_id, client_name, conversations, analysis_type):
        """
        Procesa un lote de conversaciones en segundo plano.
        
        Args:
            batch_id: ID del lote
            client_name: Nombre del cliente
            conversations: Lista de conversaciones a analizar
            analysis_type: Tipo de análisis a realizar
        """
        try:
            # Actualizar el estado del proceso
            self.batch_processes[batch_id]["status"] = "processing"
            
            # Procesar cada conversación
            for conversation in conversations:
                try:
                    # Extraer el ID de la conversación
                    conversation_id = conversation.get('id')
                    if not conversation_id:
                        logger.warning(f"Conversación sin ID en el lote {batch_id}, se omitirá")
                        self.batch_processes[batch_id]["failed"] += 1
                        continue
                    
                    # Analizar la conversación
                    analysis_result = self.openai_service.analyze_conversation(conversation, analysis_type)
                    
                    if not analysis_result:
                        logger.error(f"Error al analizar la conversación {conversation_id} en el lote {batch_id}")
                        self.batch_processes[batch_id]["failed"] += 1
                        continue
                    
                    # Crear el registro de análisis
                    analysis_data = {
                        "deepAnalysis": analysis_result,
                        "batchRunId": batch_id,
                        "status": "completed"
                    }
                    
                    # Almacenar los resultados del análisis
                    stored_analysis = self.analysis_service.create_analysis(
                        client_name=client_name,
                        conversation_id=conversation_id,
                        analysis_data=analysis_data,
                        batch_run_id=batch_id,
                        analysis_type=analysis_type
                    )
                    
                    if stored_analysis:
                        self.batch_processes[batch_id]["completed"] += 1
                    else:
                        self.batch_processes[batch_id]["failed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error al procesar la conversación en el lote {batch_id}: {str(e)}")
                    self.batch_processes[batch_id]["failed"] += 1
            
            # Actualizar el estado final del proceso
            self.batch_processes[batch_id]["status"] = "completed"
            self.batch_processes[batch_id]["end_time"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Error en el procesamiento del lote {batch_id}: {str(e)}")
            self.batch_processes[batch_id]["status"] = "failed"
            self.batch_processes[batch_id]["error"] = str(e)
            self.batch_processes[batch_id]["end_time"] = datetime.utcnow().isoformat()
    
    def get_batch_status(self, batch_id):
        """
        Obtiene el estado de un proceso por lotes.
        
        Args:
            batch_id: ID del lote
            
        Returns:
            dict: Estado del proceso por lotes
            None: Si el lote no existe
        """
        return self.batch_processes.get(batch_id)
    
    def get_all_batch_statuses(self, client_name=None):
        """
        Obtiene el estado de todos los procesos por lotes.
        
        Args:
            client_name: Filtrar por nombre de cliente (opcional)
            
        Returns:
            dict: Estado de todos los procesos por lotes
        """
        if not client_name:
            return self.batch_processes
        
        # Filtrar por cliente
        return {
            batch_id: status
            for batch_id, status in self.batch_processes.items()
            if status.get("client_name") == client_name
        } 