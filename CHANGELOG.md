# Registro de cambios (Changelog)

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Por implementar

- Optimización de la imagen Docker (Python 3.11/3.12)
- Estructura más modular con Blueprint de Flask
- Separación de modelos en archivos individuales
- Tests unitarios/integración
- Validación de datos de entrada (marshmallow/pydantic)
- Rate limiting para la API
- Configuración de CORS más restrictiva
- Herramientas de linting (flake8, black) y pre-commit hooks
- ~~CI/CD con GitHub Actions~~
- ~~Documentación con Swagger/OpenAPI~~
- Optimización de consultas a la base de datos
- Caché de resultados para endpoints frecuentes
- Sistema completo de autenticación y autorización
- Migración a PostgreSQL para producción
- Validación avanzada de datos de entrada

## [0.3.0] - En desarrollo

### Añadido

- Integración continua con GitHub Actions
- Documentación de la API con OpenAPI/Swagger
- Reestructuración de endpoints usando `flask-restx`
- Interfaz web para documentación en `/api/docs`
- Implementación de endpoint unificado para operaciones de SmartVOC
- Operaciones para listar clientes y crear clientes con tablas relacionadas
- Modelo para gestión de clientes SmartVOC
- CRUD completo para conversaciones de SmartVOC (GET, POST, PUT, DELETE)

### Cambiado

- Arquitectura del proyecto refactorizada para mejor escalabilidad
- Estructura de directorios reorganizada
- Mejora en el manejo de errores y excepciones

### Corregido

- Solución a problema de importación circular entre app.py y models.py
- Corrección del modelo RequestLog para incluir primary key y parámetros obligatorios
- Actualización de SmartVOCClient para usar db.Model en lugar de Base
- Mejora en el manejo de fechas en métodos to_dict() para objetos SQLAlchemy
- Gestión robusta de errores en las operaciones CRUD de conversaciones

## [0.2.0] - 2025-04-04

### Añadido
- Conexión a base de datos SQLite para desarrollo local
- Modelo RequestLog para registrar todas las solicitudes a la API
- Endpoint `/api/db-test` para verificar la conexión a la base de datos
- Creación automática de tablas al iniciar la aplicación
- Verificación de directorio `instance/` para SQLite

### Corregido
- Configuración de parámetros de pool para SQLite
- Compatibilidad con Mac M1/M2/M3 (puerto 8000 en lugar de 5000)

### Cambiado
- Actualizado Dockerfile para mejorar rendimiento
- Nuevo sistema de configuración basado en clases (development, testing, production)
- Reestructuración de la configuración de base de datos

## [0.1.0] - 2025-04-03

### Añadido
- Estructura inicial del proyecto
- Dockerización con Docker y Docker Compose
- Configuración de hot reload para desarrollo
- Endpoint `/api/health` para verificar el estado del servicio
- Configuración básica de Flask
- Estructura de carpetas para rutas y utilidades
- Persistencia de datos con volumen Docker
- Documentación inicial en README.md

### Seguridad
- Variables de entorno para configuración sensible
- Archivo `.env.example` para documentar variables sin exponer valores sensibles 