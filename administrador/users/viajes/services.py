"""
Servicios de lógica de negocio para viajes
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from django.db import transaction
from users.models import Viaje, EmpleadoProfile, EmpresaProfile, Notificacion, DiaViaje, Conversacion, Mensaje


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


def determinar_estado_inicial(fecha_inicio: date, fecha_fin: date) -> str:
    """
    Determina el estado inicial de un viaje según las fechas.

    Args:
        fecha_inicio: Fecha de inicio del viaje
        fecha_fin: Fecha de fin del viaje

    Returns:
        Estado del viaje: FINALIZADO, EN_CURSO o PENDIENTE
    """
    hoy = date.today()

    if fecha_fin < hoy:
        return "FINALIZADO"
    elif fecha_inicio == hoy:
        return "EN_CURSO"
    elif fecha_inicio > hoy:
        return "PENDIENTE"
    else:
        # Viaje comenzó en el pasado pero no ha terminado
        return "EN_CURSO"


def validar_conflicto_viajes(
    empleado: EmpleadoProfile,
    fecha_inicio: date,
    fecha_fin: date,
    viaje_id: Optional[int] = None
) -> bool:
    """
    Verifica si hay conflicto con otros viajes del empleado.

    Args:
        empleado: Empleado a verificar
        fecha_inicio: Fecha de inicio del nuevo viaje
        fecha_fin: Fecha de fin del nuevo viaje
        viaje_id: ID del viaje a excluir de la búsqueda (para updates)

    Returns:
        True si hay conflicto, False si no
    """
    query = Viaje.objects.filter(
        empleado=empleado,
        fecha_inicio__lte=fecha_fin,
        fecha_fin__gte=fecha_inicio,
        estado__in=["PENDIENTE", "EN_CURSO"]
    )

    if viaje_id:
        query = query.exclude(id=viaje_id)

    return query.exists()


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
    # Validar conflictos
    if validar_conflicto_viajes(empleado, fecha_inicio, fecha_fin):
        raise ValueError("Ya tienes un viaje programado en esas fechas.")

    # Determinar estado inicial
    estado = determinar_estado_inicial(fecha_inicio, fecha_fin)

    # Calcular días viajados
    dias_viajados = (fecha_fin - fecha_inicio).days + 1

    # Crear viaje
    viaje = Viaje.objects.create(
        empleado=empleado,
        empresa=empleado.empresa,
        destino=destino,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=estado,
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


def iniciar_viaje(viaje: Viaje) -> Viaje:
    """
    Inicia un viaje (cambia estado a EN_CURSO).

    Args:
        viaje: Viaje a iniciar

    Returns:
        Viaje actualizado

    Raises:
        ValueError: Si no se puede iniciar el viaje
    """
    if date.today() < viaje.fecha_inicio:
        raise ValueError("Aún no puedes iniciar este viaje, la fecha de inicio no ha llegado")

    viaje.estado = "EN_CURSO"
    viaje.save()
    return viaje


@transaction.atomic
def finalizar_viaje(viaje: Viaje) -> Viaje:
    """
    Finaliza un viaje y lo pasa a estado EN_REVISION.
    Crea objetos DiaViaje para cada jornada.

    Args:
        viaje: Viaje a finalizar

    Returns:
        Viaje actualizado

    Raises:
        ValueError: Si el viaje no está EN_CURSO
    """
    if viaje.estado != 'EN_CURSO':
        raise ValueError('Solo puedes finalizar un viaje en curso.')

    # Cambiar a revisión
    viaje.estado = 'EN_REVISION'
    viaje.save()

    # Crear objetos DiaViaje para cada jornada
    crear_dias_viaje(viaje)

    return viaje


def cancelar_viaje(viaje: Viaje) -> Viaje:
    """
    Cancela un viaje pendiente.

    Args:
        viaje: Viaje a cancelar

    Returns:
        Viaje actualizado

    Raises:
        ValueError: Si el viaje no está PENDIENTE
    """
    if viaje.estado != "PENDIENTE":
        raise ValueError("Solo puedes cancelar un viaje que aún está pendiente")

    viaje.estado = "CANCELADO"
    viaje.save()
    return viaje


@transaction.atomic
def aprobar_rechazar_viaje(
    viaje: Viaje,
    nuevo_estado: str,
    motivo: str = ""
) -> Viaje:
    """
    Aprueba o rechaza un viaje.

    Args:
        viaje: Viaje a aprobar/rechazar
        nuevo_estado: "APROBADO" o "RECHAZADO"
        motivo: Motivo del rechazo (opcional)

    Returns:
        Viaje actualizado

    Raises:
        ValueError: Si el estado es inválido
    """
    if nuevo_estado not in ["APROBADO", "RECHAZADO"]:
        raise ValueError("Estado inválido")

    viaje.estado = nuevo_estado
    viaje.save()

    # Crear notificación para el empleado
    mensaje = f"Tu viaje a {viaje.destino} ha sido {nuevo_estado.lower()}."
    if nuevo_estado == "RECHAZADO" and motivo:
        mensaje += f" Motivo: {motivo}"

    Notificacion.objects.create(
        tipo=f"VIAJE_{nuevo_estado}",
        mensaje=mensaje,
        usuario_destino=viaje.empleado.user
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
        ValueError: Si el formato de días es inválido
    """
    # Validar formato de días
    if not isinstance(dias_data, list) or not all('id' in d and 'exento' in d for d in dias_data):
        raise ValueError("Formato de días inválido")

    # Mapear días enviados
    id_a_exento = {d['id']: d['exento'] for d in dias_data}
    dias_viaje = viaje.dias.all()
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

    # Marcar viaje como finalizado
    viaje.estado = "FINALIZADO"
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

def obtener_viaje_en_curso(empleado: EmpleadoProfile) -> Optional[Viaje]:
    """
    Obtiene el viaje en curso de un empleado.

    Args:
        empleado: Empleado a buscar

    Returns:
        Viaje en curso o None
    """
    return Viaje.objects.filter(
        empleado=empleado,
        estado="EN_CURSO"
    ).order_by("-fecha_inicio").first()


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
        estado='FINALIZADO'
    ).exclude(estado='CANCELADO')

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


def tiene_viaje_en_curso(empleado: EmpleadoProfile) -> bool:
    """
    Verifica si un empleado tiene un viaje en curso.

    Args:
        empleado: Empleado a verificar

    Returns:
        True si tiene viaje en curso, False si no
    """
    return Viaje.objects.filter(empleado=empleado, estado="EN_CURSO").exists()
