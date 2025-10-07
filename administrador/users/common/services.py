"""
Servicios comunes reutilizables para toda la aplicación
Incluye lógica de filtrado jerárquico y obtención de perfiles
"""
from typing import Optional, Tuple
from django.db.models import QuerySet, Model
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile


# ============================================================================
# OBTENCIÓN DE PERFILES
# ============================================================================

def get_user_empresa(user: CustomUser) -> Optional[EmpresaProfile]:
    """
    Obtiene el perfil de empresa de un usuario.

    Args:
        user: Usuario autenticado

    Returns:
        EmpresaProfile o None si no existe

    Example:
        empresa = get_user_empresa(request.user)
        if not empresa:
            return Response({"error": "Sin perfil de empresa"}, status=404)
    """
    try:
        return user.empresa_profile
    except EmpresaProfile.DoesNotExist:
        return None


def get_user_empleado(user: CustomUser) -> Optional[EmpleadoProfile]:
    """
    Obtiene el perfil de empleado de un usuario.

    Args:
        user: Usuario autenticado

    Returns:
        EmpleadoProfile o None si no existe

    Example:
        empleado = get_user_empleado(request.user)
        if not empleado:
            return Response({"error": "Sin perfil de empleado"}, status=404)
    """
    try:
        return user.empleado_profile
    except EmpleadoProfile.DoesNotExist:
        return None


def get_user_profile(user: CustomUser) -> Tuple[Optional[EmpresaProfile], Optional[EmpleadoProfile]]:
    """
    Obtiene ambos perfiles de usuario (empresa y empleado).

    Args:
        user: Usuario autenticado

    Returns:
        Tupla (empresa, empleado) donde alguno puede ser None

    Example:
        empresa, empleado = get_user_profile(request.user)
        if empresa:
            # Lógica para empresa
        elif empleado:
            # Lógica para empleado
    """
    return get_user_empresa(user), get_user_empleado(user)


# ============================================================================
# FILTRADO JERÁRQUICO
# ============================================================================

def filter_queryset_by_role(
    user: CustomUser,
    queryset: QuerySet,
    empresa_field: str = 'empresa',
    empleado_field: str = 'empleado'
) -> QuerySet:
    """
    Filtra un queryset según el rol del usuario.

    Args:
        user: Usuario autenticado
        queryset: QuerySet a filtrar
        empresa_field: Nombre del campo que relaciona con empresa (default: 'empresa')
        empleado_field: Nombre del campo que relaciona con empleado (default: 'empleado')

    Returns:
        QuerySet filtrado según jerarquía

    Raises:
        ValueError: Si el rol no es reconocido

    Example:
        # Para modelo Viaje con campos 'empresa' y 'empleado'
        viajes = filter_queryset_by_role(request.user, Viaje.objects.all())

        # Para modelo con campos personalizados
        items = filter_queryset_by_role(
            request.user,
            Item.objects.all(),
            empresa_field='company',
            empleado_field='employee'
        )
    """
    if user.role == "MASTER":
        return queryset  # MASTER ve todo

    elif user.role == "EMPRESA":
        empresa = get_user_empresa(user)
        if not empresa:
            return queryset.none()  # Sin perfil, devuelve vacío

        # Filtrar por empresa usando el campo especificado
        filter_kwargs = {empresa_field: empresa}
        return queryset.filter(**filter_kwargs)

    elif user.role == "EMPLEADO":
        empleado = get_user_empleado(user)
        if not empleado:
            return queryset.none()  # Sin perfil, devuelve vacío

        # Filtrar por empleado usando el campo especificado
        filter_kwargs = {empleado_field: empleado}
        return queryset.filter(**filter_kwargs)

    else:
        raise ValueError(f"Rol de usuario no reconocido: {user.role}")


def filter_queryset_by_empresa(
    user: CustomUser,
    queryset: QuerySet,
    empresa_field: str = 'empresa__user'
) -> QuerySet:
    """
    Filtra un queryset solo por empresa (para modelos sin campo empleado).

    Args:
        user: Usuario autenticado
        queryset: QuerySet a filtrar
        empresa_field: Campo que relaciona con el usuario de la empresa

    Returns:
        QuerySet filtrado

    Example:
        # Para EmpleadoProfile
        empleados = filter_queryset_by_empresa(
            request.user,
            EmpleadoProfile.objects.all()
        )
    """
    if user.role == "MASTER":
        return queryset

    elif user.role == "EMPRESA":
        filter_kwargs = {empresa_field: user}
        return queryset.filter(**filter_kwargs)

    else:
        return queryset.none()


# ============================================================================
# VALIDACIONES DE PERMISOS
# ============================================================================

def can_access_empresa(user: CustomUser, empresa: EmpresaProfile) -> bool:
    """
    Verifica si un usuario puede acceder a una empresa específica.

    Args:
        user: Usuario autenticado
        empresa: Empresa a verificar

    Returns:
        True si tiene acceso, False en caso contrario

    Example:
        empresa = get_object_or_404(EmpresaProfile, id=empresa_id)
        if not can_access_empresa(request.user, empresa):
            return Response({"error": "No autorizado"}, status=403)
    """
    if user.role == "MASTER":
        return True

    if user.role == "EMPRESA":
        user_empresa = get_user_empresa(user)
        return user_empresa and user_empresa.id == empresa.id

    if user.role == "EMPLEADO":
        empleado = get_user_empleado(user)
        return empleado and empleado.empresa.id == empresa.id

    return False


def can_access_empleado(user: CustomUser, empleado: EmpleadoProfile) -> bool:
    """
    Verifica si un usuario puede acceder a un empleado específico.

    Args:
        user: Usuario autenticado
        empleado: Empleado a verificar

    Returns:
        True si tiene acceso, False en caso contrario

    Example:
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)
        if not can_access_empleado(request.user, empleado):
            return Response({"error": "No autorizado"}, status=403)
    """
    if user.role == "MASTER":
        return True

    if user.role == "EMPRESA":
        user_empresa = get_user_empresa(user)
        return user_empresa and empleado.empresa.id == user_empresa.id

    if user.role == "EMPLEADO":
        user_empleado = get_user_empleado(user)
        return user_empleado and user_empleado.id == empleado.id

    return False


def can_manage_viaje(user: CustomUser, viaje) -> bool:
    """
    Verifica si un usuario puede gestionar un viaje específico.

    Args:
        user: Usuario autenticado
        viaje: Instancia de Viaje

    Returns:
        True si puede gestionar, False en caso contrario

    Example:
        viaje = get_object_or_404(Viaje, id=viaje_id)
        if not can_manage_viaje(request.user, viaje):
            return Response({"error": "No autorizado"}, status=403)
    """
    if user.role == "MASTER":
        return True

    if user.role == "EMPRESA":
        user_empresa = get_user_empresa(user)
        return user_empresa and viaje.empresa.id == user_empresa.id

    if user.role == "EMPLEADO":
        user_empleado = get_user_empleado(user)
        return user_empleado and viaje.empleado.id == user_empleado.id

    return False


# ============================================================================
# HELPERS DE VALIDACIÓN
# ============================================================================

def validate_user_has_empresa_profile(user: CustomUser) -> Tuple[bool, Optional[str]]:
    """
    Valida que el usuario tenga perfil de empresa.

    Args:
        user: Usuario autenticado

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        is_valid, error_msg = validate_user_has_empresa_profile(request.user)
        if not is_valid:
            return Response({"error": error_msg}, status=400)
    """
    if user.role != "EMPRESA":
        return False, "El usuario no es una empresa"

    empresa = get_user_empresa(user)
    if not empresa:
        return False, "No tienes un perfil de empresa asociado"

    return True, None


def validate_user_has_empleado_profile(user: CustomUser) -> Tuple[bool, Optional[str]]:
    """
    Valida que el usuario tenga perfil de empleado.

    Args:
        user: Usuario autenticado

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        is_valid, error_msg = validate_user_has_empleado_profile(request.user)
        if not is_valid:
            return Response({"error": error_msg}, status=400)
    """
    if user.role != "EMPLEADO":
        return False, "El usuario no es un empleado"

    empleado = get_user_empleado(user)
    if not empleado:
        return False, "No tienes un perfil de empleado asociado"

    return True, None


# ============================================================================
# FILTROS ESPECIALES
# ============================================================================

def exclude_by_status(queryset: QuerySet, field: str, exclude_values: list) -> QuerySet:
    """
    Excluye registros por valores de estado.

    Args:
        queryset: QuerySet a filtrar
        field: Campo de estado
        exclude_values: Lista de valores a excluir

    Returns:
        QuerySet filtrado

    Example:
        # Excluir viajes cancelados
        viajes = exclude_by_status(
            Viaje.objects.all(),
            'estado',
            ['CANCELADO']
        )
    """
    filter_kwargs = {f"{field}__in": exclude_values}
    return queryset.exclude(**filter_kwargs)


def filter_by_date_range(queryset: QuerySet, date_field: str, start_date, end_date) -> QuerySet:
    """
    Filtra por rango de fechas.

    Args:
        queryset: QuerySet a filtrar
        date_field: Nombre del campo de fecha
        start_date: Fecha inicio
        end_date: Fecha fin

    Returns:
        QuerySet filtrado

    Example:
        viajes = filter_by_date_range(
            Viaje.objects.all(),
            'fecha_inicio',
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
    """
    filter_kwargs = {
        f"{date_field}__gte": start_date,
        f"{date_field}__lte": end_date
    }
    return queryset.filter(**filter_kwargs)
