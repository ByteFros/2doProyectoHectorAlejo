import csv

from django.http import HttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from users.models import Viaje


class ExportMasterCSVView(APIView):
    """Exporta los viajes de empleados de todas las empresas (MASTER only)."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'MASTER':
            return HttpResponse("No autorizado", status=403)

        viajes = Viaje.objects.filter(
            estado='FINALIZADO'
        ).select_related('empresa', 'empleado')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="viajes_todas_empresas.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Empresa', 'Empleado', 'Destino', 'Fecha Inicio', 'Fecha Fin', 'Días Exentos', 'Días No Exentos', 'Motivo'])

        for viaje in viajes:
            dias = viaje.dias.all()
            writer.writerow([
                viaje.empresa.nombre_empresa,
                f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                viaje.destino,
                viaje.fecha_inicio.strftime('%Y-%m-%d'),
                viaje.fecha_fin.strftime('%Y-%m-%d'),
                dias.filter(exento=True).count(),
                dias.filter(exento=False).count(),
                viaje.motivo.replace('\n', ' ').strip()
            ])

        return response

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.http import HttpResponse
from .models import EmpresaProfile, Viaje, DiaViaje
import csv

class ExportEmpresaCSVView(APIView):
    """Exporta los viajes de empleados de la empresa logueada en formato CSV."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'EMPRESA':
            return HttpResponse("No autorizado", status=403)

        try:
            empresa = EmpresaProfile.objects.get(user=request.user)
        except EmpresaProfile.DoesNotExist:
            return HttpResponse("No tienes perfil de empresa asociado", status=403)

        viajes = Viaje.objects.filter(
            empresa=empresa,
            estado='FINALIZADO'
        ).select_related('empleado')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{empresa.nombre_empresa}_viajes.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Empleado', 'Destino', 'Fecha Inicio', 'Fecha Fin', 'Días Exentos', 'Días No Exentos', 'Motivo'])

        for viaje in viajes:
            dias = viaje.dias.all()
            writer.writerow([
                f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                viaje.destino,
                viaje.fecha_inicio.strftime('%Y-%m-%d'),
                viaje.fecha_fin.strftime('%Y-%m-%d'),
                dias.filter(exento=True).count(),
                dias.filter(exento=False).count(),
                viaje.motivo.replace('\n', ' ').strip()
            ])

        return response

