"""
Vistas para gestión de notas de viajes
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Notas, Viaje, EmpleadoProfile
from users.serializers import NotaViajeSerializer
from users.common.services import get_user_empleado
from users.common.exceptions import (
    EmpleadoProfileNotFoundError,
    UnauthorizedAccessError
)


class NotaViajeListCreateView(APIView):
    """Lista y crea notas para un viaje específico"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, viaje_id):
        """Listar notas del viaje (solo para empleados)"""
        if request.user.role != 'EMPLEADO':
            raise UnauthorizedAccessError("Solo empleados pueden ver notas")

        empleado = get_user_empleado(request.user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        # Verificar que el viaje pertenece al empleado
        viaje = get_object_or_404(Viaje, id=viaje_id, empleado=empleado)

        notas = Notas.objects.filter(
            viaje=viaje,
            empleado=empleado
        ).order_by('-fecha_creacion')

        serializer = NotaViajeSerializer(notas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, viaje_id):
        """Crear una nota para el viaje"""
        if request.user.role != "EMPLEADO":
            raise UnauthorizedAccessError("Solo empleados pueden crear notas")

        empleado = get_user_empleado(request.user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        # Verificar que el viaje pertenece al empleado
        viaje = get_object_or_404(Viaje, id=viaje_id, empleado=empleado)

        data = request.data.copy()
        data["viaje"] = viaje.id
        serializer = NotaViajeSerializer(data=data)

        if serializer.is_valid():
            serializer.save(empleado=empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotaViajeDeleteView(APIView):
    """Elimina una nota de viaje"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, nota_id):
        """Eliminar una nota (solo el dueño puede eliminarla)"""
        if request.user.role != 'EMPLEADO':
            raise UnauthorizedAccessError("Solo empleados pueden eliminar notas")

        empleado = get_user_empleado(request.user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        nota = get_object_or_404(Notas, id=nota_id, empleado=empleado)
        nota.delete()

        return Response(
            {"message": "Nota eliminada correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )
