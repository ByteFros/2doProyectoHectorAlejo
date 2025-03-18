from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import EmpleadoProfile, Viaje, EmpresaProfile, Notificacion
from .serializers import ViajeSerializer
from datetime import date


class CrearViajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
            data = request.data.copy()
            data["empleado_id"] = empleado.id
            data["empresa_id"] = empleado.empresa.id

            # 🔹 Verificar si ya existe un viaje pendiente con los mismos datos
            viaje_existente = Viaje.objects.filter(
                empleado=empleado,
                destino=data.get("destino"),
                fecha_inicio=data.get("fecha_inicio"),
                fecha_fin=data.get("fecha_fin"),
                estado="PENDIENTE"
            ).exists()

            if viaje_existente:
                return Response({"error": "Ya existe un viaje pendiente con los mismos datos."},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = ViajeSerializer(data=data)
            if serializer.is_valid():
                viaje = serializer.save()

                # 🔹 Crear una notificación para la empresa o el usuario MASTER
                if empleado.empresa:
                    empresa_usuario = empleado.empresa.user
                    nombre_empleado = f"{empleado.nombre} {empleado.apellido}".strip()

                    notificacion = Notificacion.objects.create(
                        tipo="VIAJE_SOLICITADO",
                        mensaje=f"{nombre_empleado} ha solicitado un viaje a {viaje.destino}.",
                        usuario_destino=empresa_usuario
                    )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado"}, status=status.HTTP_400_BAD_REQUEST)

class AprobarRechazarViajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        try:
            viaje = Viaje.objects.get(id=viaje_id)
            empresa = EmpresaProfile.objects.get(user=request.user)

            if viaje.empresa != empresa:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

            nuevo_estado = request.data.get("estado")  # "APROBADO" o "RECHAZADO"
            if nuevo_estado not in ["APROBADO", "RECHAZADO"]:
                return Response({"error": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST)

            viaje.estado = nuevo_estado
            viaje.save()

            mensaje = f"Tu viaje a {viaje.destino} ha sido {nuevo_estado.lower()}."
            if nuevo_estado == "RECHAZADO":
                motivo = request.data.get("motivo", "Sin motivo especificado")
                mensaje += f" Motivo: {motivo}"

            # 🔹 Crear notificación para el empleado
            notificacion = Notificacion.objects.create(
                tipo=f"VIAJE_{nuevo_estado}",
                mensaje=mensaje,
                usuario_destino=viaje.empleado.user
            )

            return Response({"message": f"Viaje {nuevo_estado.lower()} correctamente."}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "El viaje no existe"}, status=status.HTTP_404_NOT_FOUND)
        except EmpresaProfile.DoesNotExist:
            return Response({"error": "No tienes perfil de empresa"}, status=status.HTTP_403_FORBIDDEN)


class IniciarViajeView(APIView):
    """Permite a un empleado iniciar un viaje aprobado cuando llega la fecha de inicio"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            viaje = Viaje.objects.get(id=viaje_id, empleado__user=request.user)

            # 🔹 Verificar que el viaje está APROBADO
            if viaje.estado != "APROBADO":
                return Response({"error": "Solo puedes iniciar un viaje aprobado"}, status=status.HTTP_400_BAD_REQUEST)

            # 🔹 Verificar que la fecha actual sea mayor o igual a la fecha de inicio

            """if date.today() < viaje.fecha_inicio:
                return Response({"error": "Aún no puedes iniciar este viaje, la fecha de inicio no ha llegado"},
                                status=status.HTTP_400_BAD_REQUEST)"""

            # 🔹 Cambiar estado del viaje a EN_CURSO
            viaje.estado = "EN_CURSO"
            viaje.save()
            return Response({"message": "Viaje iniciado correctamente"}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "Viaje no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)

class FinalizarViajeView(APIView):
    """Permite a un empleado finalizar un viaje en curso"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            viaje = Viaje.objects.get(id=viaje_id, empleado__user=request.user)

            if viaje.estado != "EN_CURSO":
                return Response({"error": "Solo puedes finalizar un viaje en curso"},
                                status=status.HTTP_400_BAD_REQUEST)

            viaje.estado = "FINALIZADO"
            viaje.save()
            return Response({"message": "Viaje finalizado correctamente."}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "Viaje no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)

class ListarViajesPendientesView(APIView):
    """Lista las solicitudes de viaje pendientes para aprobación"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "MASTER":
            # 🔹 El usuario MASTER puede ver todas las solicitudes de viaje
            viajes_pendientes = Viaje.objects.filter(estado="PENDIENTE")

        elif request.user.role == "EMPRESA":
            # 🔹 El usuario EMPRESA solo ve las solicitudes de sus empleados
            empresa = EmpresaProfile.objects.filter(user=request.user).first()
            if not empresa:
                return Response({"error": "No tienes una empresa asociada"}, status=403)

            viajes_pendientes = Viaje.objects.filter(estado="PENDIENTE", empresa=empresa)

        else:
            return Response({"error": "No autorizado"}, status=403)

        serializer = ViajeSerializer(viajes_pendientes, many=True)
        return Response(serializer.data, status=200)

class ListarViajesAprobadosView(APIView):
    """lista los viajes aprobados del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            empleado = request.user.empleado_profile
        except AttributeError:
            return Response({"error": "No tienes un perfil de empleado"}, status=403)

        viajes_aprobados = Viaje.objects.filter(empleado=empleado, estado="APROBADO")

        serializer = ViajeSerializer(viajes_aprobados, many=True)
        return Response(serializer.data, status=200)

class ListarViajesFinalizadosView(APIView):
    """lista los viajes aprobados del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            empleado = request.user.empleado_profile
        except AttributeError:
            return Response({"error": "No tienes un perfil de empleado"}, status=403)

        viajes_aprobados = Viaje.objects.filter(empleado=empleado, estado="FINALIZADO")

        serializer = ViajeSerializer(viajes_aprobados, many=True)
        return Response(serializer.data, status=200)

class ListarTodosLosViajesView(APIView):
    """Lista todos los viajes sin importar el estado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Devuelve todos los viajes en la base de datos"""
        if request.user.role not in ["EMPRESA", "MASTER"]:
            return Response({"error": "No autorizado"}, status=403)

        viajes = Viaje.objects.all()
        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=200)