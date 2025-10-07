"""
Servicios de lógica de negocio para empresas y empleados
"""
import csv
import io
import random
import string
from typing import Dict, List, Tuple
from django.db import transaction
from django.utils.text import slugify
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile
from users.common.services import get_user_empresa
from users.common.exceptions import EmpresaProfileNotFoundError


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
    Genera un email corporativo para el empleado.

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
    email: str = None,
    username: str = None,
    password: str = "empleado"
) -> EmpleadoProfile:
    """
    Crea un nuevo empleado asociado a una empresa.

    Args:
        empresa: Empresa a la que pertenece
        nombre: Nombre del empleado
        apellido: Apellido del empleado
        dni: DNI del empleado
        email: Email (se genera automáticamente si no se proporciona)
        username: Username (se genera automáticamente si no se proporciona)
        password: Contraseña (default: "empleado")

    Returns:
        EmpleadoProfile creado

    Example:
        empleado = create_empleado(
            empresa=mi_empresa,
            nombre="Juan",
            apellido="Perez",
            dni="12345678A"
        )
    """
    # Generar email si no se proporciona
    if not email:
        email = generate_employee_email(nombre, apellido, empresa.nombre_empresa)

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
        dni=dni
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
        Maria,Garcia,87654321B,

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
    decoded_file = csv_file.read().decode("utf-8").splitlines()
    reader = csv.reader(decoded_file)
    next(reader, None)  # Saltar encabezados

    with transaction.atomic():
        for row in reader:
            try:
                # Parsear row
                if len(row) < 3:
                    errores.append({"row": row, "error": "Formato inválido"})
                    continue

                nombre, apellido, dni = row[0], row[1], row[2]
                email = row[3] if len(row) > 3 else ""

                # Validaciones básicas
                if not nombre or not apellido or not dni:
                    errores.append({"dni": dni, "error": "Nombre, Apellido y DNI son obligatorios"})
                    continue

                # Verificar si ya existe en esta empresa
                if EmpleadoProfile.objects.filter(empresa=empresa, dni=dni).exists():
                    empleados_omitidos.append({"dni": dni, "mensaje": "Ya registrado en la empresa"})
                    continue

                # Generar username
                username = f"{nombre}{apellido}".replace(" ", "").lower()

                # Generar email si no viene
                if not email:
                    email = generate_employee_email(nombre, apellido, empresa.nombre_empresa)

                # Validar duplicados
                if CustomUser.objects.filter(email=email).exists():
                    errores.append({"dni": dni, "error": "El email ya está registrado"})
                    continue

                if CustomUser.objects.filter(username=username).exists():
                    errores.append({"dni": dni, "error": "El username ya está registrado"})
                    continue

                # Crear empleado
                empleado = create_empleado(
                    empresa=empresa,
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni,
                    email=email,
                    username=username
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
