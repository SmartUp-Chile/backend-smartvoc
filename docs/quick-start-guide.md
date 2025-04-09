# Guía de Inicio Rápido - API SmartVOC

Esta guía te ayudará a comenzar a utilizar la API de SmartVOC rápidamente, cubriendo los aspectos fundamentales para la integración exitosa con tus sistemas.

## Índice
1. [Instalación y Configuración](#instalación-y-configuración)
2. [Primeros Pasos](#primeros-pasos)
3. [Gestión de Clientes](#gestión-de-clientes)
4. [Manejo de Conversaciones](#manejo-de-conversaciones)
5. [Análisis Generativo](#análisis-generativo)
6. [Flujos de Trabajo Completos](#flujos-de-trabajo-completos)
7. [Paginación y Filtrado](#paginación-y-filtrado)
8. [Manejo de Errores](#manejo-de-errores)
9. [Mejores Prácticas](#mejores-prácticas)
10. [Solución de Problemas Comunes](#solución-de-problemas-comunes)
11. [Referencias](#referencias)

## Instalación y Configuración

### Requisitos Previos
- Python 3.8+ o Docker
- Cliente HTTP (curl, Postman, etc.)
- Acceso a un servidor API SmartVOC (local o remoto)

### Instalación Local

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/SmartUp-Chile/backend-smartvoc.git
   cd backend-smartvoc
   ```

2. **Configurar el entorno**
   ```bash
   # Crear y activar entorno virtual
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   
   # Instalar dependencias
   pip install -r requirements.txt
   
   # Configurar variables de entorno
   cp .env.example .env
   # Editar .env según tus necesidades
   ```

3. **Iniciar el servidor**
   ```bash
   flask run
   # La API estará disponible en http://localhost:5000
   ```

### Instalación con Docker

1. **Construir y ejecutar con Docker Compose**
   ```bash
   docker-compose up --build
   # La API estará disponible en http://localhost:8000
   ```

### Verificación de la Instalación

Verifica que la API esté funcionando correctamente:

```bash
curl http://localhost:8000/api/health
```

Deberías recibir una respuesta similar a:
```json
{
  "status": "ok",
  "version": "0.3.0",
  "timestamp": "2025-04-10T15:22:33.456789"
}
```

## Primeros Pasos

### Estructura de la API

La API SmartVOC tiene dos formas principales de interacción:

1. **Endpoints REST tradicionales** (principalmente para análisis):
   - `GET /api/analysis/<client_name>/<conversation_id>`
   - `POST /api/analysis/<client_name>`
   - `PUT /api/analysis/<client_name>/<conversation_id>/<analysis_type>`
   - `DELETE /api/analysis/<client_name>/<conversation_id>/<analysis_type>`

2. **Endpoint unificado** para operaciones de SmartVOC:
   - `POST /api/smartvoc` con diferentes valores para el parámetro `operation`

### Convenciones de Nombres

- `client_name`: Nombre del cliente (sensible a mayúsculas/minúsculas)
- `conversation_id`: ID único de la conversación
- `analysis_type`: Tipo de análisis (basic, sentiment, intent, etc.)

## Gestión de Clientes

Antes de poder administrar conversaciones o análisis, necesitas crear un cliente en el sistema.

### Crear un Nuevo Cliente

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "create-smartvoc-client",
    "parameters": {
        "clientName": "MiCliente",
        "clientSlug": "mi-cliente",
        "metadata": {
            "industry": "retail",
            "country": "chile"
        }
    }
}'
```

### Listar Clientes Existentes

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "get-all-smartvoc-clients"
}'
```

### Obtener Detalles de un Cliente

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "client-details",
    "parameters": {
        "clientName": "MiCliente"
    }
}'
```

## Manejo de Conversaciones

Las conversaciones son la unidad básica de datos que analizarás con SmartVOC.

### Crear una Nueva Conversación

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "MiCliente",
        "conversation": [
            {"role": "user", "content": "Hola, tengo un problema con mi pedido"},
            {"role": "assistant", "content": "Claro, ¿cuál es el número de su pedido?"},
            {"role": "user", "content": "El número es ABC123"}
        ],
        "metadata": {
            "channel": "chat",
            "duration": 120,
            "agent_id": "agent007"
        }
    }
}'
```

### Obtener Conversaciones

Por ID específico:
```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "MiCliente",
        "conversationId": "CONV123"
    }
}'
```

Con filtros:
```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "MiCliente",
        "filters": {
            "startDate": "2025-04-01",
            "endDate": "2025-04-10",
            "metadata.channel": "chat"
        },
        "page": 1,
        "pageSize": 10
    }
}'
```

### Actualizar una Conversación

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "MiCliente",
        "conversationId": "CONV123",
        "metadata": {
            "status": "closed",
            "satisfaction_score": 9
        }
    }
}'
```

## Análisis Generativo

El análisis generativo es una característica central de SmartVOC que te permite extraer información valiosa de las conversaciones.

### Crear un Análisis

Usando el endpoint REST:
```bash
curl -X POST "http://localhost:8000/api/analysis/MiCliente" \
-H "Content-Type: application/json" \
-d '{
    "conversation_id": "CONV123",
    "analysis_type": "sentiment",
    "result": {
        "sentiment": "positive",
        "score": 0.87,
        "topics": ["soporte", "pedido", "facturación"]
    },
    "metadata": {
        "model": "gpt-4",
        "processing_time": 1.45
    }
}'
```

Usando el endpoint unificado:
```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "generative-analysis",
    "parameters": {
        "clientName": "MiCliente",
        "conversationId": "CONV123",
        "analysisType": "intent",
        "result": {
            "primaryIntent": "resolver_problema",
            "confidence": 0.92
        }
    }
}'
```

### Obtener Análisis

```bash
curl -X GET "http://localhost:8000/api/analysis/MiCliente/CONV123"
```

Con filtro por tipo de análisis:
```bash
curl -X GET "http://localhost:8000/api/analysis/MiCliente/CONV123?analysis_type=sentiment"
```

### Actualizar un Análisis

```bash
curl -X PUT "http://localhost:8000/api/analysis/MiCliente/CONV123/sentiment" \
-H "Content-Type: application/json" \
-d '{
    "result": {
        "sentiment": "neutral",
        "score": 0.65
    }
}'
```

### Procesamiento por Lotes

Para analizar múltiples conversaciones a la vez:

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "batch-analysis",
    "parameters": {
        "clientName": "MiCliente",
        "conversationIds": ["CONV123", "CONV124", "CONV125"],
        "analysisType": "full",
        "options": {
            "priority": 2,
            "notifyOnComplete": true
        }
    }
}'
```

## Flujos de Trabajo Completos

### Ejemplo 1: Análisis Completo de una Nueva Conversación

```bash
# 1. Crear un cliente (si no existe)
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "create-smartvoc-client",
    "parameters": {
        "clientName": "ClienteDemo"
    }
}'

# 2. Crear una conversación
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "ClienteDemo",
        "conversation": [
            {"role": "user", "content": "Necesito ayuda para cambiar mi plan"},
            {"role": "assistant", "content": "Claro, ¿qué plan tiene actualmente?"},
            {"role": "user", "content": "Tengo el plan básico pero quiero el premium"}
        ]
    }
}'
# Guarda el conversationId devuelto: "CONV_XYZ"

# 3. Crear análisis de sentimiento
curl -X POST "http://localhost:8000/api/analysis/ClienteDemo" \
-H "Content-Type: application/json" \
-d '{
    "conversation_id": "CONV_XYZ",
    "analysis_type": "sentiment",
    "result": {
        "sentiment": "positive",
        "score": 0.75
    }
}'

# 4. Crear análisis de intención
curl -X POST "http://localhost:8000/api/analysis/ClienteDemo" \
-H "Content-Type: application/json" \
-d '{
    "conversation_id": "CONV_XYZ",
    "analysis_type": "intent",
    "result": {
        "intent": "upgrade_plan",
        "confidence": 0.92
    }
}'

# 5. Obtener todos los análisis
curl -X GET "http://localhost:8000/api/analysis/ClienteDemo/CONV_XYZ"
```

### Ejemplo 2: Procesamiento por Lotes y Monitoreo

```bash
# 1. Iniciar procesamiento por lotes
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "batch-analysis",
    "parameters": {
        "clientName": "ClienteDemo",
        "conversationIds": ["CONV1", "CONV2", "CONV3"],
        "analysisType": "full"
    }
}'
# Guarda el batchId devuelto: "BATCH_123"

# 2. Monitorear el progreso del lote
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "batch-status",
    "parameters": {
        "clientName": "ClienteDemo",
        "batchId": "BATCH_123"
    }
}'
```

## Paginación y Filtrado

Para manejar grandes volúmenes de datos, la API admite paginación y filtrado.

### Parámetros de Paginación

- `page`: Número de página (comienza en 1)
- `pageSize`: Cantidad de elementos por página (por defecto 10, máximo 100)

### Filtros Comunes

- `startDate` / `endDate`: Rango de fechas para filtrar
- `metadata.X`: Filtrar por campos específicos de metadatos
- `status`: Estado del elemento (completado, pendiente, etc.)

### Ejemplo de Uso

```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "ClienteDemo",
        "filters": {
            "startDate": "2025-01-01",
            "endDate": "2025-04-30",
            "metadata.channel": "web",
            "status": "completed"
        },
        "page": 2,
        "pageSize": 25,
        "sortBy": "createdAt",
        "sortDirection": "desc"
    }
}'
```

## Manejo de Errores

La API utiliza códigos de estado HTTP estándar y respuestas JSON consistentes para errores.

### Estructura de Respuesta de Error

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "El recurso solicitado no existe",
    "details": {...}
  }
}
```

### Códigos de Error Comunes

| Código HTTP | Significado                                     |
|-------------|------------------------------------------------|
| 400         | Solicitud incorrecta o validación fallida      |
| 404         | Recurso no encontrado                          |
| 409         | Conflicto (ej: recurso ya existe)              |
| 429         | Demasiadas solicitudes (rate limiting)         |
| 500         | Error interno del servidor                     |

### Tratamiento de Errores

- Siempre verifica el campo `success` en la respuesta
- Implementa reintentos con backoff exponencial para errores transitorios
- Considera el manejo de casos específicos según el código de error

## Mejores Prácticas

### Rendimiento
- Utiliza el procesamiento por lotes para operaciones masivas
- Filtra los datos en el servidor, no en el cliente
- Implementa caché para respuestas frecuentes

### Seguridad
- Protege tus credenciales de API
- Valida todos los datos de entrada
- Utiliza HTTPS para todas las comunicaciones

### Desarrollo
- Implementa pruebas automatizadas para tus integraciones
- Desarrolla con la versión de la API especificada
- Mantén registros detallados para resolución de problemas

## Solución de Problemas Comunes

### "No se puede conectar al servidor"
- Verifica que el servidor esté en ejecución
- Comprueba la configuración de red y firewall
- Asegúrate de que la URL sea correcta

### "Error de validación en los datos"
- Revisa el formato JSON de tu solicitud
- Verifica que todos los campos requeridos estén presentes
- Asegúrate de que los tipos de datos sean correctos

### "Cliente no encontrado"
- Verifica que el nombre del cliente exista exactamente como está escrito
- Comprueba si hay espacios o caracteres especiales en el nombre
- Utiliza el endpoint `get-all-smartvoc-clients` para listar clientes disponibles

### "Rendimiento lento en procesos por lotes"
- Reduce el tamaño de los lotes
- Aumenta la prioridad del proceso
- Verifica el tamaño de los datos de conversación

## Referencias

- [Documentación Completa de la API](/api/docs)
- [GitHub del Proyecto](https://github.com/SmartUp-Chile/backend-smartvoc)
- [Changelog](../CHANGELOG.md)
- [Roadmap](../ROADMAP.md)

---

Para cualquier problema o sugerencia, abre un issue en el [repositorio GitHub](https://github.com/SmartUp-Chile/backend-smartvoc/issues) o contacta al equipo de soporte en support@smartvoc.io. 