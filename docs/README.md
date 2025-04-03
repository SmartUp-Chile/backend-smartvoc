# Backend SmartVoc

Este es un proyecto de backend utilizando Flask y Docker con capacidad de hot reload para desarrollo.

## Requisitos previos

- Docker
- Docker Compose

## Instalación

1. Clonar este repositorio
2. Navegar a la carpeta del proyecto
3. Copiar el archivo de configuración de ejemplo:
   ```bash
   cp .env.example .env
   ```
4. Editar el archivo `.env` con tus configuraciones

## Ejecución

Para iniciar el contenedor en local con hot reload, ejecutar:

```bash
docker-compose up --build
```

El servidor se iniciará en modo desarrollo y cualquier cambio en el código se recargará automáticamente.

Para ejecutar en segundo plano:

```bash
docker-compose up -d
```

Para detener los contenedores:

```bash
docker-compose down
```

## Estructura del proyecto

```
backend-smartvoc/
├── app/                  # Módulos de la aplicación
├── docs/                 # Documentación
├── instance/             # Datos persistentes (bases de datos)
├── routes/               # Definiciones de rutas
├── utils/                # Utilidades
├── .env                  # Variables de entorno (no incluido en git)
├── .env.example          # Ejemplo de variables de entorno
├── app.py                # Punto de entrada principal
├── Dockerfile            # Configuración de Docker
└── docker-compose.yml    # Configuración de Docker Compose
```

## Endpoints disponibles

- `GET /api/health`: Verificar el estado del servicio

## Pruebas

Para probar el endpoint de salud, ejecutar:

```bash
curl http://localhost:8000/api/health
```

O visitar en el navegador: http://localhost:8000/api/health

## Desarrollo

La configuración incluye hot reload, lo que significa que los cambios en el código se aplicarán automáticamente sin necesidad de reiniciar el contenedor. Esto facilita el desarrollo y la depuración.

## Notas para Mac con chip M1/M2/M3

En equipos Mac con Apple Silicon, el puerto 5000 suele estar ocupado por AirPlay. Por eso, la aplicación se expone en el puerto 8000 del host, aunque dentro del contenedor sigue usando el puerto 5000.

## Persistencia de datos

Los datos persistentes se almacenan en el volumen Docker `smartvoc_data`, que se monta en la carpeta `/app/instance` dentro del contenedor. Esto garantiza que los datos no se pierdan cuando el contenedor se detenga o se elimine. 