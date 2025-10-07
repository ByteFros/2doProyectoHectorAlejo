"""
Vistas para gestión de gastos
"""
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
import mimetypes

from users.models import Gasto, Viaje
from users.serializers import GastoSerializer
from users.common.services import get_user_empleado, get_user_empresa
from users.common.exceptions import (
    EmpleadoProfileNotFoundError,
    EmpresaProfileNotFoundError,
    UnauthorizedAccessError
)

from .services import (
    validar_viaje_para_gasto,
    crear_gasto,
    actualizar_gasto,
    aprobar_rechazar_gasto,
    eliminar_gasto,
    puede_gestionar_gasto,
    puede_modificar_gasto,
    obtener_gastos_por_rol
)


class CrearGastoView(APIView):
    """Permite a un empleado registrar un gasto en un viaje"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if request.user.role != "EMPLEADO":
            raise UnauthorizedAccessError("Solo los empleados pueden registrar gastos")

        empleado = get_user_empleado(request.user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        # Obtener y validar viaje
        viaje_id = request.data.get("viaje_id")
        viaje = get_object_or_404(Viaje, id=viaje_id)

        try:
            validar_viaje_para_gasto(viaje)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Crear gasto usando serializer
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data.copy()
        data["empleado_id"] = empleado.id
        data["empresa_id"] = empleado.empresa.id

        serializer = GastoSerializer(data=data)

        if serializer.is_valid():
            gasto = serializer.save()
            return Response(
                GastoSerializer(gasto).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AprobarRechazarGastoView(APIView):
    """Permite a una EMPRESA o MASTER aprobar o rechazar gastos"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, gasto_id):
        user = request.user
        gasto = get_object_or_404(Gasto, id=gasto_id)
        nuevo_estado = request.data.get("estado")

        # Verificar permisos
        if not puede_gestionar_gasto(user, gasto):
            raise UnauthorizedAccessError("No tienes permiso para gestionar este gasto")

        # Aprobar o rechazar
        try:
            aprobar_rechazar_gasto(gasto, nuevo_estado)
            return Response(
                {"message": "Estado del gasto actualizado correctamente"},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GastoListView(APIView):
    """Vista para listar los gastos con detalles de los viajes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        gastos = obtener_gastos_por_rol(request.user)

        if gastos is None:
            raise UnauthorizedAccessError("No autorizado")

        serializer = GastoSerializer(gastos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GastoUpdateDeleteView(APIView):
    """Permite a un empleado actualizar o eliminar sus propios gastos"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, id=gasto_id)

        # Verificar permisos
        if not puede_modificar_gasto(request.user, gasto):
            raise UnauthorizedAccessError("No puedes modificar este gasto")

        serializer = GastoSerializer(gasto, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, id=gasto_id)

        # Verificar permisos
        if not puede_modificar_gasto(request.user, gasto):
            raise UnauthorizedAccessError("No puedes eliminar este gasto")

        eliminar_gasto(gasto)
        return Response(
            {"message": "Gasto eliminado correctamente"},
            status=status.HTTP_200_OK
        )


class GastoComprobanteDownloadView(APIView):
    """Permite descargar el comprobante de un gasto"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, id=gasto_id)

        if not gasto.comprobante:
            raise Http404("No hay archivo para este gasto")

        file_path = gasto.comprobante.path
        content_type, _ = mimetypes.guess_type(file_path)

        response = FileResponse(
            gasto.comprobante.open(),
            content_type=content_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'inline; filename="{gasto.comprobante.name}"'
        return response
