"""
Vistas para gestión de mensajería
"""
import os
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions, parsers
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import mimetypes

from users.models import Gasto, MensajeJustificante, Conversacion, CustomUser, Mensaje, Viaje
from users.serializers import MensajeJustificanteSerializer, ConversacionSerializer, MensajeSerializer
from users.common.exceptions import UnauthorizedAccessError

from .services import (
    solicitar_justificante,
    responder_justificante,
    cambiar_estado_justificante,
    puede_solicitar_justificante,
    puede_responder_justificante,
    puede_cambiar_estado_justificante,
    crear_conversacion,
    enviar_mensaje,
    puede_participar_conversacion,
    obtener_mensajes_justificantes_por_rol,
    obtener_conversaciones_usuario,
    obtener_mensajes_conversacion
)


# ============================================================================
# VISTAS DE MENSAJES JUSTIFICANTES
# ============================================================================

class SolicitarJustificanteView(APIView):
    """Permite a MASTER o EMPRESA solicitar justificante para un gasto"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, id=gasto_id)
        motivo = request.data.get("motivo", "").strip()

        # Verificar permisos
        if not puede_solicitar_justificante(request.user, gasto):
            raise UnauthorizedAccessError("No autorizado para este gasto")

        # Solicitar justificante
        try:
            solicitar_justificante(request.user, gasto, motivo)
            return Response(
                {"message": "Justificante solicitado correctamente"},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ListarMensajesView(generics.ListAPIView):
    """Lista mensajes de justificantes según el rol"""
    serializer_class = MensajeJustificanteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return obtener_mensajes_justificantes_por_rol(self.request.user)


class ResponderMensajeView(APIView):
    """Permite a un empleado responder una solicitud de justificante"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, mensaje_id):
        mensaje = get_object_or_404(MensajeJustificante, id=mensaje_id)

        # Verificar permisos
        if request.user.role != "EMPLEADO":
            raise UnauthorizedAccessError("Solo los empleados pueden responder mensajes")

        if not puede_responder_justificante(request.user, mensaje):
            raise UnauthorizedAccessError("No tienes permiso para responder este mensaje")

        # Responder
        respuesta = request.data.get("respuesta", "").strip()
        archivo = request.FILES.get("archivo")

        try:
            responder_justificante(mensaje, respuesta, archivo)
            return Response(
                {"message": "Respuesta guardada correctamente"},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CambiarEstadoJustificacionView(APIView):
    """Permite a MASTER o EMPRESA aprobar/rechazar un justificante"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, mensaje_id):
        mensaje = get_object_or_404(MensajeJustificante, id=mensaje_id)
        estado = request.data.get("estado")

        # Verificar permisos
        if not puede_cambiar_estado_justificante(request.user, mensaje):
            raise UnauthorizedAccessError("No autorizado")

        # Cambiar estado
        try:
            cambiar_estado_justificante(mensaje, estado)
            return Response(
                {"message": f"Justificante {estado}"},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DescargarArchivoMensajeView(APIView):
    """Descarga el archivo adjunto de un mensaje justificante"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, mensaje_id):
        mensaje = get_object_or_404(MensajeJustificante, id=mensaje_id)

        if not mensaje.archivo_justificante:
            return Response(
                {"error": "Este mensaje no tiene justificante adjunto"},
                status=status.HTTP_404_NOT_FOUND
            )

        archivo = mensaje.archivo_justificante
        mime_type, _ = mimetypes.guess_type(archivo.name)
        content_type = mime_type or 'application/octet-stream'

        response = FileResponse(archivo.open(), content_type=content_type)
        response['Content-Disposition'] = f"inline; filename=\"{archivo.name.split('/')[-1]}\""

        return response


# ============================================================================
# VISTAS DE CONVERSACIONES
# ============================================================================

class CrearConversacionView(APIView):
    """
    Crea una conversación nueva, ligada opcionalmente a un viaje o empleado.
    Solo MASTER o EMPRESA pueden iniciar conversaciones.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Verificar rol
        if user.role not in ["MASTER", "EMPRESA"]:
            raise UnauthorizedAccessError("Solo MASTER o EMPRESA pueden crear conversaciones")

        # Obtener parámetros
        viaje_id = request.data.get("viaje_id")
        empleado_id = request.data.get("empleado_id")

        # Obtener objetos si existen
        viaje = None
        empleado = None

        if viaje_id:
            viaje = get_object_or_404(Viaje, id=viaje_id)
        elif empleado_id:
            empleado = get_object_or_404(CustomUser, id=empleado_id, role="EMPLEADO")

        # Crear conversación
        try:
            conversacion = crear_conversacion(user, viaje=viaje, empleado=empleado)
            serializer = ConversacionSerializer(conversacion)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ListarConversacionesView(generics.ListAPIView):
    """Lista todas las conversaciones en las que participa el usuario"""
    serializer_class = ConversacionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return obtener_conversaciones_usuario(self.request.user)


class ListarMensajesByIdView(generics.ListAPIView):
    """Lista todos los mensajes de una conversación"""
    serializer_class = MensajeSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conv_id = self.kwargs.get('conversacion_id')
        conversacion = get_object_or_404(Conversacion, id=conv_id)

        # Validar que el usuario esté en la conversación
        if not puede_participar_conversacion(self.request.user, conversacion):
            return Mensaje.objects.none()

        return obtener_mensajes_conversacion(conversacion)


class EnviarMensajeView(APIView):
    """Envía un nuevo mensaje en una conversación existente"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conv_id = request.data.get("conversacion_id")
        contenido = request.data.get("contenido", "").strip()
        gasto_id = request.data.get("gasto_id")
        archivo = request.FILES.get("archivo")

        # Validar datos mínimos
        if not conv_id:
            return Response(
                {"error": "Falta conversacion_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener conversación
        conversacion = get_object_or_404(Conversacion, id=conv_id)

        # Verificar permisos
        if not puede_participar_conversacion(request.user, conversacion):
            raise UnauthorizedAccessError("No participas en esta conversación")

        # Obtener gasto si existe
        gasto = None
        if gasto_id:
            gasto = get_object_or_404(Gasto, id=gasto_id)

        # Enviar mensaje
        try:
            mensaje = enviar_mensaje(conversacion, request.user, contenido, gasto, archivo)
            return Response(
                MensajeSerializer(mensaje).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DescargarAdjuntoMensajeView(APIView):
    """Descarga el archivo adjunto de un mensaje de conversación"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, mensaje_id):
        mensaje = get_object_or_404(Mensaje, id=mensaje_id)

        # Validar permisos
        if not puede_participar_conversacion(request.user, mensaje.conversacion):
            raise UnauthorizedAccessError("No autorizado")

        if not mensaje.archivo:
            return Response(
                {"error": "No hay archivo adjunto"},
                status=status.HTTP_404_NOT_FOUND
            )

        archivo = mensaje.archivo
        mime_type, _ = mimetypes.guess_type(archivo.name)
        response = FileResponse(
            archivo.open(),
            content_type=mime_type or 'application/octet-stream'
        )
        filename = os.path.basename(archivo.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
