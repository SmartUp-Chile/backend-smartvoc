# Registro de cambios
Todos los cambios notables en este proyecto serán documentados en este archivo.

## [Unreleased]

### Añadido
- Nueva estructura modular para la aplicación con separación clara de responsabilidades
- Implementación de endpoints para análisis de conversaciones:
  - `GET /api/analysis/<client_name>/<conversation_id>`: Obtener análisis de una conversación
  - `POST /api/analysis/<client_name>`: Crear un nuevo análisis
  - `PUT /api/analysis/<client_name>/<conversation_id>/<analysis_type>`: Actualizar un análisis existente
  - `DELETE /api/analysis/<client_name>/<conversation_id>/<analysis_type>`: Eliminar un análisis
- Integración con Flask Blueprint para rutas de análisis más estructuradas
- Conversión automática entre objetos Python y cadenas JSON para compatibilidad con SQLite
- Creación dinámica de tablas específicas por cliente para análisis
- Manejo mejorado de transacciones en las operaciones de base de datos
- Nuevo servicio `AnalysisService` con métodos completos para CRUD de análisis
- Sistema de logging detallado para seguimiento de operaciones y depuración
- Implementación de análisis generativo de conversaciones:
  - Modelo `GenerativeAnalysis` para almacenar resultados de análisis con campos JSON
  - Soporte para diferentes tipos de análisis: estándar, sentimiento, intención, entidades
  - Procesamiento por lotes para análisis múltiples con seguimiento de estado
  - API para creación, recuperación y actualización de análisis generativos
  - Validación de esquemas para datos de entrada de análisis
  - Creación automática de tablas específicas por cliente
  - Métodos completos para análisis generativo:
    - `get_generative_analyses`: Consulta de análisis por ID de conversación, ID de lote o tipo
    - `create_generative_analysis`: Creación de análisis con soporte para campos JSON
    - `update_generative_analysis`: Actualización flexible de análisis existentes
  - Procesamiento eficiente de lotes de análisis con priorización 
  - Manejo inteligente de conversión JSON para compatibilidad con diferentes bases de datos
  - Sistema de monitoreo y seguimiento del estado de procesamiento

### Modificado
- Refactorización de la estructura del proyecto para minimizar importaciones circulares
- Simplificación de la estructura de la API utilizando Flask directamente
- Mejora en la gestión de errores y validación de datos de entrada
- Manejo optimizado de transacciones SQLAlchemy en operaciones CRUD
- Patrones mejorados para evitar bloqueos en la base de datos
- Actualización de dependencias y librerías:
  - SQLAlchemy text() para consultas dinámicas seguras
  - UUID para generación de identificadores únicos
  - Manejo mejorado de fechas con timedelta
- Refactorización de métodos principales (GET, POST, PUT) para:
  - Mejorar la organización del código
  - Separar operaciones lógicas por tipo
  - Estandarizar manejo de parámetros y respuestas
  - Optimizar el rendimiento en procesamiento de solicitudes
  - Mejorar el manejo de errores con mensajes descriptivos

### Corregido
- Solución a error en f-string con llaves vacías en la definición de tablas SQL
- Corrección del manejo de objetos JSON en SQLite mediante serialización explícita
- Prevención de errores "transaction in progress" en operaciones de base de datos
- Manejo adecuado de resultados de consultas con .scalar() en lugar de .fetchone().count
- Verificación mejorada de la existencia de registros antes de actualizar o eliminar

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