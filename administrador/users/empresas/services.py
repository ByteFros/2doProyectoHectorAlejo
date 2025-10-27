"""
Servicios de lógica de negocio para empresas y empleados
"""
import csv
import io
import random
import string
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional
from django.db import transaction
from django.utils.text import slugify
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile
from users.common.services import get_user_empresa
from users.common.exceptions import EmpresaProfileNotFoundError
from users.common.validators import validate_dni_nie_nif, normalize_documento


# ============================================================================
# UTILIDADES
# ============================================================================

def generate_unique_username(base_name: str) -> str:
    """
    Genera un username único basado en el nombre y apellido.

    Args:
        base_name: Nombre base para generar el username

    Returns:
        Username único

    Example:
        username = generate_unique_username("Juan Perez")
        # Resultado: "juan-perez" o "juan-perez742" si ya existe
    """
    username = slugify(base_name.lower())
    while CustomUser.objects.filter(username=username).exists():
        suffix = ''.join(random.choices(string.digits, k=3))
        username = f"{slugify(base_name.lower())}{suffix}"
    return username


def generate_employee_email(nombre: str, apellido: str, nombre_empresa: str) -> str:
    """
    DEPRECATED: Esta función ya no se usa.
    Los emails ahora son obligatorios y deben ser proporcionados.

    Se mantiene por compatibilidad con código legacy pero no debe usarse.

    Args:
        nombre: Nombre del empleado
        apellido: Apellido del empleado
        nombre_empresa: Nombre de la empresa

    Returns:
        Email generado

    Example:
        email = generate_employee_email("Juan", "Perez", "Mi Empresa")
        # Resultado: "juan.perez@miempresa.com"
    """
    nombre_empresa_clean = nombre_empresa.lower().replace(" ", "")
    return f"{nombre.lower()}.{apellido.lower()}@{nombre_empresa_clean}.com"


# ============================================================================
# SERVICIOS DE EMPRESAS
# ============================================================================

def create_empresa(data: Dict) -> EmpresaProfile:
    """
    Crea una nueva empresa con su usuario asociado.

    Args:
        data: Diccionario con los datos de la empresa validados

    Returns:
        EmpresaProfile creado

    Raises:
        IntegrityError: Si hay problemas de integridad

    Example:
        empresa = create_empresa({
            'nombre_empresa': 'Mi Empresa',
            'nif': 'B12345678',
            'correo_contacto': 'contacto@empresa.com',
            'address': 'Calle Test 123',
            'city': 'Madrid',
            'postal_code': '28001',
            'permisos': False
        })
    """
    # Crear usuario
    user = CustomUser.objects.create(
        username=data["nombre_empresa"],
        email=data["correo_contacto"],
        role="EMPRESA"
    )
    user.set_password("empresa")  # Contraseña por defecto
    user.save()

    # Crear perfil de empresa
    empresa = EmpresaProfile.objects.create(
        user=user,
        nombre_empresa=data["nombre_empresa"],
        nif=data["nif"],
        address=data.get("address", ""),
        city=data.get("city", ""),
        postal_code=data.get("postal_code", ""),
        correo_contacto=data["correo_contacto"],
        permisos=data.get("permisos", False)
    )

    return empresa


def update_empresa_permissions(empresa: EmpresaProfile, permisos: bool) -> EmpresaProfile:
    """
    Actualiza los permisos de autogestión de una empresa.

    Args:
        empresa: Instancia de EmpresaProfile
        permisos: Nuevo valor de permisos

    Returns:
        EmpresaProfile actualizado
    """
    empresa.permisos = permisos
    empresa.save()
    return empresa


def delete_empresa(empresa: EmpresaProfile) -> None:
    """
    Elimina una empresa y su usuario asociado.
    Los empleados se eliminan en cascada por el modelo.

    Args:
        empresa: Instancia de EmpresaProfile
    """
    user = empresa.user
    empresa.delete()
    if user and user.id:
        user.delete()


# ============================================================================
# SERVICIOS DE EMPLEADOS
# ============================================================================

def create_empleado(
    empresa: EmpresaProfile,
    nombre: str,
    apellido: str,
    dni: str,
    email: str,  # Ahora es obligatorio
    username: str = None,
    password: str = "empleado",
    salario: Optional[Decimal] = None
) -> EmpleadoProfile:
    """
    Crea un nuevo empleado asociado a una empresa.

    Args:
        empresa: Empresa a la que pertenece
        nombre: Nombre del empleado
        apellido: Apellido del empleado
        dni: DNI del empleado (será normalizado automáticamente)
        email: Email del empleado (OBLIGATORIO)
        username: Username (se genera automáticamente si no se proporciona)
        password: Contraseña (default: "empleado")
        salario: Salario bruto anual del empleado (opcional)

    Returns:
        EmpleadoProfile creado

    Raises:
        ValueError: Si el email no se proporciona o el DNI es inválido

    Example:
        empleado = create_empleado(
            empresa=mi_empresa,
            nombre="Juan",
            apellido="Perez",
            dni="12345678A",
            email="juan.perez@empresa.com"
        )
    """
    # Validar que el email sea proporcionado
    if not email:
        raise ValueError("El email es obligatorio")

    # Normalizar y validar DNI
    dni_normalized = normalize_documento(dni)
    is_valid, error_msg = validate_dni_nie_nif(dni_normalized)
    if not is_valid:
        raise ValueError(f"DNI inválido: {error_msg}")

    # Generar username si no se proporciona
    if not username:
        base = f"{nombre}{apellido}"
        username = generate_unique_username(base)

    # Crear usuario
    user = CustomUser(
        username=username,
        email=email,
        role="EMPLEADO"
    )
    user.set_password(password)
    user.save()

    # Crear perfil de empleado
    empleado = EmpleadoProfile.objects.create(
        user=user,
        empresa=empresa,
        nombre=nombre,
        apellido=apellido,
        dni=dni_normalized,  # Guardar DNI normalizado
        salario=salario
    )

    return empleado


def delete_empleado(empleado: EmpleadoProfile) -> None:
    """
    Elimina un empleado y su usuario asociado.

    Args:
        empleado: Instancia de EmpleadoProfile
    """
    user = empleado.user
    empleado.delete()
    if user:
        user.delete()


# ============================================================================
# REGISTRO MASIVO DE EMPLEADOS (CSV)
# ============================================================================

def process_employee_csv(
    empresa: EmpresaProfile,
    csv_file
) -> Dict[str, List]:
    """
    Procesa un archivo CSV y registra empleados en lote.

    Args:
        empresa: Empresa a la que pertenecen los empleados
        csv_file: Archivo CSV con los datos

    Returns:
        Diccionario con:
        - empleados_registrados: Lista de empleados creados
        - empleados_omitidos: Lista de empleados ya existentes
        - errores: Lista de errores encontrados

    Format CSV esperado:
        nombre,apellido,dni,email
        Juan,Perez,12345678A,juan.perez@empresa.com
        Maria,Garcia,87654321B,maria.garcia@empresa.com

    NOTA: Todos los campos son obligatorios en el CSV.

    Example:
        resultado = process_employee_csv(mi_empresa, archivo_csv)
        print(f"Registrados: {len(resultado['empleados_registrados'])}")
        print(f"Omitidos: {len(resultado['empleados_omitidos'])}")
        print(f"Errores: {len(resultado['errores'])}")
    """
    empleados_registrados = []
    empleados_omitidos = []
    errores = []

    # Decodificar archivo
    decoded_file = csv_file.read().decode("utf-8-sig")
    lines = decoded_file.splitlines()
    reader = csv.DictReader(lines)

    if not reader.fieldnames:
        return {
            "empleados_registrados": [],
            "empleados_omitidos": [],
            "errores": [{"error": "El archivo CSV está vacío o no tiene encabezados"}]
        }

    header_map = {header.strip().lower(): header for header in reader.fieldnames if header}
    required_headers = {'nombre', 'apellido', 'dni', 'email'}
    missing = required_headers - set(header_map.keys())
    if missing:
        return {
            "empleados_registrados": [],
            "empleados_omitidos": [],
            "errores": [{
                "error": f"Faltan columnas obligatorias: {', '.join(sorted(missing))}"
            }]
        }

    salario_header = header_map.get('salario')

    with transaction.atomic():
        for row in reader:
            try:
                nombre = row.get(header_map['nombre'], '').strip()
                apellido = row.get(header_map['apellido'], '').strip()
                dni = row.get(header_map['dni'], '').strip()
                email = row.get(header_map['email'], '').strip()

                # Validaciones básicas
                if not nombre or not apellido or not dni or not email:
                    errores.append({"dni": dni, "error": "Nombre, Apellido, DNI y Email son obligatorios"})
                    continue

                # Normalizar DNI
                dni_normalized = normalize_documento(dni)

                # Validar formato DNI
                is_valid, error_msg = validate_dni_nie_nif(dni_normalized)
                if not is_valid:
                    errores.append({"dni": dni, "error": error_msg})
                    continue

                # Verificar si ya existe en esta empresa
                if EmpleadoProfile.objects.filter(empresa=empresa, dni=dni_normalized).exists():
                    empleados_omitidos.append({"dni": dni, "mensaje": "Ya registrado en la empresa"})
                    continue

                # Validar email duplicado
                if CustomUser.objects.filter(email=email).exists():
                    errores.append({"dni": dni, "error": "El email ya está registrado"})
                    continue

                # Generar username único
                base = f"{nombre}{apellido}"
                username = generate_unique_username(base)

                salario = None
                if salario_header:
                    salario_raw = row.get(salario_header, '').strip()
                    if salario_raw:
                        try:
                            salario = Decimal(salario_raw)
                        except (InvalidOperation, ValueError):
                            errores.append({"dni": dni, "error": f"Salario inválido: '{salario_raw}'"})
                            continue
                        if salario < 0:
                            errores.append({"dni": dni, "error": "El salario debe ser un número positivo"})
                            continue

                empleado = create_empleado(
                    empresa=empresa,
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni_normalized,
                    email=email,
                    username=username,
                    salario=salario
                )

                empleados_registrados.append(empleado)

            except Exception as e:
                errores.append({"dni": dni if 'dni' in locals() else "unknown", "error": str(e)})

    return {
        "empleados_registrados": empleados_registrados,
        "empleados_omitidos": empleados_omitidos,
        "errores": errores
    }


# ============================================================================
# QUERIES ESPECIALES
# ============================================================================

def get_companies_with_pending_reviews() -> 'QuerySet[EmpresaProfile]':
    """
    Obtiene empresas que tienen empleados con viajes en estado EN_REVISION.

    Returns:
        QuerySet de EmpresaProfile

    Example:
        empresas = get_companies_with_pending_reviews()
        for empresa in empresas:
            print(f"{empresa.nombre_empresa} tiene viajes pendientes")
    """
    return EmpresaProfile.objects.filter(
        empleados__viaje__estado='EN_REVISION'
    ).distinct()


def get_employees_with_pending_reviews(empresa: EmpresaProfile) -> 'QuerySet[EmpleadoProfile]':
    """
    Obtiene empleados de una empresa que tienen viajes en estado EN_REVISION.

    Args:
        empresa: Empresa a filtrar

    Returns:
        QuerySet de EmpleadoProfile

    Example:
        empleados = get_employees_with_pending_reviews(mi_empresa)
        for empleado in empleados:
            print(f"{empleado.nombre} tiene viajes en revisión")
    """
    return EmpleadoProfile.objects.filter(
        empresa=empresa,
        viaje__estado='EN_REVISION'
    ).distinct()
