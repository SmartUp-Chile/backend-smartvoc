#!/usr/bin/env python
"""
Script para probar el manejo de errores de la API de SmartVOC.

Este script realiza solicitudes a varios endpoints para verificar que los errores
se manejan correctamente según la implementación del sistema de manejo de
errores global.
"""
import requests
import json
import sys
from termcolor import colored
import time

# URL base de la API
BASE_URL = "http://localhost:8000"

# Contador de resultados
results = {
    "success": 0,
    "fail": 0
}

def print_separator():
    """Imprime un separador para mejorar la legibilidad."""
    print("-" * 80)

def check_response(response, expected_status=None, expected_error_code=None):
    """
    Verifica que la respuesta tenga el formato y los códigos esperados.
    
    Args:
        response: Respuesta HTTP recibida
        expected_status: Código de estado HTTP esperado
        expected_error_code: Código de error específico esperado en la respuesta
        
    Returns:
        bool: True si la respuesta cumple con lo esperado, False en caso contrario
    """
    try:
        data = response.json()
    except ValueError:
        print(colored("ERROR: La respuesta no es JSON válido", "red"))
        return False
    
    success = True
    
    if expected_status and response.status_code != expected_status:
        print(colored(f"ERROR: Código de estado esperado {expected_status}, obtenido {response.status_code}", "red"))
        success = False
    
    if response.status_code >= 400:
        # Verificar estructura de error
        if "error" not in data:
            print(colored("ERROR: Respuesta de error sin campo 'error'", "red"))
            success = False
        
        if "message" not in data:
            print(colored("ERROR: Respuesta de error sin campo 'message'", "red"))
            success = False
            
        if "status_code" not in data:
            print(colored("ERROR: Respuesta de error sin campo 'status_code'", "red"))
            success = False
        
        if expected_error_code and data.get("error") != expected_error_code:
            print(colored(f"ERROR: Código de error esperado '{expected_error_code}', obtenido '{data.get('error')}'", "red"))
            success = False
    
    return success

def test_endpoint(description, method, endpoint, data=None, params=None, 
                 expected_status=200, expected_error_code=None):
    """
    Realiza una prueba a un endpoint específico.
    
    Args:
        description: Descripción de la prueba
        method: Método HTTP (GET, POST, PUT, DELETE)
        endpoint: Ruta del endpoint a probar
        data: Datos a enviar en la solicitud (para POST/PUT)
        params: Parámetros de consulta (para GET)
        expected_status: Código de estado HTTP esperado
        expected_error_code: Código de error específico esperado
    """
    print_separator()
    print(colored(f"PRUEBA: {description}", "cyan"))
    print(f"Método: {method}")
    print(f"Endpoint: {endpoint}")
    
    if data:
        print(f"Datos: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if params:
        print(f"Parámetros: {params}")
        
    print(f"Estado esperado: {expected_status}")
    
    if expected_error_code:
        print(f"Código de error esperado: {expected_error_code}")
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url, params=params)
        else:
            print(colored(f"ERROR: Método HTTP no soportado: {method}", "red"))
            results["fail"] += 1
            return
        
        print(f"Estado obtenido: {response.status_code}")
        print(f"Respuesta: {json.dumps(response.json(), indent=2, ensure_ascii=False) if response.content else 'Sin contenido'}")
        
        if check_response(response, expected_status, expected_error_code):
            print(colored("RESULTADO: ✓ OK", "green"))
            results["success"] += 1
        else:
            print(colored("RESULTADO: ✗ ERROR", "red"))
            results["fail"] += 1
            
    except Exception as e:
        print(colored(f"ERROR EN LA PRUEBA: {str(e)}", "red"))
        results["fail"] += 1

# -------------------------------------------------------------------------
# PRUEBAS
# -------------------------------------------------------------------------

# 1. PRUEBAS DE RUTAS Y MÉTODOS
# -------------------------------------------------------------------------

# Prueba 1: Obtener estado de salud (caso exitoso)
test_endpoint(
    description="Verificar estado de salud (caso exitoso)",
    method="GET",
    endpoint="/api/health",
    expected_status=200
)

# Prueba 2: Ruta no existente
test_endpoint(
    description="Ruta no existente (error 404)",
    method="GET",
    endpoint="/api/ruta_que_no_existe",
    expected_status=404,
    expected_error_code="not_found"
)

# Prueba 3: Método no permitido
test_endpoint(
    description="Método no permitido (error 405)",
    method="DELETE",
    endpoint="/api/health",
    expected_status=405,
    expected_error_code="method_not_allowed"
)

# 2. PRUEBAS DE VALIDACIÓN
# -------------------------------------------------------------------------

# Prueba 4: Crear cliente sin datos requeridos
test_endpoint(
    description="Crear cliente sin datos requeridos (error de validación)",
    method="POST",
    endpoint="/api/smartvoc/clients",
    data={},
    expected_status=400,
    expected_error_code="validation_error"
)

# Prueba 5: Crear cliente con datos incorrectos
test_endpoint(
    description="Crear cliente con datos incorrectos (error de validación)",
    method="POST",
    endpoint="/api/smartvoc/clients",
    data={
        "clientName": "",  # Nombre vacío (no permitido)
        "clientWebsite": "no es una url válida"
    },
    expected_status=400,
    expected_error_code="validation_error"
)

# 3. PRUEBAS DE RECURSOS
# -------------------------------------------------------------------------

# Prueba 6: Obtener cliente inexistente
test_endpoint(
    description="Obtener cliente inexistente (error 404)",
    method="GET",
    endpoint="/api/smartvoc/clients/cliente_que_no_existe",
    expected_status=404,
    expected_error_code="not_found"
)

# Prueba 7: Actualizar cliente inexistente
test_endpoint(
    description="Actualizar cliente inexistente (error 404)",
    method="PUT",
    endpoint="/api/smartvoc/clients/cliente_que_no_existe",
    data={"clientName": "Nuevo nombre"},
    expected_status=404,
    expected_error_code="not_found"
)

# Prueba 8: Eliminar cliente inexistente
test_endpoint(
    description="Eliminar cliente inexistente (error 404)",
    method="DELETE",
    endpoint="/api/smartvoc/clients/cliente_que_no_existe",
    expected_status=404,
    expected_error_code="not_found"
)

# 4. PRUEBAS DE VALIDACIÓN DE PARÁMETROS
# -------------------------------------------------------------------------

# Prueba 9: Obtener conversación sin parámetros requeridos
test_endpoint(
    description="Obtener conversación sin parámetros requeridos",
    method="GET",
    endpoint="/api/smartvoc/conversations/conv-123",
    expected_status=400,
    expected_error_code="validation_error"
)

# 5. PRUEBAS DE CREACIÓN DE RECURSOS (ÉXITO)
# -------------------------------------------------------------------------

# Prueba 10: Crear cliente (éxito)
test_endpoint(
    description="Crear cliente (éxito)",
    method="POST",
    endpoint="/api/smartvoc/clients",
    data={
        "clientName": f"Cliente de Prueba {int(time.time())}",  # Nombre único usando timestamp
        "clientWebsite": "https://ejemplo.com",
        "clientDescription": "Cliente creado para pruebas"
    },
    expected_status=201
)

# 6. PRUEBAS DE CONFLICTOS
# -------------------------------------------------------------------------

# Prueba 11: Crear cliente duplicado
test_endpoint(
    description="Crear cliente duplicado (error de conflicto)",
    method="POST",
    endpoint="/api/smartvoc/clients",
    data={
        "clientName": "Cliente de Prueba",  # Mismo nombre que en prueba anterior
        "clientWebsite": "https://ejemplo.com"
    },
    expected_status=409,
    expected_error_code="resource_exists"
)

# Presentar resultados
print_separator()
print(colored("RESUMEN DE RESULTADOS", "cyan"))
print(f"Pruebas exitosas: {results['success']}")
print(f"Pruebas fallidas: {results['fail']}")
print(f"Total de pruebas: {results['success'] + results['fail']}")

# Salir con código de error si hubo fallos
if results["fail"] > 0:
    sys.exit(1) 