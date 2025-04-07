# Backend SmartVOC

Backend para el proyecto SmartVOC, implementado con Flask y SQLite.

## Descripción

Este proyecto implementa una API RESTful para el sistema SmartVOC de gestión de conversaciones, análisis de texto y generación de insights utilizando IA.

## Características principales

- Desarrollo en Python con Flask
- Base de datos SQLite para desarrollo
- Documentación de la API con Swagger/OpenAPI
- CI/CD con GitHub Actions
- Endpoints RESTful para operaciones CRUD

## Requisitos

- Python 3.8+
- Dependencias listadas en requirements.txt
- SQLite 3

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/SmartUp-Chile/backend-smartvoc.git
cd backend-smartvoc
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:

```bash
cp .env.example .env
# Editar .env con la configuración deseada
```

## Ejecución

Para ejecutar el servidor en modo desarrollo:

```bash
flask run
# o
python app.py
```

El servidor estará disponible en http://localhost:8000.

## Documentación de la API

La documentación interactiva de la API está disponible en http://localhost:8000/api/docs

## Estructura del proyecto

```
backend-smartvoc/
├── app.py              # Punto de entrada de la aplicación
├── api.py              # Configuración de la API con Swagger
├── resources/          # Controladores de recursos
│   ├── __init__.py
│   ├── health.py       # Endpoint de verificación de salud
│   ├── db.py           # Endpoint de pruebas de DB
│   └── smartvoc.py     # Endpoints de SmartVOC
├── models.py           # Modelos de datos
├── config.py           # Configuración de la aplicación
├── requirements.txt    # Dependencias del proyecto
└── .env                # Variables de entorno (no incluido en el repositorio)
```

## Configuración de la base de datos

La aplicación utiliza SQLite por defecto. La base de datos se creará automáticamente en la ruta especificada en la configuración.

```python
# Ejemplo de configuración en .env:
DATABASE_URI = "sqlite:///database.db"
```

## Endpoints disponibles

### Health Check

- `GET /api/health/`: Verifica el estado del servicio.

### Database Test

- `GET /api/db/test`: Prueba la conexión con la base de datos.

### SmartVOC

Todos los endpoints de SmartVOC utilizan el método POST a `/api/smartvoc` con el parámetro `operation`.

#### Operaciones de clientes

- `/get-all-smartvoc-clients`: Lista todos los clientes de SmartVOC registrados.
- `/create-smartvoc-client`: Crea un nuevo cliente SmartVOC con sus tablas relacionadas.

#### Operaciones de conversaciones

- `/smartvoc-conversations`: Gestiona las conversaciones (CRUD)
  - Método GET: Obtiene conversaciones según parámetros
  - Método POST: Crea una nueva conversación
  - Método PUT: Actualiza una conversación existente
  - Método DELETE: Elimina una conversación

> ⚠️ Nota: Los endpoints directos (GET /api/health, GET /api/db/test) serán removidos en futuras versiones, favoreciendo la estructura unificada.

## Ejemplos de uso

### Verificar salud del servicio

```bash
curl -X GET http://localhost:8000/api/health
```

### Obtener todos los clientes

```bash
curl -X POST http://localhost:8000/api/smartvoc \
  -H "Content-Type: application/json" \
  -d '{"operation": "get-all-smartvoc-clients"}'
```

### Crear un cliente

```bash
curl -X POST http://localhost:8000/api/smartvoc \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create-smartvoc-client",
    "parameters": {
      "clientName": "Cliente Ejemplo"
    }
  }'
```

### Obtener conversaciones de un cliente

```bash
curl -X POST http://localhost:8000/api/smartvoc \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "smartvoc-conversations",
    "method": "GET",
    "parameters": {
      "clientName": "Cliente Ejemplo",
      "clientId": 1
    }
  }'
```

### Crear una conversación

```bash
curl -X POST http://localhost:8000/api/smartvoc \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "smartvoc-conversations",
    "method": "POST",
    "parameters": {
      "clientName": "Cliente Ejemplo",
      "clientId": 1,
      "batchCustomName": "Lote de prueba",
      "conversation": [
        {
          "role": "user",
          "content": "Hola, tengo un problema con mi pedido"
        },
        {
          "role": "agent",
          "content": "Claro, con gusto le ayudo. ¿Podría proporcionarme el número de su pedido?"
        }
      ],
      "metadata": {
        "source": "chat",
        "channel": "web",
        "priority": "medium"
      }
    }
  }'
```

## Desarrollo

### Agregar nuevos modelos

1. Definir el modelo en `models.py`
2. Crear migraciones para actualizar la base de datos
3. Implementar los endpoints correspondientes en `resources/`

### Agregar nuevas rutas

1. Crear un nuevo archivo en `resources/` si es necesario
2. Implementar las clases de recursos usando flask-restx
3. Registrar los recursos en `api.py`

## Contribución

1. Hacer fork del repositorio
2. Crear una rama para la nueva funcionalidad
3. Realizar los cambios y pruebas
4. Enviar un Pull Request con una descripción clara de los cambios

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles. 