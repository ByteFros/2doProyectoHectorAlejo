"""
Vistas para gestión de viajes
"""
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Viaje, EmpleadoProfile, EmpresaProfile, DiaViaje, Gasto
from users.serializers import (
    ViajeSerializer,
    PendingTripSerializer,
    DiaViajeSerializer,
    ViajeWithGastosSerializer,
    EmpleadoProfileSerializer,
    EmpresaProfileSerializer,
    ViajeSnapshotSerializer,
    GastoSerializer,
    GastoSnapshotSerializer,
)
from users.common.services import (
    get_user_empleado,
    get_user_empresa,
    get_visible_viajes_queryset,
    get_visible_gastos_queryset,
)
from users.common.exceptions import (
    EmpleadoProfileNotFoundError,
    EmpresaProfileNotFoundError,
    UnauthorizedAccessError
)

from .services import (
    validar_fechas,
    crear_viaje,
    obtener_estadisticas_ciudades,
    cambiar_estado_viaje
)


def _ensure_can_review_viaje(user, viaje, empresa_cache=None):
    if user.role == 'EMPRESA':
        empresa = empresa_cache or get_object_or_404(EmpresaProfile, user=user)
        if viaje.empresa_id != empresa.id:
            raise UnauthorizedAccessError("No autorizado")
        return empresa
    if user.role == 'EMPLEADO':
        raise UnauthorizedAccessError("Empleados no pueden validar días")
    if user.role != 'MASTER':
        raise UnauthorizedAccessError("No autorizado")
    return None


class CrearViajeView(APIView):
    """Permite a los empleados crear un nuevo viaje"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "EMPLEADO":
            raise UnauthorizedAccessError("Solo empleados pueden crear viajes")

        empleado = get_user_empleado(request.user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        # Validar fechas
        try:
            fecha_inicio, fecha_fin = validar_fechas(
                request.data.get("fecha_inicio"),
                request.data.get("fecha_fin")
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        motivo = request.data.get("motivo")
        if not motivo:
            return Response(
                {"error": "El campo 'motivo' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear viaje
        try:
            viaje = crear_viaje(
                empleado=empleado,
                destino=request.data.get("destino"),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo,
                empresa_visitada=request.data.get("empresa_visitada", ""),
                ciudad=request.data.get("ciudad", ""),
                pais=request.data.get("pais", ""),
                es_internacional=request.data.get("es_internacional", False)
            )

            serializer = ViajeSerializer(viaje)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListarViajesRevisadosView(APIView):
    """Lista los viajes revisados según el rol del usuario"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        include = {
            part.strip().lower()
            for part in request.query_params.get('include', '').split(',')
            if part.strip()
        }
        include_gastos = 'gastos' in include

        visible_viajes = get_visible_viajes_queryset(user)

        if visible_viajes.uses_snapshot:
            snapshots = visible_viajes.queryset
            if include_gastos:
                snapshots = snapshots.prefetch_related('gastos_snapshot', 'gastos_snapshot__gasto')

            serializer = ViajeSnapshotSerializer(
                snapshots,
                many=True,
                context={'request': request, 'include_gastos': include_gastos}
            )
            data = serializer.data

        else:
            if user.role != "MASTER":
                raise UnauthorizedAccessError("Rol de usuario no reconocido")

            viajes = visible_viajes.queryset.filter(estado="REVISADO")

            serializer_class = ViajeWithGastosSerializer if include_gastos else ViajeSerializer
            if include_gastos:
                viajes = viajes.prefetch_related(
                    Prefetch(
                        'gasto_set',
                        queryset=Gasto.objects.select_related('empleado', 'empresa').order_by('fecha_gasto', 'id')
                    )
                )

            serializer = serializer_class(viajes, many=True, context={'request': request})
            data = serializer.data

        if user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            empresa = empleado.empresa if empleado else None
            employee_data = EmpleadoProfileSerializer(empleado, context={'request': request}).data if empleado else None
            company_data = EmpresaProfileSerializer(empresa, context={'request': request}).data if empresa else None

            for trip in data:
                trip.pop('empleado', None)
                trip.pop('empresa', None)

            return Response({
                "employee": employee_data,
                "company": company_data,
                "trips": data
            }, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_200_OK)


class PendingTripsByEmployeeView(APIView):
    """
    Lista viajes en revisión de un empleado.
    MASTER puede ver cualquier empleado;
    EMPRESA sólo los de su empresa;
    EMPLEADO ve sólo sus propios viajes.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empresa_id, empleado_id):
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)

        # Validación de permisos
        if request.user.role == 'EMPRESA':
            mi_empresa = get_user_empresa(request.user)
            if not mi_empresa or empleado.empresa_id != mi_empresa.id:
                raise UnauthorizedAccessError("No puedes ver viajes de empleados de otras empresas")

        elif request.user.role == 'EMPLEADO':
            if empleado.user != request.user:
                raise UnauthorizedAccessError("Solo puedes ver tus propios viajes")

        # MASTER pasa sin restricciones

        # Obtener viajes en revisión
        viajes = Viaje.objects.filter(
            empleado=empleado,
            estado__in=['EN_REVISION', 'REABIERTO']
        )

        serializer = PendingTripSerializer(viajes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListarTodosLosViajesView(APIView):
    """Lista todos los viajes según el rol del usuario"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        include = {
            part.strip().lower()
            for part in request.query_params.get('include', '').split(',')
            if part.strip()
        }
        include_gastos = 'gastos' in include
        visible_viajes = get_visible_viajes_queryset(user)
        data = []

        if visible_viajes.uses_snapshot:
            snapshots = visible_viajes.queryset
            if include_gastos:
                snapshots = snapshots.prefetch_related('gastos_snapshot', 'gastos_snapshot__gasto')

            snapshot_serializer = ViajeSnapshotSerializer(
                snapshots,
                many=True,
                context={'request': request, 'include_gastos': include_gastos}
            )
            data.extend(snapshot_serializer.data)

            if user.role == "EMPRESA":
                empresa = get_user_empresa(user)
                if not empresa:
                    raise EmpresaProfileNotFoundError()
                live_qs = Viaje.objects.filter(empleado__empresa=empresa).exclude(estado="REVISADO")
            elif user.role == "EMPLEADO":
                empleado = get_user_empleado(user)
                if not empleado:
                    raise EmpleadoProfileNotFoundError()
                live_qs = Viaje.objects.filter(empleado=empleado).exclude(estado="REVISADO")
            else:
                live_qs = Viaje.objects.none()

            serializer_class = ViajeWithGastosSerializer if include_gastos else ViajeSerializer
            if include_gastos:
                live_qs = live_qs.prefetch_related(
                    Prefetch(
                        'gasto_set',
                        queryset=Gasto.objects.select_related('empleado', 'empresa').order_by('fecha_gasto', 'id')
                    )
                )

            live_serializer = serializer_class(live_qs, many=True, context={'request': request})
            data.extend(live_serializer.data)

        else:
            if user.role != "MASTER":
                raise UnauthorizedAccessError("No autorizado")

            viajes_qs = visible_viajes.queryset
            serializer_class = ViajeWithGastosSerializer if include_gastos else ViajeSerializer
            if include_gastos:
                viajes_qs = viajes_qs.prefetch_related(
                    Prefetch(
                        'gasto_set',
                        queryset=Gasto.objects.select_related('empleado', 'empresa').order_by('fecha_gasto', 'id')
                    )
                )

            serializer = serializer_class(viajes_qs, many=True, context={'request': request})
            data = serializer.data

        data.sort(key=lambda trip: trip.get('fecha_inicio') or '', reverse=True)

        if user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            empresa = empleado.empresa if empleado else None
            employee_data = EmpleadoProfileSerializer(empleado, context={'request': request}).data if empleado else None
            company_data = EmpresaProfileSerializer(empresa, context={'request': request}).data if empresa else None

            for trip in data:
                trip.pop('empleado', None)
                trip.pop('empresa', None)

            return Response({
                "employee": employee_data,
                "company": company_data,
                "trips": data
            }, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_200_OK)


class PendingTripsDetailView(APIView):
    """Devuelve count + lista de viajes 'EN_REVISION' o 'REABIERTO', opcionalmente filtrado por empleado"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        empleado_id = request.query_params.get('empleado')

        # Si piden por empleado y tengo permiso, lo filtro
        if empleado_id:
            # Validar permisos
            if user.role == "EMPLEADO":
                mi_empleado = get_user_empleado(user)
                if not mi_empleado or int(empleado_id) != mi_empleado.id:
                    raise UnauthorizedAccessError("No autorizado")

            viajes_qs = Viaje.objects.filter(
                empleado_id=empleado_id,
                estado__in=["EN_REVISION", "REABIERTO"]
            )

        else:
            # Sin filtro, cae en la lógica global
            if user.role == "MASTER":
                viajes_qs = Viaje.objects.filter(estado__in=["EN_REVISION", "REABIERTO"])

            elif user.role == "EMPRESA":
                empresa = get_user_empresa(user)
                if not empresa:
                    raise EmpresaProfileNotFoundError()
                viajes_qs = Viaje.objects.filter(
                    empleado__empresa=empresa,
                    estado__in=["EN_REVISION", "REABIERTO"]
                )

            elif user.role == "EMPLEADO":
                empleado = get_user_empleado(user)
                if not empleado:
                    raise EmpleadoProfileNotFoundError()
                viajes_qs = Viaje.objects.filter(
                    empleado=empleado,
                    estado__in=["EN_REVISION", "REABIERTO"]
                )
            else:
                raise UnauthorizedAccessError("Rol de usuario no reconocido")

        serializer = PendingTripSerializer(viajes_qs, many=True)
        return Response({
            "count": viajes_qs.count(),
            "trips": serializer.data
        }, status=status.HTTP_200_OK)


class ViajeDetailView(APIView):
    """Permite eliminar un viaje según el rol del usuario."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, viaje_id):
        viaje = get_object_or_404(Viaje, id=viaje_id)
        user = request.user

        if user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado or viaje.empleado != empleado:
                raise UnauthorizedAccessError("Solo puedes eliminar tus propios viajes")
            if viaje.estado != "EN_REVISION":
                return Response(
                    {"error": "Solo puedes eliminar viajes que aún están en revisión"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa or viaje.empresa != empresa:
                raise UnauthorizedAccessError("No autorizado para eliminar este viaje")
            if viaje.estado != "EN_REVISION":
                return Response(
                    {"error": "Solo se pueden eliminar viajes que están en revisión"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif user.role == "MASTER":
            pass
        else:
            raise UnauthorizedAccessError("No autorizado para eliminar este viaje")

        viaje.delete()
        return Response(
            {"message": "Viaje eliminado correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )


class CambiarEstadoViajeView(APIView):
    """Permite a MASTER o EMPRESA cambiar el estado de un viaje (revisar o reabrir)"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, viaje_id):
        viaje = get_object_or_404(Viaje, id=viaje_id)
        target_state = request.data.get("target_state")
        dias_data = request.data.get("dias")

        user = request.user

        if user.role == 'EMPRESA':
            empresa = get_user_empresa(user)
            if not empresa or viaje.empresa != empresa:
                raise UnauthorizedAccessError("No autorizado para gestionar este viaje")
        elif user.role != 'MASTER':
            raise UnauthorizedAccessError("Solo MASTER o EMPRESA pueden gestionar estados de viajes")

        try:
            resultado = cambiar_estado_viaje(
                viaje=viaje,
                target_state=target_state,
                usuario=user,
                dias_data=dias_data
            )
            mensaje = "Estado del viaje actualizado correctamente."
            if resultado.get("nuevo_estado") == "REABIERTO":
                mensaje = "Viaje reabierto. Los días y gastos deberán revisarse nuevamente."
            elif resultado.get("nuevo_estado") == "REVISADO":
                mensaje = "Revisión finalizada."

            return Response(
                {"message": mensaje, "resultado": resultado},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeCityStatsView(APIView):
    """Devuelve estadísticas de ciudades visitadas por un empleado (viajes revisados)"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'EMPLEADO':
            raise UnauthorizedAccessError("Solo empleados pueden ver estas estadísticas")

        empleado = get_user_empleado(request.user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        estadisticas = obtener_estadisticas_ciudades(empleado)
        return Response(estadisticas, status=status.HTTP_200_OK)


class DiaViajeListView(APIView):
    """Lista los días de un viaje para revisión"""
    authentication_classes = [JWTAuthentication]
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
        serializer = DiaViajeSerializer(dias, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DiaViajeReviewView(APIView):
    """Permite aprobar o marcar gasto no exento para un día de viaje"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, dia_id):
        user = request.user
        dia = get_object_or_404(DiaViaje, id=dia_id)
        viaje = dia.viaje

        if viaje.estado not in ['EN_REVISION', 'REABIERTO']:
            return Response(
                {'error': 'El viaje ya no se encuentra en revisión'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            _ensure_can_review_viaje(user, viaje)
        except UnauthorizedAccessError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        exento = request.data.get('exento')
        if not isinstance(exento, bool):
            return Response({'error': 'Campo "exento" inválido. Debe ser true o false.'}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar día y gastos
        dia.exento = exento
        dia.revisado = True
        dia.save()
        nuevo_estado = 'APROBADO' if exento else 'RECHAZADO'
        dia.gastos.update(estado=nuevo_estado)

        return Response({'message': 'Día validado correctamente.'}, status=status.HTTP_200_OK)


class DiaViajeBatchReviewView(APIView):
    """Permite validar múltiples días de viaje en una sola petición."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        dia_ids = request.data.get('dia_ids')
        exento = request.data.get('exento')

        if not isinstance(dia_ids, list) or not dia_ids:
            return Response({'error': 'dia_ids debe ser una lista con al menos un elemento'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dia_ids = [int(d) for d in dia_ids]
        except (TypeError, ValueError):
            return Response({'error': 'Todos los valores en dia_ids deben ser enteros'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(exento, bool):
            return Response({'error': 'Campo "exento" inválido. Debe ser true o false.'}, status=status.HTTP_400_BAD_REQUEST)

        dias_qs = DiaViaje.objects.filter(id__in=dia_ids).select_related('viaje__empresa')
        dias = list(dias_qs)
        expected = len(set(dia_ids))
        if len(dias) != expected:
            existentes = {dia.id for dia in dias}
            faltantes = [str(_id) for _id in dia_ids if _id not in existentes]
            return Response({'error': f"No se encontraron los siguientes días: {', '.join(faltantes)}"}, status=status.HTTP_404_NOT_FOUND)

        empresa_cache = None
        try:
            if request.user.role == 'EMPRESA':
                empresa_cache = get_object_or_404(EmpresaProfile, user=request.user)
                for dia in dias:
                    _ensure_can_review_viaje(request.user, dia.viaje, empresa_cache)
            else:
                for dia in dias:
                    _ensure_can_review_viaje(request.user, dia.viaje)
        except UnauthorizedAccessError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        estado_gasto = 'APROBADO' if exento else 'RECHAZADO'

        with transaction.atomic():
            DiaViaje.objects.filter(id__in=dia_ids).update(exento=exento, revisado=True)
            Gasto.objects.filter(dia_id__in=dia_ids).update(estado=estado_gasto)

        return Response(
            {
                'message': f'Se actualizaron {len(dias)} días de viaje',
                'count': len(dias),
                'estado_gastos': estado_gasto
            },
            status=status.HTTP_200_OK
        )
