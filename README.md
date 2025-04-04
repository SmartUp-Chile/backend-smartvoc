# Backend SmartVOC

Backend para SmartVOC desarrollado con Flask y SQLAlchemy, configurado con Docker para facilitar el desarrollo y despliegue.

## Características principales

- API REST con Flask
- Soporte para SQLite (desarrollo) y SQL Server (producción)
- Hot reload para desarrollo
- Dockerizado para fácil despliegue
- Configuración para conexión a Azure SQL
- Registro automático de solicitudes
- Documentación interactiva de la API con Swagger/OpenAPI
- CI/CD con GitHub Actions

## Requisitos previos

- Docker
- Docker Compose

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/SmartUp-Chile/backend-smartvoc.git
cd backend-smartvoc
```

2. Crear archivo de variables de entorno:
```bash
cp .env.example .env
```

3. Modificar el archivo `.env` según sea necesario.

## Ejecución

### Desarrollo local

Para iniciar el contenedor en modo desarrollo con hot reload:

```bash
docker-compose up --build
```

El servidor estará disponible en:
- [http://localhost:8000/api/health](http://localhost:8000/api/health)

Para ejecutar en segundo plano:

```bash
docker-compose up -d
```

Para detener el contenedor:

```bash
docker-compose down
```

### Producción

Para producción, modifica las variables de entorno y usa:

```bash
FLASK_ENV=production docker-compose up -d
```

## Estructura del proyecto

```
backend-smartvoc/
├── app.py                # Punto de entrada principal
├── config.py             # Configuración de la aplicación
├── models.py             # Modelos de base de datos
├── requirements.txt      # Dependencias
├── Dockerfile            # Configuración de Docker
├── docker-compose.yml    # Configuración de Docker Compose
├── .env                  # Variables de entorno (no incluido en git)
├── .env.example          # Ejemplo de variables de entorno
├── instance/             # Datos persistentes (SQLite)
├── docs/                 # Documentación
└── routes/               # Definiciones de rutas API
```

## Endpoints disponibles

La API está documentada con Swagger/OpenAPI. Puedes acceder a la documentación interactiva en:

```
http://localhost:8000/api/docs
```

### Principales endpoints

- **Health Check**:
  - `GET /api/health/` - Verifica el estado del servicio

- **Base de datos**:
  - `GET /api/db/test` - Verifica la conexión a la base de datos

> Nota: Los endpoints anteriores `/api/health` y `/api/db-test` están mantenidos por compatibilidad, pero serán eliminados en versiones futuras.

## Base de datos

El proyecto está configurado para usar:

- **SQLite** para desarrollo local
- **SQL Server** para producción

La configuración de la base de datos está en `config.py` y las variables de conexión en `docker-compose.yml` o el archivo `.env`.

## Desarrollo

### Hot Reload

Los cambios en el código se detectan automáticamente y el servidor se reinicia gracias a la configuración de watchdog.

### Agregar nuevos modelos

Para agregar nuevos modelos, definirlos en `models.py` siguiendo la estructura de SQLAlchemy:

```python
class NuevoModelo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Más campos...
```

### Agregar nuevas rutas

Las rutas se pueden definir directamente en `app.py` para endpoints simples o en módulos separados en la carpeta `routes/`.

## Notas para Mac con chip M1/M2/M3

En equipos Mac con Apple Silicon:
- El puerto 5000 suele estar ocupado por AirPlay, por lo que la aplicación se expone en el puerto 8000
- La imagen Docker está configurada para funcionar en arquitectura ARM64

## Solución de problemas

### Base de datos

Si encuentras problemas con la conexión a la base de datos:

1. Verifica que el directorio `instance/` exista y tenga permisos adecuados
2. Prueba la conexión con el endpoint `/api/db-test`
3. Revisa los logs del contenedor:
```bash
docker logs smartvoc-api
```

## Contribución

1. Haz un fork del proyecto
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request 