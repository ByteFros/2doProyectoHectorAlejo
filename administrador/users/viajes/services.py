"""
Servicios de lógica de negocio para viajes
"""
from datetime import datetime, date, timedelta
from typing import Dict, List
from django.db import transaction
from users.models import Viaje, EmpleadoProfile, Notificacion, DiaViaje, Conversacion, Mensaje


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
    except (ValueError, TypeError):
        raise ValueError("Formato de fecha inválido. Usa YYYY-MM-DD.")

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
    motivo: str = "",
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
        motivo=motivo or "",
        empresa_visitada=empresa_visitada or "",
        ciudad=ciudad or "",
        pais=pais or "",
        es_internacional=es_internacional,
        dias_viajados=dias_viajados
    )

    # Crear notificación para la empresa
    if empleado.empresa:
        nombre_empleado = f"{empleado.nombre} {empleado.apellido}".strip()
        Notificacion.objects.create(
            tipo="VIAJE_SOLICITADO",
            mensaje=f"{nombre_empleado} ha solicitado un viaje a {viaje.destino}.",
            usuario_destino=empleado.empresa.user
        )

    return viaje


# ============================================================================
# SERVICIOS DE DÍAS DE VIAJE
# ============================================================================

def crear_dias_viaje(viaje: Viaje) -> List[DiaViaje]:
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
def inicializar_dias_viaje_finalizado(viaje: Viaje, exentos: bool = True) -> List[DiaViaje]:
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
    if viaje.estado not in ["REVISADO", "EN_REVISION"]:
        raise ValueError(
            f"Este método es solo para viajes REVISADOS o EN_REVISION. "
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
    dias_data: List[Dict],
    motivo: str,
    usuario
) -> Dict:
    """
    Procesa la revisión de un viaje, actualizando días y gastos.

    Args:
        viaje: Viaje a revisar
        dias_data: Lista de diccionarios con {id: int, exento: bool}
        motivo: Motivo de la revisión
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

    # Crear conversación si hay días no exentos y motivo
    conversacion_creada = False
    if dias_no_exentos and motivo:
        conversacion = Conversacion.objects.create(viaje=viaje)
        conversacion.participantes.add(usuario, viaje.empleado.user)

        Mensaje.objects.create(
            conversacion=conversacion,
            autor=usuario,
            contenido=motivo
        )
        conversacion_creada = True

    # Marcar viaje como revisado
    viaje.estado = "REVISADO"
    viaje.save()

    return {
        "viaje": viaje,
        "dias_procesados": len(dias_viaje),
        "dias_no_exentos": len(dias_no_exentos),
        "conversacion_creada": conversacion_creada
    }


# ============================================================================
# QUERIES Y ESTADÍSTICAS
# ============================================================================

def obtener_estadisticas_ciudades(empleado: EmpleadoProfile) -> List[Dict]:
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

    city_stats = {}

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


