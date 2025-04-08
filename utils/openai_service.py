"""
Servicio para integración con Azure OpenAI.
Este módulo contiene las funcionalidades para interactuar con Azure OpenAI
para el análisis de conversaciones.
"""
import os
import json
import logging
import time
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Servicio para integración con Azure OpenAI.
    Esta clase proporciona métodos para analizar conversaciones 
    utilizando los modelos de Azure OpenAI.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de OpenAI con las credenciales de Azure.
        """
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY', '')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-35-turbo')
        
        # Verificar que las credenciales estén configuradas
        if not self.api_key or not self.endpoint:
            logger.warning("Las credenciales de Azure OpenAI no están configuradas correctamente.")
    
    def _get_headers(self):
        """
        Obtiene los headers necesarios para la API de Azure OpenAI.
        
        Returns:
            dict: Headers para las solicitudes a la API
        """
        return {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
    
    def _get_api_url(self):
        """
        Construye la URL de la API de Azure OpenAI.
        
        Returns:
            str: URL de la API
        """
        return f"{self.endpoint}openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
    
    def analyze_conversation(self, conversation, analysis_type="standard"):
        """
        Analiza una conversación utilizando Azure OpenAI.
        
        Args:
            conversation (dict): Conversación a analizar
            analysis_type (str): Tipo de análisis a realizar
            
        Returns:
            dict: Resultados del análisis
            None: Si ocurre un error
        """
        try:
            if not self.api_key or not self.endpoint:
                logger.error("No se pueden realizar análisis sin las credenciales de Azure OpenAI")
                return None
            
            # Preparar el mensaje para la API según el tipo de análisis
            if analysis_type == "standard":
                system_message = """Eres un asistente experto en análisis de conversaciones. 
                Tu tarea es analizar la siguiente conversación y proporcionar:
                1. Un resumen conciso de la conversación
                2. Los temas principales discutidos
                3. Los sentimientos expresados por cada participante
                4. Problemas o quejas identificados
                5. Acciones o soluciones propuestas
                
                Organiza tu respuesta en formato JSON con las siguientes claves:
                summary, topics, sentiment, issues, actions
                """
            elif analysis_type == "deep":
                system_message = """Eres un asistente experto en análisis profundo de conversaciones.
                Tu tarea es analizar minuciosamente la siguiente conversación y proporcionar:
                1. Un resumen detallado de la conversación
                2. Los temas principales y secundarios discutidos
                3. Análisis detallado de sentimientos para cada participante
                4. Problemas o quejas identificados con nivel de urgencia (bajo, medio, alto)
                5. Acciones o soluciones propuestas
                6. Recomendaciones específicas para seguimiento
                7. Métricas de calidad de la conversación
                
                Organiza tu respuesta en formato JSON con las siguientes claves:
                summary, topics (array), sentiment (object por participante), 
                issues (array con objetos que incluyan description y urgency), 
                actions (array), recommendations (array), quality_metrics (object)
                """
            else:
                system_message = f"""Eres un asistente experto en análisis de conversaciones.
                Realizarás un análisis de tipo {analysis_type}.
                Analiza la siguiente conversación y proporciona tus hallazgos en formato JSON.
                """
            
            # Convertir la conversación a texto si es un objeto
            conversation_text = json.dumps(conversation) if isinstance(conversation, dict) else str(conversation)
            
            # Construir el payload
            payload = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Aquí está la conversación a analizar:\n\n{conversation_text}"}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # Realizar la solicitud a la API
            response = requests.post(
                self._get_api_url(),
                headers=self._get_headers(),
                json=payload,
                timeout=60  # 60 segundos de timeout
            )
            
            # Verificar la respuesta
            if response.status_code != 200:
                logger.error(f"Error en la API de Azure OpenAI: {response.status_code} - {response.text}")
                return None
            
            # Extraer la respuesta
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Intentar parsear el contenido como JSON
            try:
                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                # Si no es JSON válido, devolver como texto
                return {"analysis": content}
            
        except Exception as e:
            logger.error(f"Error al analizar la conversación: {str(e)}")
            return None
    
    def batch_analyze_conversations(self, conversations, analysis_type="standard", max_retries=3, retry_delay=2):
        """
        Analiza un lote de conversaciones.
        
        Args:
            conversations (list): Lista de conversaciones a analizar
            analysis_type (str): Tipo de análisis a realizar
            max_retries (int): Número máximo de reintentos por conversación
            retry_delay (int): Segundos de espera entre reintentos
            
        Returns:
            dict: Resultados del análisis por ID de conversación
            None: Si ocurre un error
        """
        if not conversations:
            logger.warning("No se proporcionaron conversaciones para analizar")
            return {}
        
        results = {}
        for conv in conversations:
            conv_id = conv.get('id', str(hash(json.dumps(conv))))
            retries = 0
            success = False
            
            while retries < max_retries and not success:
                try:
                    analysis = self.analyze_conversation(conv, analysis_type)
                    if analysis:
                        results[conv_id] = analysis
                        success = True
                    else:
                        retries += 1
                        logger.warning(f"Reintento {retries}/{max_retries} para conversación {conv_id}")
                        time.sleep(retry_delay)
                except Exception as e:
                    retries += 1
                    logger.error(f"Error en el análisis de conversación {conv_id}: {str(e)}")
                    time.sleep(retry_delay)
            
            if not success:
                results[conv_id] = {"error": f"No se pudo analizar después de {max_retries} intentos"}
        
        return results 