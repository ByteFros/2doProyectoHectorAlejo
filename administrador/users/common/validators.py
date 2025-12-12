"""
Validadores comunes para DNI/NIF español y otros documentos de identidad
"""
import re

from rest_framework import serializers

# ============================================================================
# CONSTANTES
# ============================================================================

DNI_REGEX = re.compile(r'^[0-9]{8}[A-Z]$')
NIE_REGEX = re.compile(r'^[XYZ][0-9]{7}[A-Z]$')
NIF_REGEX = re.compile(r'^[A-Z][0-9]{7}[A-Z0-9]$')

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
NIE_REPLACE = {'X': '0', 'Y': '1', 'Z': '2'}


# ============================================================================
# VALIDADORES DE FORMATO
# ============================================================================

def validate_dni_format(dni: str) -> tuple[bool, str]:
    """
    Valida el formato y letra de control de un DNI español.

    Args:
        dni: DNI a validar (formato: 12345678A)

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> validate_dni_format("12345678Z")
        (True, "")
        >>> validate_dni_format("12345678X")
        (False, "La letra del DNI no es correcta")
        >>> validate_dni_format("1234567A")
        (False, "El formato del DNI no es válido. Debe ser 8 dígitos y una letra")
    """
    if not dni:
        return False, "El DNI no puede estar vacío"

    dni = dni.upper().strip()

    # Validar formato básico
    if not DNI_REGEX.match(dni):
        return False, "El formato del DNI no es válido. Debe ser 8 dígitos y una letra"

    # Extraer número y letra
    numero = dni[:8]
    letra = dni[8]

    # Calcular letra correcta
    letra_calculada = DNI_LETTERS[int(numero) % 23]

    if letra != letra_calculada:
        return False, f"La letra del DNI no es correcta. Debería ser {letra_calculada}"

    return True, ""


def validate_nie_format(nie: str) -> tuple[bool, str]:
    """
    Valida el formato y letra de control de un NIE español.

    Args:
        nie: NIE a validar (formato: X1234567A)

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> validate_nie_format("X1234567L")
        (True, "")
        >>> validate_nie_format("X1234567X")
        (False, "La letra del NIE no es correcta")
        >>> validate_nie_format("A1234567L")
        (False, "El formato del NIE no es válido")
    """
    if not nie:
        return False, "El NIE no puede estar vacío"

    nie = nie.upper().strip()

    # Validar formato básico
    if not NIE_REGEX.match(nie):
        return False, "El formato del NIE no es válido. Debe comenzar con X, Y o Z seguido de 7 dígitos y una letra"

    # Reemplazar primera letra por número
    primera_letra = nie[0]
    numero = NIE_REPLACE[primera_letra] + nie[1:8]
    letra = nie[8]

    # Calcular letra correcta
    letra_calculada = DNI_LETTERS[int(numero) % 23]

    if letra != letra_calculada:
        return False, f"La letra del NIE no es correcta. Debería ser {letra_calculada}"

    return True, ""


def validate_nif_format(nif: str) -> tuple[bool, str]:
    """
    Valida el formato de un NIF empresarial español.

    Tipos de NIF válidos:
    - CIF: A-H, J-N, P-S, U-W + 7 dígitos + letra/dígito

    Args:
        nif: NIF a validar (formato: B12345678)

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> validate_nif_format("B12345678")
        (True, "")
        >>> validate_nif_format("12345678")
        (False, "El formato del NIF no es válido")
    """
    if not nif:
        return False, "El NIF no puede estar vacío"

    nif = nif.upper().strip()

    # Validar formato básico
    if not NIF_REGEX.match(nif):
        return False, "El formato del NIF no es válido. Debe comenzar con una letra seguida de 7 dígitos y un carácter"

    primera_letra = nif[0]

    # Letras válidas para NIF empresarial
    letras_validas = "ABCDEFGHJNPQRSUVW"

    if primera_letra not in letras_validas:
        return False, f"La primera letra del NIF no es válida. Debe ser una de: {letras_validas}"

    return True, ""


def validate_dni_nie_nif(documento: str) -> tuple[bool, str]:
    """
    Valida un documento que puede ser DNI, NIE o NIF.
    Intenta validar en ese orden.

    Args:
        documento: Documento a validar

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> validate_dni_nie_nif("12345678Z")
        (True, "")
        >>> validate_dni_nie_nif("X1234567L")
        (True, "")
        >>> validate_dni_nie_nif("B12345678")
        (True, "")
        >>> validate_dni_nie_nif("INVALID")
        (False, "Formato de documento no válido")
    """
    if not documento:
        return False, "El documento no puede estar vacío"

    documento = documento.upper().strip()

    # Intentar validar como DNI
    if DNI_REGEX.match(documento):
        return validate_dni_format(documento)

    # Intentar validar como NIE
    if NIE_REGEX.match(documento):
        return validate_nie_format(documento)

    # Intentar validar como NIF
    if NIF_REGEX.match(documento):
        return validate_nif_format(documento)

    return False, "Formato de documento no válido. Debe ser un DNI (8 dígitos + letra), NIE (X/Y/Z + 7 dígitos + letra) o NIF (letra + 7 dígitos + carácter)"


# ============================================================================
# SERIALIZER FIELD VALIDATORS
# ============================================================================

def validate_dni_serializer(value: str) -> str:
    """
    Validador para usar en serializers de Django REST Framework (DNI).

    Args:
        value: DNI a validar

    Returns:
        DNI en mayúsculas y sin espacios

    Raises:
        serializers.ValidationError: Si el DNI no es válido

    Example:
        class EmpleadoSerializer(serializers.Serializer):
            dni = serializers.CharField(validators=[validate_dni_serializer])
    """
    is_valid, error_msg = validate_dni_format(value)
    if not is_valid:
        raise serializers.ValidationError(error_msg)
    return value.upper().strip()


def validate_nie_serializer(value: str) -> str:
    """
    Validador para usar en serializers de Django REST Framework (NIE).

    Args:
        value: NIE a validar

    Returns:
        NIE en mayúsculas y sin espacios

    Raises:
        serializers.ValidationError: Si el NIE no es válido
    """
    is_valid, error_msg = validate_nie_format(value)
    if not is_valid:
        raise serializers.ValidationError(error_msg)
    return value.upper().strip()


def validate_nif_serializer(value: str) -> str:
    """
    Validador para usar en serializers de Django REST Framework (NIF).

    Args:
        value: NIF a validar

    Returns:
        NIF en mayúsculas y sin espacios

    Raises:
        serializers.ValidationError: Si el NIF no es válido
    """
    is_valid, error_msg = validate_nif_format(value)
    if not is_valid:
        raise serializers.ValidationError(error_msg)
    return value.upper().strip()


def validate_dni_nie_nif_serializer(value: str) -> str:
    """
    Validador para usar en serializers de Django REST Framework (DNI/NIE/NIF).

    Args:
        value: Documento a validar

    Returns:
        Documento en mayúsculas y sin espacios

    Raises:
        serializers.ValidationError: Si el documento no es válido

    Example:
        class EmpleadoSerializer(serializers.Serializer):
            documento = serializers.CharField(validators=[validate_dni_nie_nif_serializer])
    """
    is_valid, error_msg = validate_dni_nie_nif(value)
    if not is_valid:
        raise serializers.ValidationError(error_msg)
    return value.upper().strip()


# ============================================================================
# HELPERS
# ============================================================================

def normalize_documento(documento: str) -> str:
    """
    Normaliza un documento (DNI/NIE/NIF) a mayúsculas y sin espacios.

    Args:
        documento: Documento a normalizar

    Returns:
        Documento normalizado

    Example:
        >>> normalize_documento("  12345678z  ")
        "12345678Z"
    """
    return documento.upper().strip() if documento else ""
