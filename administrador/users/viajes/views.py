"""
Vistas para gestión de viajes
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Viaje, EmpleadoProfile, EmpresaProfile, DiaViaje, Gasto
from users.serializers import ViajeSerializer, PendingTripSerializer, DiaViajeSerializer
from users.common.services import get_user_empleado, get_user_empresa
from users.common.exceptions import (
    EmpleadoProfileNotFoundError,
    EmpresaProfileNotFoundError,
    UnauthorizedAccessError
)

from .services import (
    validar_fechas,
    crear_viaje,
    procesar_revision_viaje,
    obtener_estadisticas_ciudades
)


class CrearViajeView(APIView):
    """Permite a los empleados crear un nuevo viaje"""
    authentication_classes = [TokenAuthentication]
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

        # Crear viaje
        try:
            viaje = crear_viaje(
                empleado=empleado,
                destino=request.data.get("destino"),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=request.data.get("motivo", ""),
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "MASTER":
            viajes = Viaje.objects.filter(estado="REVISADO")

        elif user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            viajes = Viaje.objects.filter(
                empleado__empresa=empresa,
                estado="REVISADO"
            )

        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            viajes = Viaje.objects.filter(
                empleado=empleado,
                estado="REVISADO"
            )

        else:
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PendingTripsByEmployeeView(APIView):
    """
    Lista viajes en revisión de un empleado.
    MASTER puede ver cualquier empleado;
    EMPRESA sólo los de su empresa;
    EMPLEADO ve sólo sus propios viajes.
    """
    authentication_classes = [TokenAuthentication]
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
            estado='EN_REVISION'
        )

        serializer = PendingTripSerializer(viajes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListarTodosLosViajesView(APIView):
    """Lista todos los viajes según el rol del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "MASTER":
            viajes = Viaje.objects.all()

        elif user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            viajes = Viaje.objects.filter(
                empleado__empresa=empresa
            )

        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            viajes = Viaje.objects.filter(empleado=empleado)

        else:
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PendingTripsDetailView(APIView):
    """Devuelve count + lista de viajes 'EN_REVISION', opcionalmente filtrado por empleado"""
    authentication_classes = [TokenAuthentication]
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
                estado="EN_REVISION"
            )

        else:
            # Sin filtro, cae en la lógica global
            if user.role == "MASTER":
                viajes_qs = Viaje.objects.filter(estado="EN_REVISION")

            elif user.role == "EMPRESA":
                empresa = get_user_empresa(user)
                if not empresa:
                    raise EmpresaProfileNotFoundError()
                viajes_qs = Viaje.objects.filter(
                    empleado__empresa=empresa,
                    estado="EN_REVISION"
                )

            else:  # EMPLEADO
                empleado = get_user_empleado(user)
                if not empleado:
                    raise EmpleadoProfileNotFoundError()
                viajes_qs = Viaje.objects.filter(
                    empleado=empleado,
                    estado="EN_REVISION"
                )

        serializer = PendingTripSerializer(viajes_qs, many=True)
        return Response({
            "count": viajes_qs.count(),
            "trips": serializer.data
        }, status=status.HTTP_200_OK)


class FinalizarRevisionViajeView(APIView):
    """Permite a MASTER o EMPRESA finalizar la revisión de un viaje"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, viaje_id):
        user = request.user
        motivo = request.data.get("motivo", "").strip()
        dias_data = request.data.get("dias", [])

        viaje = get_object_or_404(Viaje, id=viaje_id, estado='EN_REVISION')

        # Validación de permisos
        if user.role == 'EMPRESA':
            empresa = get_user_empresa(user)
            if not empresa or viaje.empresa != empresa:
                raise UnauthorizedAccessError("No autorizado para revisar este viaje")

        elif user.role != 'MASTER':
            raise UnauthorizedAccessError("Solo MASTER o EMPRESA pueden revisar viajes")

        # Procesar revisión
        try:
            resultado = procesar_revision_viaje(viaje, dias_data, motivo, user)
            return Response(
                {"message": "Revisión finalizada. Conversación creada si fue necesario."},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReabrirViajeView(APIView):
    """Permite reabrir un viaje revisado para recabar más información"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, viaje_id):
        viaje = get_object_or_404(Viaje, id=viaje_id)

        if viaje.estado != 'REVISADO':
            return Response(
                {"error": "Solo se pueden reabrir viajes en estado REVISADO"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if user.role == 'EMPRESA':
            empresa = get_object_or_404(EmpresaProfile, user=user)
            if viaje.empresa != empresa:
                raise UnauthorizedAccessError("No autorizado para reabrir este viaje")
        elif user.role != 'MASTER':
            raise UnauthorizedAccessError("Solo MASTER o EMPRESA pueden reabrir viajes")

        viaje.estado = 'EN_REVISION'
        viaje.save(update_fields=['estado'])

        viaje.dias.update(revisado=False)
        Gasto.objects.filter(viaje=viaje).exclude(estado='PENDIENTE').update(estado='PENDIENTE')

        return Response(
            {"message": "Viaje reabierto. Los días y gastos deberán revisarse nuevamente."},
            status=status.HTTP_200_OK
        )


class EmployeeCityStatsView(APIView):
    """Devuelve estadísticas de ciudades visitadas por un empleado (viajes revisados)"""
    authentication_classes = [TokenAuthentication]
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


class DiaViajeReviewView(APIView):
    """Permite aprobar o marcar gasto no exento para un día de viaje"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, dia_id):
        user = request.user
        dia = get_object_or_404(DiaViaje, id=dia_id)
        viaje = dia.viaje

        if viaje.estado != 'EN_REVISION':
            return Response(
                {'error': 'El viaje ya no se encuentra en revisión'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Permisos según rol
        if user.role == 'EMPRESA':
            empresa = get_object_or_404(EmpresaProfile, user=user)
            if viaje.empresa != empresa:
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'EMPLEADO':
            return Response({'error': 'Empleados no pueden validar días'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role != 'MASTER':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

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
            viaje.estado = 'REVISADO'
            viaje.save()

        return Response({'message': 'Día validado correctamente.'}, status=status.HTTP_200_OK)
