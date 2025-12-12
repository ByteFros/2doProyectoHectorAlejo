"""
Servicios de lógica de negocio para viajes
"""
from datetime import date, datetime, timedelta
from typing import TypedDict

from django.db import transaction

from users.common.services import mark_company_review_pending
from users.models import DiaViaje, EmpleadoProfile, Gasto, Viaje


class CityStat(TypedDict):
    city: str
    trips: int
    days: int
    nonExemptDays: int
    exemptDays: int


# ============================================================================
# VALIDACIONES
# ============================================================================

def validar_fechas(fecha_inicio_str: str, fecha_fin_str: str) -> tuple:
    """
    Valida y convierte strings de fechas al formato date.

    Args:
        fecha_inicio_str: Fecha de inicio en formato YYYY-MM-DD
        fecha_fin_str: Fecha de fin en formato YYYY-MM-DD

    Returns:
        Tupla (fecha_inicio, fecha_fin)

    Raises:
        ValueError: Si el formato es inválido o fecha_fin < fecha_inicio
    """
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ValueError("Formato de fecha inválido. Usa YYYY-MM-DD.") from exc

    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")

    return fecha_inicio, fecha_fin


# ============================================================================
# SERVICIOS DE VIAJES
# ============================================================================

@transaction.atomic
def crear_viaje(
    empleado: EmpleadoProfile,
    destino: str,
    fecha_inicio: date,
    fecha_fin: date,
    motivo: str,
    empresa_visitada: str = "",
    ciudad: str = "",
    pais: str = "",
    es_internacional: bool = False
) -> Viaje:
    """
    Crea un nuevo viaje para un empleado.

    Args:
        empleado: Empleado que solicita el viaje
        destino: Destino del viaje
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin
        motivo: Motivo del viaje
        empresa_visitada: Empresa visitada
        ciudad: Ciudad destino
        pais: País destino
        es_internacional: Si el viaje es internacional

    Returns:
        Viaje creado

    Raises:
        ValueError: Si hay conflicto con otros viajes o fechas inválidas
    """
    # Calcular días viajados
    dias_viajados = (fecha_fin - fecha_inicio).days + 1

    # Crear viaje
    viaje = Viaje.objects.create(
        empleado=empleado,
        empresa=empleado.empresa,
        destino=destino,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado="EN_REVISION",
        motivo=motivo,
        empresa_visitada=empresa_visitada or "",
        ciudad=ciudad or "",
        pais=pais or "",
        es_internacional=es_internacional,
        dias_viajados=dias_viajados
    )

    crear_dias_viaje(viaje)

    return viaje


# ============================================================================
# SERVICIOS DE DÍAS DE VIAJE
# ============================================================================

def crear_dias_viaje(viaje: Viaje) -> list[DiaViaje]:
    """
    Crea objetos DiaViaje para cada día del viaje.

    Args:
        viaje: Viaje para el que crear los días

    Returns:
        Lista de DiaViaje creados
    """
    dias = []
    start = viaje.fecha_inicio
    end = viaje.fecha_fin
    delta = (end - start).days

    for i in range(delta + 1):
        fecha = start + timedelta(days=i)
        dia, created = DiaViaje.objects.get_or_create(viaje=viaje, fecha=fecha)
        dias.append(dia)

    return dias


@transaction.atomic
def inicializar_dias_viaje_finalizado(viaje: Viaje, exentos: bool = True) -> list[DiaViaje]:
    """
    Crea e inicializa DiaViaje para viajes ya revisados (uso en scripts).

    Este método es útil para scripts que crean viajes directamente en estado
    REVISADO (por ejemplo, para datos de prueba históricos).

    Args:
        viaje: Viaje en estado REVISADO sin DiaViaje
        exentos: Si True, marca todos los días como exentos. Si False, como no exentos.

    Returns:
        Lista de DiaViaje creados

    Raises:
        ValueError: Si el viaje no está REVISADO o EN_REVISION
    """
    if viaje.estado not in ["REVISADO", "EN_REVISION", "REABIERTO"]:
        raise ValueError(
            f"Este método es solo para viajes REVISADOS, EN_REVISION o REABIERTO. "
            f"Estado actual: {viaje.estado}"
        )

    # Crear todos los días
    dias = crear_dias_viaje(viaje)

    # Inicializar todos como revisados y con el estado de exento especificado
    for dia in dias:
        dia.exento = exentos
        dia.revisado = True
        dia.save()

    return dias


@transaction.atomic
def procesar_revision_viaje(
    viaje: Viaje,
    dias_data: list[dict],
    usuario
) -> dict:
    """
    Procesa la revisión de un viaje, actualizando días y gastos.

    Args:
        viaje: Viaje a revisar
        dias_data: Lista de diccionarios con {id: int, exento: bool}
        usuario: Usuario que realiza la revisión

    Returns:
        Diccionario con resultado de la operación

    Raises:
        ValueError: Si el formato de días es inválido o faltan días
    """
    # Validar formato de días
    if not isinstance(dias_data, list) or not all('id' in d and 'exento' in d for d in dias_data):
        raise ValueError("Formato de días inválido")

    # Obtener días del viaje
    dias_viaje = viaje.dias.all()

    # Validar que existen todos los DiaViaje esperados
    dias_esperados = (viaje.fecha_fin - viaje.fecha_inicio).days + 1
    if dias_viaje.count() != dias_esperados:
        raise ValueError(
            f"Faltan días por crear. Esperados: {dias_esperados}, "
            f"Encontrados: {dias_viaje.count()}. "
            f"Ejecuta crear_dias_viaje(viaje) primero."
        )

    # Mapear días enviados
    id_a_exento = {d['id']: d['exento'] for d in dias_data}
    ids_validos = set(d.id for d in dias_viaje)

    # Validar que todos los días pertenezcan al viaje
    if not set(id_a_exento.keys()).issubset(ids_validos):
        raise ValueError("Uno o más días no pertenecen al viaje")

    # Procesar cada día
    dias_no_exentos = []
    for dia in dias_viaje:
        exento = id_a_exento.get(dia.id, dia.exento)
        dia.exento = exento
        dia.revisado = True
        dia.save()

        # Actualizar estado de gastos
        estado_gasto = "RECHAZADO" if not exento else "APROBADO"
        dia.gastos.update(estado=estado_gasto)

        if not exento:
            dias_no_exentos.append(dia)

    # Marcar viaje como revisado
    viaje.estado = "REVISADO"
    viaje.save()

    mark_company_review_pending(viaje.empresa)

    return {
        "viaje_id": viaje.id,
        "dias_procesados": len(dias_viaje),
        "dias_no_exentos": len(dias_no_exentos)
    }


@transaction.atomic
def cambiar_estado_viaje(
    viaje: Viaje,
    target_state: str,
    usuario,
    dias_data: list[dict] | None = None
) -> dict:
    """
    Maneja las transiciones permitidas de estado para un viaje.

    Args:
        viaje: Viaje a actualizar
        target_state: Estado deseado ("REVISADO" o "REABIERTO")
        usuario: Usuario que ejecuta la transición
        dias_data: Datos de días para procesar revisión (cuando aplica)

    Returns:
        Información sobre la transición ejecutada.

    Raises:
        ValueError: Si la transición no es válida o faltan datos requeridos.
    """
    estado_actual = viaje.estado

    if target_state not in ["REVISADO", "REABIERTO"]:
        raise ValueError("Estado de destino inválido.")

    if target_state == "REVISADO":
        if estado_actual not in ["EN_REVISION", "REABIERTO"]:
            raise ValueError("Solo puedes marcar como revisado un viaje en revisión o reabierto.")
        if dias_data is not None:
            resultado = procesar_revision_viaje(viaje, dias_data, usuario)
            return {"nuevo_estado": "REVISADO", **resultado}

        dias_pendientes = viaje.dias.filter(revisado=False).order_by("fecha")
        if dias_pendientes.exists():
            fechas_pendientes = ", ".join(d.fecha.isoformat() for d in dias_pendientes)
            raise ValueError(
                "No puedes finalizar la revisión. "
                f"Días pendientes de revisar: {fechas_pendientes}"
            )

        dias_queryset = viaje.dias.order_by("fecha")
        dias_no_exentos = dias_queryset.filter(exento=False).count()

        viaje.estado = "REVISADO"
        viaje.save(update_fields=["estado"])

        mark_company_review_pending(viaje.empresa)

        return {
            "nuevo_estado": "REVISADO",
            "viaje_id": viaje.id,
            "dias_procesados": dias_queryset.count(),
            "dias_no_exentos": dias_no_exentos
        }

    # target_state == "REABIERTO"
    if estado_actual != "REVISADO":
        raise ValueError("Solo puedes reabrir viajes que están revisados.")

    viaje.estado = "REABIERTO"
    viaje.save(update_fields=["estado"])

    viaje.dias.update(revisado=False)
    Gasto.objects.filter(viaje=viaje).exclude(estado='PENDIENTE').update(estado='PENDIENTE')

    mark_company_review_pending(viaje.empresa)

    return {"nuevo_estado": "REABIERTO", "viaje_id": viaje.id}


# ============================================================================
# QUERIES Y ESTADÍSTICAS
# ============================================================================

def obtener_estadisticas_ciudades(empleado: EmpleadoProfile) -> list[CityStat]:
    """
    Obtiene estadísticas de ciudades visitadas por un empleado.

    Args:
        empleado: Empleado a analizar

    Returns:
        Lista de diccionarios con estadísticas por ciudad
    """
    viajes = Viaje.objects.filter(
        empleado=empleado,
        estado='REVISADO'
    )

    city_stats: dict[str, CityStat] = {}

    for viaje in viajes:
        ciudad = viaje.ciudad or viaje.destino.split(',')[0].strip()
        dias = viaje.dias_viajados or 1

        # Calcular días exentos y no exentos
        dias_relacionados = DiaViaje.objects.filter(viaje=viaje)
        exentos = dias_relacionados.filter(exento=True).count()
        no_exentos = dias_relacionados.filter(exento=False).count()

        if ciudad not in city_stats:
            city_stats[ciudad] = {
                'city': ciudad,
                'trips': 1,
                'days': dias,
                'nonExemptDays': no_exentos,
                'exemptDays': exentos,
            }
        else:
            city_stats[ciudad]['trips'] += 1
            city_stats[ciudad]['days'] += dias
            city_stats[ciudad]['nonExemptDays'] += no_exentos
            city_stats[ciudad]['exemptDays'] += exentos

    return list(city_stats.values())


