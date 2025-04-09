"""
Módulo de esquemas para validación de datos.

Este módulo contiene los esquemas de Marshmallow para la validación
de datos de entrada y salida de la API.
"""

from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field 