"""
Vistas para gestión de notificaciones
"""
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Notificacion
from users.serializers import NotificacionSerializer

User = get_user_model()


class ListaNotificacionesView(APIView):
    """Lista las notificaciones del usuario autenticado y permite marcarlas como leídas"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtiene las notificaciones no leídas del usuario"""
        notificaciones = Notificacion.objects.filter(
            usuario_destino=request.user,
            leida=False
        ).order_by("-fecha_creacion")

        serializer = NotificacionSerializer(notificaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """Marca todas las notificaciones del usuario como leídas"""
        notificaciones_actualizadas = Notificacion.objects.filter(
            usuario_destino=request.user,
            leida=False
        ).update(leida=True)

        return Response(
            {
                "message": "Notificaciones marcadas como leídas",
                "count": notificaciones_actualizadas
            },
            status=status.HTTP_200_OK
        )


class CrearNotificacionView(APIView):
    """Crea una notificación para un usuario específico"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Crea una notificación y la envía al usuario destino"""
        tipo = request.data.get("tipo")
        mensaje = request.data.get("mensaje")
        usuario_destino_id = request.data.get("usuario_destino")

        # Validar datos requeridos
        if not all([tipo, mensaje, usuario_destino_id]):
            return Response(
                {"error": "Datos incompletos. Se requieren: tipo, mensaje y usuario_destino"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que el usuario destino existe
        usuario_destino = get_object_or_404(User, id=usuario_destino_id)

        # Crear notificación
        notificacion = Notificacion.objects.create(
            tipo=tipo,
            mensaje=mensaje,
            usuario_destino=usuario_destino
        )

        serializer = NotificacionSerializer(notificacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
