"""
Vistas para gestión de mensajería (conversaciones entre usuarios)
"""
import os
import mimetypes

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Conversacion, CustomUser, Mensaje
from users.serializers import ConversacionSerializer, MensajeSerializer
from users.common.exceptions import UnauthorizedAccessError
from .utils import (
    get_target_user_or_400,
    get_existing_conversation,
    create_conversation,
)


def puede_participar_conversacion(usuario: CustomUser, conversacion: Conversacion) -> bool:
    """Verifica si un usuario participa en la conversación"""
    return conversacion.participantes.filter(id=usuario.id).exists()


def enviar_mensaje(
    conversacion: Conversacion,
    autor: CustomUser,
    contenido: str,
    archivo=None
) -> Mensaje:
    """Crea un mensaje dentro de una conversación"""
    if not contenido or not contenido.strip():
        raise ValueError("El contenido no puede estar vacío")

    return Mensaje.objects.create(
        conversacion=conversacion,
        autor=autor,
        contenido=contenido,
        archivo=archivo
    )


def obtener_conversaciones_usuario(usuario: CustomUser):
    return Conversacion.objects.filter(participantes=usuario)


def obtener_mensajes_conversacion(conversacion: Conversacion):
    return conversacion.mensajes.order_by('fecha_creacion')

class CrearConversacionView(APIView):
    """Crea una conversación entre el usuario autenticado y otro usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        target_user_id = request.data.get("user_id")
        if not target_user_id:
            return Response({"error": "Debes indicar user_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = get_target_user_or_400(user, int(target_user_id))
        except UnauthorizedAccessError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError:
            return Response({"error": "user_id inválido"}, status=status.HTTP_400_BAD_REQUEST)

        existing = get_existing_conversation(user, target_user)
        if existing:
            return Response(
                {"error": "Ya existe una conversación con este usuario"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversacion = create_conversation(user, target_user)

        serializer = ConversacionSerializer(conversacion, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListarConversacionesView(generics.ListAPIView):
    """Lista todas las conversaciones en las que participa el usuario"""
    serializer_class = ConversacionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return obtener_conversaciones_usuario(self.request.user).prefetch_related('mensajes', 'participantes')


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

        # Enviar mensaje
        try:
            mensaje = enviar_mensaje(conversacion, request.user, contenido, archivo)
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
