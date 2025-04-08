# Backend SmartVOC

Backend para el proyecto SmartVOC, implementado con Flask y SQLite.

## Descripción

Este proyecto implementa una API RESTful para el sistema SmartVOC de gestión de conversaciones, análisis de texto y generación de insights utilizando IA.

## Estructura del Proyecto

```
backend-smartvoc/
├── app.py              # Aplicación principal Flask
├── api.py              # Configuración de Swagger/OpenAPI
├── config.py           # Configuración de la aplicación
├── models.py           # Modelos de datos SQLAlchemy
├── resources/          # Recursos de la API
│   ├── __init__.py
│   ├── health.py      # Endpoint de salud
│   ├── db_test.py     # Prueba de conexión a BD
│   └── smartvoc.py    # Endpoints de SmartVOC
├── routes/            # Rutas adicionales
│   └── smartvoc_routes.py
├── instance/          # Datos de la aplicación
├── docs/             # Documentación
└── tests/            # Pruebas unitarias
```

## API Endpoints

### SmartVOC

Todos los endpoints de SmartVOC utilizan el método POST a `/api/smartvoc` con el parámetro `operation`.

#### Operaciones Disponibles

1. **Gestión de Clientes**
   - `get-all-smartvoc-clients`: Lista todos los clientes registrados
   - `create-smartvoc-client`: Crea un nuevo cliente con sus tablas relacionadas

2. **Gestión de Conversaciones**
   - `smartvoc-conversations`: Operaciones CRUD para conversaciones
     - GET: Obtener conversaciones con filtros opcionales
     - POST: Crear nueva conversación
     - PUT: Actualizar conversación existente
     - DELETE: Eliminar conversación

3. **Detalles del Cliente**
   - `client-details`: Gestión de información detallada del cliente
     - GET: Obtener detalles
     - POST: Crear detalles
     - PUT: Actualizar detalles

4. **Grupos de Campos**
   - `field-groups`: Gestión de campos y categorías
     - GET: Obtener grupos
     - POST: Crear grupo
     - PUT: Actualizar grupo

5. **Análisis Generativo**
   - `generative-analysis`: Gestión de análisis generativos
     - GET: Obtener análisis con filtros
     - POST: Crear nuevo análisis
     - PUT: Actualizar análisis existente

#### Ejemplos de Uso

1. **Listar Clientes**
```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{"operation": "get-all-smartvoc-clients"}'
```

2. **Crear Cliente**
```bash
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "create-smartvoc-client",
    "parameters": {
        "clientName": "ClienteEjemplo"
    }
}'
```

3. **Gestionar Conversaciones**
```bash
# Obtener conversaciones
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "ClienteEjemplo",
        "conversationId": "123"
    }
}'

# Crear conversación
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "smartvoc-conversations",
    "parameters": {
        "clientName": "ClienteEjemplo",
        "conversation": [...],
        "metadata": {...}
    }
}'
```

4. **Análisis Generativo**
```bash
# Obtener análisis
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "generative-analysis",
    "parameters": {
        "clientName": "ClienteEjemplo",
        "conversationId": "123"
    }
}'

# Crear análisis
curl -X POST http://localhost:8000/api/smartvoc \
-H "Content-Type: application/json" \
-d '{
    "operation": "generative-analysis",
    "parameters": {
        "clientName": "ClienteEjemplo",
        "conversationId": "123",
        "deepAnalysis": {...},
        "gscAnalysis": {...}
    }
}'
```

## Modelos de Datos

### SmartVOCClient
- `clientId`: Identificador único del cliente
- `clientName`: Nombre del cliente
- `clientSlug`: Identificador URL-friendly
- `createdAt`: Fecha de creación

### ClientDetails
- Información detallada del cliente
- Configuraciones específicas
- Metadatos del cliente

### FieldGroup
- Grupos de campos personalizados
- Categorías y campos generados
- Configuraciones de análisis

### GenerativeAnalysis
- Análisis profundo de conversaciones
- Análisis GSC
- Metadatos de procesamiento

### SmartVOCConversation
- Contenido de la conversación
- Metadatos
- Estados de análisis
- IDs de lotes de procesamiento

## Características Principales

1. **Gestión Multi-cliente**
   - Creación dinámica de tablas por cliente
   - Aislamiento de datos
   - Configuraciones personalizadas

2. **Procesamiento de Conversaciones**
   - Almacenamiento estructurado
   - Metadatos enriquecidos
   - Estados de procesamiento

3. **Análisis Generativo**
   - Análisis profundo
   - Análisis GSC
   - Procesamiento por lotes

4. **Seguridad y Validación**
   - Validación de parámetros
   - Manejo de errores
   - Reintentos automáticos

5. **Persistencia de Datos**
   - Almacenamiento en SQLite
   - Tablas dinámicas por cliente
   - Relaciones y constraints

## Configuración

### Variables de Entorno
```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///instance/smartvoc.db
```

### Base de Datos
- SQLite por defecto
- Soporte para otros motores SQL
- Migraciones automáticas

## Desarrollo

### Requisitos
- Python 3.8+
- Flask
- SQLAlchemy
- Flask-RESTX

### Instalación
```bash
# Clonar el repositorio
git clone https://github.com/SmartUp-Chile/backend-smartvoc.git
cd backend-smartvoc

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar el servidor
flask run
```

### Docker
```bash
# Construir la imagen
docker build -t smartvoc-api .

# Ejecutar el contenedor
docker run -p 8000:5000 --env-file .env smartvoc-api
```

## Pruebas

### Ejecutar Pruebas
```bash
# Pruebas unitarias
python -m pytest tests/

# Pruebas con cobertura
python -m pytest --cov=app tests/
```

## Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto

SmartUp Chile - [@SmartUpChile](https://twitter.com/SmartUpChile)

Link del Proyecto: [https://github.com/SmartUp-Chile/backend-smartvoc](https://github.com/SmartUp-Chile/backend-smartvoc) 