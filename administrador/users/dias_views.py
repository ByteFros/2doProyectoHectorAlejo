from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Viaje, DiaViaje, EmpresaProfile
from .serializers import DiaViajeSerializer


class DiaViajeListView(APIView):
    """Lista los días de un viaje para revisión"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, viaje_id):
        user = request.user
        viaje = get_object_or_404(Viaje, id=viaje_id)

        # Permisos según rol
        if user.role == 'EMPRESA':
            empresa = get_object_or_404(EmpresaProfile, user=user)
            if viaje.empresa != empresa:
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'EMPLEADO':
            if viaje.empleado.user != user:
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role != 'MASTER':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        dias = viaje.dias.prefetch_related('gastos')
        serializer = DiaViajeSerializer(dias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DiaViajeUpdateView(APIView):
    """Permite aprobar o exentar un día de viaje"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id, dia_id):
        user = request.user
        viaje = get_object_or_404(Viaje, id=viaje_id, estado='EN_REVISION')

        # Permisos según rol
        if user.role == 'EMPRESA':
            empresa = get_object_or_404(EmpresaProfile, user=user)
            if viaje.empresa != empresa:
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'EMPLEADO':
            return Response({'error': 'Empleados no pueden validar días'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role != 'MASTER':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        dia = get_object_or_404(DiaViaje, id=dia_id, viaje=viaje)
        exento = request.data.get('exento')
        if not isinstance(exento, bool):
            return Response({'error': 'Campo "exento" inválido. Debe ser true o false.'}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar día y gastos
        dia.exento = exento
        dia.revisado = True
        dia.save()
        nuevo_estado = 'RECHAZADO' if exento else 'APROBADO'
        dia.gastos.update(estado=nuevo_estado)

        # Si todos los días están revisados, finalizar el viaje
        if not viaje.dias.filter(revisado=False).exists():
            viaje.estado = 'FINALIZADO'
            viaje.save()

        return Response({'message': 'Día validado correctamente.'}, status=status.HTTP_200_OK)
