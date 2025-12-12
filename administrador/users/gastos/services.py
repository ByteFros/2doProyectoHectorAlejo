"""
Servicios de lógica de negocio para gastos
"""

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet

from users.common.files import compress_if_image
from users.common.services import mark_company_review_pending
from users.models import EmpleadoProfile, EmpresaProfile, Gasto, Viaje

# ============================================================================
# VALIDACIONES
# ============================================================================

def validar_viaje_para_gasto(viaje: Viaje) -> None:
    """
    Valida que un viaje pueda recibir gastos.

    Args:
        viaje: Viaje a validar

    Raises:
        ValueError: Si el viaje ya fue revisado
    """
    if viaje.estado == "REVISADO":
        raise ValueError("No puedes registrar gastos en viajes revisados")


def validar_estado_gasto(estado: str) -> None:
    """
    Valida que el estado de un gasto sea válido.

    Args:
        estado: Estado a validar

    Raises:
        ValueError: Si el estado no es válido
    """
    if estado not in ["APROBADO", "RECHAZADO"]:
        raise ValueError("Estado inválido")


# ============================================================================
# SERVICIOS DE GASTOS
# ============================================================================

FILE_UPLOAD_LIMIT: int = int(getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024) or 10 * 1024 * 1024)


def _prepare_comprobante(comprobante: UploadedFile | None):
    if not comprobante:
        return None
    if comprobante.size and comprobante.size > FILE_UPLOAD_LIMIT:
        raise ValueError("El comprobante supera el límite permitido (10 MB).")
    return compress_if_image(comprobante, prefer_detail=True).file


def crear_gasto(
    empleado: EmpleadoProfile,
    viaje: Viaje,
    concepto: str,
    monto: float,
    fecha_gasto: str | None = None,
    comprobante: UploadedFile | None = None,
    descripcion: str = ""
) -> Gasto:
    """
    Crea un nuevo gasto para un empleado en un viaje.

    Args:
        empleado: Empleado que registra el gasto
        viaje: Viaje asociado al gasto
        concepto: Concepto del gasto
        monto: Monto del gasto
        fecha_gasto: Fecha del gasto (opcional)
        comprobante: Archivo comprobante (opcional)
        descripcion: Descripción adicional (opcional)

    Returns:
        Gasto creado

    Raises:
        ValueError: Si el viaje ya fue revisado
    """
    # Validar viaje
    validar_viaje_para_gasto(viaje)

    # Crear gasto
    comprobante_file = _prepare_comprobante(comprobante)

    gasto_kwargs = {
        "empleado": empleado,
        "empresa": empleado.empresa,
        "viaje": viaje,
        "concepto": concepto,
        "monto": monto,
        "fecha_gasto": fecha_gasto,
        "comprobante": comprobante_file,
        "estado": "PENDIENTE",
    }
    if hasattr(Gasto, "descripcion"):
        gasto_kwargs["descripcion"] = descripcion or ""

    gasto = Gasto.objects.create(**gasto_kwargs)

    return gasto


def actualizar_gasto(
    gasto: Gasto,
    concepto: str | None = None,
    monto: float | None = None,
    fecha_gasto: str | None = None,
    comprobante: UploadedFile | None = None,
    descripcion: str | None = None
) -> Gasto:
    """
    Actualiza un gasto existente.

    Args:
        gasto: Gasto a actualizar
        concepto: Nuevo concepto (opcional)
        monto: Nuevo monto (opcional)
        fecha_gasto: Nueva fecha (opcional)
        comprobante: Nuevo comprobante (opcional)
        descripcion: Nueva descripción (opcional)

    Returns:
        Gasto actualizado
    """
    if concepto is not None:
        gasto.concepto = concepto
    if monto is not None:
        gasto.monto = monto
    if fecha_gasto is not None:
        gasto.fecha_gasto = fecha_gasto
    if comprobante is not None:
        gasto.comprobante = _prepare_comprobante(comprobante)
    if descripcion is not None and hasattr(gasto, "descripcion"):
        gasto.descripcion = descripcion

    gasto.save()

    if gasto.empresa and gasto.viaje and gasto.viaje.estado == "REVISADO":
        mark_company_review_pending(gasto.empresa)

    return gasto


def aprobar_rechazar_gasto(gasto: Gasto, nuevo_estado: str) -> Gasto:
    """
    Aprueba o rechaza un gasto.

    Args:
        gasto: Gasto a aprobar/rechazar
        nuevo_estado: "APROBADO" o "RECHAZADO"

    Returns:
        Gasto actualizado

    Raises:
        ValueError: Si el estado es inválido
    """
    validar_estado_gasto(nuevo_estado)

    gasto.estado = nuevo_estado
    gasto.save()

    if gasto.empresa and gasto.viaje and gasto.viaje.estado == "REVISADO":
        mark_company_review_pending(gasto.empresa)

    return gasto


def eliminar_gasto(gasto: Gasto) -> None:
    """
    Elimina un gasto.

    Args:
        gasto: Gasto a eliminar
    """
    empresa = gasto.empresa
    viaje = gasto.viaje
    gasto.delete()

    if empresa and viaje and viaje.estado == "REVISADO":
        mark_company_review_pending(empresa)


def puede_gestionar_gasto(usuario, gasto: Gasto) -> bool:
    """
    Verifica si un usuario puede gestionar (aprobar/rechazar) un gasto.

    Args:
        usuario: Usuario a verificar
        gasto: Gasto a gestionar

    Returns:
        True si puede gestionar, False si no
    """
    # MASTER puede gestionar cualquier gasto
    if usuario.role == "MASTER":
        return True

    # EMPRESA solo puede gestionar gastos de su empresa
    if usuario.role == "EMPRESA":
        try:
            empresa = EmpresaProfile.objects.get(user=usuario)
            return gasto.empresa == empresa
        except EmpresaProfile.DoesNotExist:
            return False

    return False


def puede_modificar_gasto(usuario, gasto: Gasto) -> bool:
    """
    Verifica si un usuario puede modificar/eliminar un gasto.

    Args:
        usuario: Usuario a verificar
        gasto: Gasto a modificar

    Returns:
        True si puede modificar, False si no
    """
    # Solo el empleado dueño del gasto puede modificarlo
    return bool(gasto.empleado.user == usuario)


# ============================================================================
# QUERIES Y FILTROS
# ============================================================================

def obtener_gastos_por_rol(usuario) -> QuerySet[Gasto]:
    """
    Obtiene los gastos según el rol del usuario.

    Args:
        usuario: Usuario que solicita los gastos

    Returns:
        QuerySet de Gasto filtrado según el rol
    """
    if usuario.role == "MASTER":
        return Gasto.objects.all()

    elif usuario.role == "EMPRESA":
        return Gasto.objects.filter(empresa__user=usuario)

    elif usuario.role == "EMPLEADO":
        return Gasto.objects.filter(empleado__user=usuario)

    return Gasto.objects.none()


def obtener_gastos_por_viaje(viaje: Viaje) -> QuerySet[Gasto]:
    """
    Obtiene todos los gastos de un viaje.

    Args:
        viaje: Viaje a filtrar

    Returns:
        QuerySet de Gasto
    """
    return Gasto.objects.filter(viaje=viaje)


def obtener_gastos_pendientes(empresa: EmpresaProfile | None = None) -> QuerySet[Gasto]:
    """
    Obtiene gastos pendientes de aprobación.

    Args:
        empresa: Empresa a filtrar (opcional, para MASTER ve todos)

    Returns:
        QuerySet de Gasto
    """
    gastos = Gasto.objects.filter(estado="PENDIENTE")

    if empresa:
        gastos = gastos.filter(empresa=empresa)

    return gastos
