# Registro de cambios (Changelog)

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Por implementar

- Optimización de la imagen Docker (Python 3.11/3.12)
- Estructura más modular con Blueprint de Flask
- Separación de modelos en archivos individuales
- Tests unitarios/integración
- ~~Validación de datos de entrada (marshmallow/pydantic)~~
- Rate limiting para la API
- Configuración de CORS más restrictiva
- Herramientas de linting (flake8, black) y pre-commit hooks
- ~~CI/CD con GitHub Actions~~
- ~~Documentación con Swagger/OpenAPI~~
- Optimización de consultas a la base de datos
- Caché de resultados para endpoints frecuentes
- Sistema completo de autenticación y autorización
- Migración a PostgreSQL para producción
- ~~Validación avanzada de datos de entrada~~
- ~~Manejo global de errores y excepciones~~

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
- Sistema centralizado de manejo de errores con jerarquía de excepciones personalizadas
- Mapeo inteligente de excepciones SQLAlchemy a errores de API estandarizados
- Logging detallado para facilitar debugging de errores
- Formato estandarizado para todas las respuestas de error en la API
- Middleware para capturar todas las excepciones no manejadas

### Cambiado

- Arquitectura del proyecto refactorizada para mejor escalabilidad
- Estructura de directorios reorganizada
- Mejora en el manejo de errores y excepciones
- Refactorización de validadores para integrarse con el nuevo sistema de excepciones
- Código más limpio en controladores al usar excepciones en lugar de retornar errores manualmente

### Corregido

- Solución a problema de importación circular entre app.py y models.py
- Corrección del modelo RequestLog para incluir primary key y parámetros obligatorios
- Actualización de SmartVOCClient para usar db.Model en lugar de Base
- Mejora en el manejo de fechas en métodos to_dict() para objetos SQLAlchemy
- Gestión robusta de errores en las operaciones CRUD de conversaciones
- Mejor gestión y reporting de errores de base de datos

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

## [Unreleased]

### Añadido
- Nueva estructura modular para la aplicación con separación clara de responsabilidades
- Implementación de endpoints para análisis de conversaciones:
  - `GET /api/analysis/<client_name>/<conversation_id>`: Obtener análisis de una conversación
  - `POST /api/analysis/<client_name>/<conversation_id>`: Crear un nuevo análisis
  - `PUT /api/analysis/<client_name>/<conversation_id>`: Actualizar un análisis existente
  - `DELETE /api/analysis/<client_name>/<conversation_id>`: Eliminar un análisis
  - `GET /api/analysis/<client_name>`: Listar análisis con filtrado
- Implementación de endpoints para procesamiento por lotes:
  - `POST /api/batch-analysis/<client_name>`: Iniciar un análisis por lotes
  - `GET /api/batch-analysis/<batch_id>/status`: Obtener estado de un proceso por lotes
  - `GET /api/batch-analysis`: Listar todos los procesos por lotes
- Nuevos servicios en estructura modular:
  - `AnalysisService`: Gestión de análisis de conversaciones en la base de datos
  - `OpenAIService`: Integración con Azure OpenAI para análisis de texto
  - `ConversationController`: Coordinación del proceso de análisis
- Implementación completa de rutas para conversaciones de SmartVOC:
  - `PUT /api/smartvoc/conversations/<conversation_id>`: Actualizar una conversación
  - `DELETE /api/smartvoc/conversations/<conversation_id>`: Eliminar una conversación
- Sistema de validación de datos basado en Marshmallow:
  - Esquemas para validación de clientes, conversaciones y análisis
  - Decoradores para validar automáticamente rutas y parámetros
  - Mensajes de error personalizados y estandarizados
  - Validación de tipos, longitudes y reglas de negocio
- Sistema centralizado de manejo de errores:
  - Jerarquía de excepciones personalizadas para diferentes tipos de errores
  - Manejadores globales para capturar y transformar excepciones
  - Formato consistente de respuestas de error en toda la API
  - Logging detallado para facilitar debugging

### Modificado
- Refactorización completa de la aplicación para resolver problemas de importación circular
- Simplificación de la estructura de la API utilizando Flask directamente
- Mejora en la gestión de errores y logging
- Implementación del modelo con datos separado de la lógica de negocio
- Reorganización de middlewares para mejor rendimiento
- Refactorización del patrón de diseño para todas las rutas de la API:
  - Separación estricta entre rutas y lógica de negocio
  - Rutas convertidas en simples delegadores hacia servicios
  - Responsabilidad del código de estado HTTP trasladada a los servicios
  - Eliminación de condicionales y lógica de negocio en rutas
  - Normalización de la estructura de respuestas en todas las rutas
- Implementación de validación de datos en la capa de rutas:
  - Las rutas ahora validan automáticamente los datos de entrada
  - Manejo consistente de errores de validación
  - Respuestas estandarizadas para errores de usuario
- Sistema de excepciones personalizadas integrado con SQLAlchemy:
  - Mapeo inteligente de errores de SQLAlchemy a excepciones de API
  - Mejor experiencia de usuario al recibir errores de base de datos
  - Ocultamiento de detalles técnicos en entornos de producción

### Corregido
- Solucionado el problema con RequestLog y la falta de una clave primaria
- Corregidos los problemas de importación circular entre módulos
- Mejorado el manejo de errores en las operaciones de base de datos 