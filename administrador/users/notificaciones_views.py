from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notificacion
from .serializers import NotificacionSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class ListaNotificacionesView(APIView):
    """Devuelve las notificaciones del usuario autenticado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notificaciones = Notificacion.objects.filter(usuario_destino=request.user, leida=False).order_by("-fecha_creacion")
        serializer = NotificacionSerializer(notificaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """Marca todas las notificaciones como leídas"""
        Notificacion.objects.filter(usuario_destino=request.user, leida=False).update(leida=True)
        return Response({"message": "Notificaciones marcadas como leídas"}, status=status.HTTP_200_OK)


class CrearNotificacionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Crea una notificación y la envía vía WebSockets"""
        data = request.data
        tipo = data.get("tipo")
        mensaje = data.get("mensaje")
        usuario_destino_id = data.get("usuario_destino")

        if not tipo or not mensaje or not usuario_destino_id:
            return Response({"error": "Datos incompletos"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario_destino = User.objects.get(id=usuario_destino_id)
        except User.DoesNotExist:
            return Response({"error": "Usuario destino no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        notificacion = Notificacion.objects.create(
            tipo=tipo,
            mensaje=mensaje,
            usuario_destino=usuario_destino
        )

        serializer = NotificacionSerializer(notificacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
