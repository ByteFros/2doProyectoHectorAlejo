# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notas, Viaje, EmpleadoProfile
from .serializers import NotaViajeSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class NotaViajeListCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, viaje_id):
        """Listar notas del viaje (solo para empleados)"""
        empleado = EmpleadoProfile.objects.get(user=request.user)
        notas = Notas.objects.filter(viaje__id=viaje_id, empleado=empleado).order_by('-fecha_creacion')
        serializer = NotaViajeSerializer(notas, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, viaje_id):
        if request.user.role != "EMPLEADO":
            return Response({"error": "Solo los empleados pueden crear notas"}, status=403)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "Perfil de empleado no encontrado"}, status=404)

        # 🔒 Verifica que el viaje pertenece al empleado
        try:
            viaje = Viaje.objects.get(id=viaje_id, empleado=empleado)
        except Viaje.DoesNotExist:
            return Response({"error": "El viaje no existe o no te pertenece"}, status=403)

        data = request.data.copy()
        data["viaje"] = viaje.id  # Asigna explícitamente el viaje
        serializer = NotaViajeSerializer(data=data)

        if serializer.is_valid():
            serializer.save(empleado=empleado)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class NotaViajeDeleteView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, nota_id):
        try:
            nota = Notas.objects.get(id=nota_id, empleado__user=request.user)
            nota.delete()
            return Response({"message": "Nota eliminada"}, status=204)
        except Notas.DoesNotExist:
            return Response({"error": "Nota no encontrada o no tienes permisos"}, status=404)


