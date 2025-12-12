"""
Módulo común con utilidades reutilizables
Contiene servicios, excepciones, validators y helpers compartidos entre módulos
"""
from .validators import (
    normalize_documento,
    validate_dni_format,
    validate_dni_nie_nif,
    validate_dni_nie_nif_serializer,
    validate_dni_serializer,
    validate_nie_format,
    validate_nie_serializer,
    validate_nif_format,
    validate_nif_serializer,
)

__all__ = [
    'validate_dni_format',
    'validate_nie_format',
    'validate_nif_format',
    'validate_dni_nie_nif',
    'validate_dni_serializer',
    'validate_nie_serializer',
    'validate_nif_serializer',
    'validate_dni_nie_nif_serializer',
    'normalize_documento',
]
