"""
Vistas para exportación de datos
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from users.models import Viaje, EmpresaProfile, EmpleadoProfile
from users.common.services import get_user_empresa, get_user_empleado
from users.common.exceptions import (
    EmpresaProfileNotFoundError,
    EmpleadoProfileNotFoundError,
    UnauthorizedAccessError
)

from .services import (
    generar_csv_viajes_master,
    generar_csv_viajes_empresa,
    generar_csv_viajes_con_gastos,
    generar_zip_viajes_con_gastos,
    obtener_viajes_para_exportacion
)


# ============================================================================
# VISTAS DE EXPORTACIÓN CSV
# ============================================================================

class ExportMasterCSVView(APIView):
    """Exporta los viajes de empleados de todas las empresas (MASTER only)"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "MASTER":
            raise UnauthorizedAccessError("Solo MASTER puede exportar todos los viajes")

        viajes = Viaje.objects.filter(estado="FINALIZADO").select_related(
            "empresa", "empleado"
        )

        csv_content = generar_csv_viajes_master(viajes)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="viajes_todas_empresas.csv"'
        response.write(csv_content)

        return response


class ExportEmpresaCSVView(APIView):
    """Exporta los viajes de empleados de la empresa logueada en formato CSV"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "EMPRESA":
            raise UnauthorizedAccessError("Solo EMPRESA puede usar esta exportación")

        empresa = get_user_empresa(request.user)
        if not empresa:
            raise EmpresaProfileNotFoundError()

        viajes = Viaje.objects.filter(
            empresa=empresa, estado="FINALIZADO"
        ).select_related("empleado")

        csv_content = generar_csv_viajes_empresa(viajes)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{empresa.nombre_empresa}_viajes.csv"'
        )
        response.write(csv_content)

        return response


class ExportViajesGastosView(APIView):
    """Exporta viajes con sus gastos asociados según el rol del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            viajes, filename_base = obtener_viajes_para_exportacion(request.user)
        except EmpresaProfile.DoesNotExist:
            raise EmpresaProfileNotFoundError()
        except EmpleadoProfile.DoesNotExist:
            raise EmpleadoProfileNotFoundError()

        csv_content = generar_csv_viajes_con_gastos(viajes)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{filename_base}_viajes_con_gastos.csv"'
        )
        response.write(csv_content)

        return response


class ExportEmpleadoIndividualView(APIView):
    """Exporta los viajes con gastos de un empleado específico"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empleado_id):
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)

        # Validar permisos
        if request.user.role == "EMPLEADO":
            if empleado.user != request.user:
                raise UnauthorizedAccessError("No puedes exportar datos de otros empleados")

        elif request.user.role == "EMPRESA":
            empresa = get_user_empresa(request.user)
            if not empresa or empleado.empresa != empresa:
                raise UnauthorizedAccessError("No puedes exportar datos de empleados de otras empresas")

        # MASTER puede ver cualquier empleado

        try:
            viajes, filename_base = obtener_viajes_para_exportacion(
                request.user,
                empleado_id=empleado_id
            )
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)

        csv_content = generar_csv_viajes_con_gastos(viajes)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{filename_base}_viajes_detallados.csv"'
        )
        response.write(csv_content)

        return response


# ============================================================================
# VISTAS DE EXPORTACIÓN ZIP
# ============================================================================

class ExportViajesGastosZipView(APIView):
    """Exporta viajes con gastos y archivos comprobantes en formato ZIP"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            viajes, filename_base = obtener_viajes_para_exportacion(request.user)
        except EmpresaProfile.DoesNotExist:
            raise EmpresaProfileNotFoundError()
        except EmpleadoProfile.DoesNotExist:
            raise EmpleadoProfileNotFoundError()

        # Generar ZIP
        zip_buffer = generar_zip_viajes_con_gastos(
            viajes,
            rol_usuario=request.user.role
        )

        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = (
            f'attachment; filename="{filename_base}_viajes_completos.zip"'
        )

        return response


class ExportEmpleadoIndividualZipView(APIView):
    """Exporta los viajes con gastos y archivos de un empleado específico en ZIP"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empleado_id):
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)

        # Validar permisos
        if request.user.role == 'EMPLEADO':
            if empleado.user != request.user:
                raise UnauthorizedAccessError("No puedes exportar datos de otros empleados")

        elif request.user.role == 'EMPRESA':
            empresa = get_user_empresa(request.user)
            if not empresa or empleado.empresa != empresa:
                raise UnauthorizedAccessError("No puedes exportar datos de empleados de otras empresas")

        # MASTER puede ver cualquier empleado

        try:
            viajes, filename_base = obtener_viajes_para_exportacion(
                request.user,
                empleado_id=empleado_id
            )
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)

        # Generar ZIP
        zip_buffer = generar_zip_viajes_con_gastos(
            viajes,
            rol_usuario=request.user.role
        )

        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = (
            f'attachment; filename="{filename_base}_viajes_detallados.zip"'
        )

        return response
