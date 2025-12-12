"""
Vistas para gestión de gastos
"""
import mimetypes

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.common.exceptions import (
    EmpleadoProfileNotFoundError,
    EmpresaProfileNotFoundError,
    UnauthorizedAccessError,
)
from users.common.services import (
    get_user_empleado,
    get_user_empresa,
    get_visible_gastos_queryset,
    get_visible_viajes_queryset,
)
from users.models import Gasto, Viaje
from users.serializers import GastoSerializer, GastoSnapshotSerializer

from .services import (
    aprobar_rechazar_gasto,
    eliminar_gasto,
    obtener_gastos_por_rol,
    puede_gestionar_gasto,
    puede_modificar_gasto,
    validar_viaje_para_gasto,
)


class CrearGastoView(APIView):
    """Permite a un empleado registrar un gasto en un viaje"""
    authentication_classes = [JWTAuthentication]
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

        serializer = GastoSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            gasto = serializer.save()
            return Response(
                GastoSerializer(gasto, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AprobarRechazarGastoView(APIView):
    """Permite a una EMPRESA o MASTER aprobar o rechazar gastos"""
    authentication_classes = [JWTAuthentication]
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "MASTER":
            gastos = obtener_gastos_por_rol(user)
            serializer = GastoSerializer(gastos, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            live_qs = Gasto.objects.filter(empresa=empresa).exclude(viaje__estado="REVISADO")

        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            live_qs = Gasto.objects.filter(empleado=empleado).exclude(viaje__estado="REVISADO")

        else:
            raise UnauthorizedAccessError("No autorizado")

        visible_viajes = get_visible_viajes_queryset(user)

        snapshot_data = []
        if visible_viajes.uses_snapshot:
            snapshot_qs = get_visible_gastos_queryset(visible_viajes).select_related('gasto', 'viaje_snapshot')
            snapshot_serializer = GastoSnapshotSerializer(snapshot_qs, many=True, context={'request': request})
            snapshot_data = snapshot_serializer.data

        live_serializer = GastoSerializer(live_qs, many=True, context={'request': request})
        live_data = live_serializer.data

        combined = snapshot_data + list(live_data)
        combined.sort(key=lambda item: item.get('fecha_solicitud') or '', reverse=True)

        return Response(combined, status=status.HTTP_200_OK)


class GastoUpdateDeleteView(APIView):
    """Permite a un empleado actualizar o eliminar sus propios gastos"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, id=gasto_id)

        # Verificar permisos
        if not puede_modificar_gasto(request.user, gasto):
            raise UnauthorizedAccessError("No puedes modificar este gasto")

        serializer = GastoSerializer(gasto, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                GastoSerializer(gasto, context={'request': request}).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, id=gasto_id)

        # Verificar permisos
        if not puede_modificar_gasto(request.user, gasto):
            raise UnauthorizedAccessError("No puedes eliminar este gasto")

        if gasto.viaje and gasto.viaje.estado == "REABIERTO":
            return Response(
                {"error": "No puedes eliminar gastos mientras el viaje está reabierto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        eliminar_gasto(gasto)
        return Response(
            {"message": "Gasto eliminado correctamente"},
            status=status.HTTP_200_OK
        )


class GastoComprobanteDownloadView(APIView):
    """Permite descargar el comprobante de un gasto"""
    authentication_classes = [JWTAuthentication]
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
