#!/usr/bin/env python
"""
Script para probar el manejo de errores de base de datos de la API de SmartVOC.

Este script provoca deliberadamente errores de base de datos y verifica
que se manejen correctamente según la implementación del sistema de manejo
de errores global.
"""
import requests
import json
import sys
from termcolor import colored
import sqlite3
import os
import time

# URL base de la API
BASE_URL = "http://localhost:8000"

# Path a la base de datos SQLite
DB_PATH = "smartvoc.db"

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

def create_backup():
    """Crea una copia de seguridad de la base de datos."""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'rb') as src, open(f"{DB_PATH}.bak", 'wb') as dst:
            dst.write(src.read())
        return True
    return False

def restore_backup():
    """Restaura la copia de seguridad de la base de datos."""
    if os.path.exists(f"{DB_PATH}.bak"):
        with open(f"{DB_PATH}.bak", 'rb') as src, open(DB_PATH, 'wb') as dst:
            dst.write(src.read())
        os.remove(f"{DB_PATH}.bak")
        return True
    return False

def corrupt_table(table_name):
    """
    Corrompe deliberadamente una tabla para provocar errores.
    
    Args:
        table_name: Nombre de la tabla a corromper
        
    Returns:
        bool: True si se pudo corromper la tabla, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Renombrar la tabla para simular que no existe
        cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_corrupted")
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(colored(f"No se pudo corromper la tabla: {str(e)}", "red"))
        return False

def restore_table(table_name):
    """
    Restaura una tabla corrupta.
    
    Args:
        table_name: Nombre de la tabla a restaurar
        
    Returns:
        bool: True si se pudo restaurar la tabla, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Renombrar la tabla de nuevo a su nombre original
        cursor.execute(f"ALTER TABLE {table_name}_corrupted RENAME TO {table_name}")
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(colored(f"No se pudo restaurar la tabla: {str(e)}", "red"))
        return False

# -------------------------------------------------------------------------
# PRUEBAS
# -------------------------------------------------------------------------

# Hacer backup de la base de datos
print_separator()
print(colored("Creando copia de seguridad de la base de datos...", "cyan"))
if create_backup():
    print(colored("Copia de seguridad creada exitosamente", "green"))
else:
    print(colored("No se pudo crear copia de seguridad", "red"))
    sys.exit(1)

try:
    # 1. PRUEBAS DE ERRORES DE BASE DE DATOS
    # -------------------------------------------------------------------------
    
    # Corromper tabla de clientes
    print_separator()
    print(colored("Corrompiendo tabla de clientes...", "cyan"))
    if corrupt_table("smartvoc_clients"):
        print(colored("Tabla corrompida exitosamente", "green"))
    else:
        print(colored("No se pudo corromper la tabla", "red"))
        restore_backup()
        sys.exit(1)
    
    # Prueba 1: Intentar obtener clientes con tabla corrompida
    test_endpoint(
        description="Obtener clientes con tabla corrompida",
        method="GET",
        endpoint="/api/smartvoc/clients",
        expected_status=500,
        expected_error_code="database_error"
    )
    
    # Restaurar tabla de clientes
    print_separator()
    print(colored("Restaurando tabla de clientes...", "cyan"))
    if restore_table("smartvoc_clients"):
        print(colored("Tabla restaurada exitosamente", "green"))
    else:
        print(colored("No se pudo restaurar la tabla", "red"))
        restore_backup()
        sys.exit(1)
    
    # Prueba 2: Crear cliente con nombre duplicado
    test_endpoint(
        description="Crear cliente (para prueba de duplicado)",
        method="POST",
        endpoint="/api/smartvoc/clients",
        data={
            "clientName": f"Cliente Test DB {int(time.time())}",
            "clientWebsite": "https://ejemplo.com"
        },
        expected_status=201
    )
    
    # Crear una copia del nombre para la prueba de duplicación
    client_test_name = f"Cliente Test DB Duplicado {int(time.time())}"

    # Crear el primer cliente
    test_endpoint(
        description="Crear cliente para prueba duplicado (primero)",
        method="POST",
        endpoint="/api/smartvoc/clients",
        data={
            "clientName": client_test_name,
            "clientWebsite": "https://ejemplo.com"
        },
        expected_status=201
    )

    # Prueba 3: Crear cliente con nombre duplicado para forzar error de integridad
    test_endpoint(
        description="Crear cliente con nombre duplicado (error de integridad)",
        method="POST",
        endpoint="/api/smartvoc/clients",
        data={
            "clientName": client_test_name,  # Mismo nombre que el anterior
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
    
except Exception as e:
    print(colored(f"ERROR DURANTE LAS PRUEBAS: {str(e)}", "red"))
finally:
    # Restaurar backup de la base de datos
    print_separator()
    print(colored("Restaurando copia de seguridad de la base de datos...", "cyan"))
    if restore_backup():
        print(colored("Base de datos restaurada exitosamente", "green"))
    else:
        print(colored("ERROR: No se pudo restaurar la base de datos!", "red"))

# Salir con código de error si hubo fallos
if results["fail"] > 0:
    sys.exit(1) 