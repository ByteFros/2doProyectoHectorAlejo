"""
Vistas para gestión de viajes
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Viaje, EmpleadoProfile, EmpresaProfile, DiaViaje
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
    obtener_estadisticas_ciudades,
    cambiar_estado_viaje
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
            estado__in=['EN_REVISION', 'REABIERTO']
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
    """Devuelve count + lista de viajes 'EN_REVISION' o 'REABIERTO', opcionalmente filtrado por empleado"""
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


class CambiarEstadoViajeView(APIView):
    """Permite a MASTER o EMPRESA cambiar el estado de un viaje (revisar o reabrir)"""
    authentication_classes = [TokenAuthentication]
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
        serializer = DiaViajeSerializer(dias, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DiaViajeReviewView(APIView):
    """Permite aprobar o marcar gasto no exento para un día de viaje"""
    authentication_classes = [TokenAuthentication]
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
        nuevo_estado = 'APROBADO' if exento else 'RECHAZADO'
        dia.gastos.update(estado=nuevo_estado)

        return Response({'message': 'Día validado correctamente.'}, status=status.HTTP_200_OK)
