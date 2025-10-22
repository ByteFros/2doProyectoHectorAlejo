"""
Servicios de lógica de negocio para mensajería
"""
from typing import Optional
from django.core.files.uploadedfile import UploadedFile
from users.models import (
    MensajeJustificante, Conversacion, Mensaje, Gasto,
    CustomUser, Viaje, EmpresaProfile
)


# ============================================================================
# SERVICIOS DE MENSAJES JUSTIFICANTES
# ============================================================================

def solicitar_justificante(
    usuario: CustomUser,
    gasto: Gasto,
    motivo: str
) -> MensajeJustificante:
    """
    Solicita un justificante para un gasto.

    Args:
        usuario: Usuario que solicita (MASTER o EMPRESA)
        gasto: Gasto para el que solicitar justificante
        motivo: Motivo de la solicitud

    Returns:
        MensajeJustificante creado

    Raises:
        ValueError: Si hay errores de validación
    """
    # Validar motivo
    if not motivo or not motivo.strip():
        raise ValueError("Debes explicar por qué solicitas el justificante")

    # Validar que no tenga ya comprobante
    if gasto.comprobante:
        raise ValueError("Este gasto ya tiene un justificante")

    # Validar que no haya solicitud pendiente
    if MensajeJustificante.objects.filter(gasto=gasto, respuesta__isnull=True).exists():
        raise ValueError("Ya se ha solicitado un justificante para este gasto.")

    # Crear mensaje
    mensaje = MensajeJustificante.objects.create(
        gasto=gasto,
        autor=usuario,
        motivo=motivo
    )

    # Actualizar estado del gasto
    gasto.estado = "JUSTIFICAR"
    gasto.save()

    return mensaje


def responder_justificante(
    mensaje: MensajeJustificante,
    respuesta: str,
    archivo: Optional[UploadedFile] = None
) -> MensajeJustificante:
    """
    Responde a una solicitud de justificante.

    Args:
        mensaje: Mensaje a responder
        respuesta: Texto de la respuesta
        archivo: Archivo justificante (opcional)

    Returns:
        MensajeJustificante actualizado

    Raises:
        ValueError: Si hay errores de validación
    """
    # Validar que no haya sido respondido
    if mensaje.respuesta:
        raise ValueError("Este mensaje ya ha sido respondido")

    # Validar respuesta
    if not respuesta or not respuesta.strip():
        raise ValueError("La respuesta no puede estar vacía")

    # Actualizar mensaje
    mensaje.respuesta = respuesta
    mensaje.estado = "pendiente"

    if archivo:
        mensaje.archivo_justificante = archivo
        mensaje.gasto.comprobante = archivo

    mensaje.save()
    mensaje.gasto.save()

    return mensaje


def cambiar_estado_justificante(
    mensaje: MensajeJustificante,
    nuevo_estado: str
) -> MensajeJustificante:
    """
    Cambia el estado de un justificante (aprobar/rechazar).

    Args:
        mensaje: Mensaje a actualizar
        nuevo_estado: "aprobado" o "rechazado"

    Returns:
        MensajeJustificante actualizado

    Raises:
        ValueError: Si el estado es inválido
    """
    if nuevo_estado not in ["aprobado", "rechazado"]:
        raise ValueError("Estado inválido")

    mensaje.estado = nuevo_estado
    mensaje.save()

    # Actualizar estado del gasto
    if nuevo_estado == "aprobado":
        mensaje.gasto.estado = "APROBADO"
    elif nuevo_estado == "rechazado":
        mensaje.gasto.estado = "RECHAZADO"

    mensaje.gasto.save()

    return mensaje


def puede_solicitar_justificante(usuario: CustomUser, gasto: Gasto) -> bool:
    """
    Verifica si un usuario puede solicitar justificante para un gasto.

    Args:
        usuario: Usuario a verificar
        gasto: Gasto a validar

    Returns:
        True si puede solicitar, False si no
    """
    # MASTER puede solicitar a cualquier gasto
    if usuario.role == "MASTER":
        return True

    # EMPRESA solo puede solicitar a sus propios gastos
    if usuario.role == "EMPRESA":
        try:
            empresa = EmpresaProfile.objects.get(user=usuario)
            return gasto.empresa == empresa
        except EmpresaProfile.DoesNotExist:
            return False

    return False


def puede_responder_justificante(usuario: CustomUser, mensaje: MensajeJustificante) -> bool:
    """
    Verifica si un usuario puede responder un mensaje de justificante.

    Args:
        usuario: Usuario a verificar
        mensaje: Mensaje a validar

    Returns:
        True si puede responder, False si no
    """
    # Solo el empleado dueño del gasto puede responder
    return mensaje.gasto.empleado.user == usuario


def puede_cambiar_estado_justificante(usuario: CustomUser, mensaje: MensajeJustificante) -> bool:
    """
    Verifica si un usuario puede cambiar el estado de un justificante.

    Args:
        usuario: Usuario a verificar
        mensaje: Mensaje a validar

    Returns:
        True si puede cambiar estado, False si no
    """
    # MASTER puede cambiar cualquier estado
    if usuario.role == "MASTER":
        return True

    # EMPRESA solo puede cambiar estados de sus gastos
    if usuario.role == "EMPRESA":
        return mensaje.gasto.empresa.user == usuario

    return False


# ============================================================================
# SERVICIOS DE CONVERSACIONES
# ============================================================================

def crear_conversacion(
    usuario: CustomUser,
    viaje: Optional[Viaje] = None,
    empleado: Optional[CustomUser] = None
) -> Conversacion:
    """
    Crea una conversación nueva.

    Args:
        usuario: Usuario que crea la conversación (MASTER o EMPRESA)
        viaje: Viaje asociado (opcional)
        empleado: Empleado para conversación libre (opcional)

    Returns:
        Conversacion creada

    Raises:
        ValueError: Si no se especifica viaje ni empleado
    """
    if not viaje and not empleado:
        raise ValueError("Envía viaje_id o empleado_id")

    if viaje:
        conversacion = Conversacion.objects.create(viaje=viaje)
        conversacion.participantes.add(usuario, viaje.empleado.user)
    else:
        conversacion = Conversacion.objects.create()
        conversacion.participantes.add(usuario, empleado)

    return conversacion


def enviar_mensaje(
    conversacion: Conversacion,
    autor: CustomUser,
    contenido: str,
    gasto: Optional[Gasto] = None,
    archivo: Optional[UploadedFile] = None
) -> Mensaje:
    """
    Envía un mensaje en una conversación.

    Args:
        conversacion: Conversación donde enviar
        autor: Usuario que envía
        contenido: Contenido del mensaje
        gasto: Gasto asociado (opcional)
        archivo: Archivo adjunto (opcional)

    Returns:
        Mensaje creado

    Raises:
        ValueError: Si falta información requerida
    """
    if not contenido or not contenido.strip():
        raise ValueError("El contenido no puede estar vacío")

    # Si hay gasto asociado, actualizar su estado según el rol
    if gasto:
        if autor.role in ["MASTER", "EMPRESA"]:
            gasto.estado = "JUSTIFICAR"
            gasto.save()
        elif autor.role == "EMPLEADO" and archivo:
            gasto.comprobante = archivo
            gasto.estado = "PENDIENTE"
            gasto.save()

    # Crear mensaje
    mensaje = Mensaje.objects.create(
        conversacion=conversacion,
        autor=autor,
        contenido=contenido,
        archivo=archivo,
        gasto=gasto
    )

    return mensaje


def puede_participar_conversacion(usuario: CustomUser, conversacion: Conversacion) -> bool:
    """
    Verifica si un usuario puede participar en una conversación.

    Args:
        usuario: Usuario a verificar
        conversacion: Conversación a validar

    Returns:
        True si puede participar, False si no
    """
    return usuario in conversacion.participantes.all()


# ============================================================================
# QUERIES Y FILTROS
# ============================================================================

def obtener_mensajes_justificantes_por_rol(usuario: CustomUser) -> 'QuerySet[MensajeJustificante]':
    """
    Obtiene mensajes de justificantes según el rol del usuario.

    Args:
        usuario: Usuario que solicita

    Returns:
        QuerySet de MensajeJustificante
    """
    if usuario.role == 'MASTER':
        return MensajeJustificante.objects.all()
    elif usuario.role == 'EMPRESA':
        return MensajeJustificante.objects.filter(gasto__empresa__user=usuario)
    elif usuario.role == 'EMPLEADO':
        return MensajeJustificante.objects.filter(gasto__empleado__user=usuario)
    return MensajeJustificante.objects.none()


def obtener_conversaciones_usuario(usuario: CustomUser) -> 'QuerySet[Conversacion]':
    """
    Obtiene todas las conversaciones de un usuario.

    Args:
        usuario: Usuario a filtrar

    Returns:
        QuerySet de Conversacion
    """
    return Conversacion.objects.filter(participantes=usuario)


def obtener_mensajes_conversacion(conversacion: Conversacion) -> 'QuerySet[Mensaje]':
    """
    Obtiene todos los mensajes de una conversación.

    Args:
        conversacion: Conversación a filtrar

    Returns:
        QuerySet de Mensaje ordenado por fecha
    """
    return conversacion.mensajes.order_by('fecha_creacion')
