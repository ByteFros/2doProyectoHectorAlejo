from django.db.models import Count
from django.db.models.functions import TruncMonth

from .models import EmpleadoProfile, Viaje, EmpresaProfile, Notificacion
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from datetime import datetime, date
from .serializers import ViajeSerializer


class CrearViajeView(APIView):
    """ Permitimos a los empleados crear un nuevo viaje """
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

            # 🔄 Validar y convertir fechas
            fecha_inicio_str = data.get("fecha_inicio")
            fecha_fin_str = data.get("fecha_fin")

            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return Response({"error": "Formato de fecha inválido. Usa YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 🔒 Validar que fecha_fin >= fecha_inicio
            if fecha_fin < fecha_inicio:
                return Response({"error": "La fecha de fin no puede ser anterior a la fecha de inicio."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 🔁 Determinar estado inicial del viaje
            data["estado"] = "EN_CURSO" if fecha_inicio == date.today() else "PENDIENTE"

            # 🔍 Verificar conflicto con otros viajes
            conflicto_viajes = Viaje.objects.filter(
                empleado=empleado,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio,
                estado__in=["PENDIENTE", "EN_CURSO"]
            ).exists()

            if conflicto_viajes:
                return Response({"error": "Ya tienes un viaje programado en esas fechas."},
                                status=status.HTTP_400_BAD_REQUEST)

            # ✅ Crear viaje
            serializer = ViajeSerializer(data=data)
            if serializer.is_valid():
                viaje = serializer.save()

                # 🔔 Notificar a la empresa
                if empleado.empresa:
                    empresa_usuario = empleado.empresa.user
                    nombre_empleado = f"{empleado.nombre} {empleado.apellido}".strip()

                    Notificacion.objects.create(
                        tipo="VIAJE_SOLICITADO",
                        mensaje=f"{nombre_empleado} ha solicitado un viaje a {viaje.destino}.",
                        usuario_destino=empresa_usuario
                    )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado"}, status=status.HTTP_400_BAD_REQUEST)


class VerificarViajeEnCursoView(APIView):
    """ Verifica si un usuario tiene un viaje en curso """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
            viaje_en_curso = Viaje.objects.filter(empleado=empleado, estado="EN_CURSO").exists()
            return Response({"tiene_viaje_en_curso": viaje_en_curso}, status=status.HTTP_200_OK)

        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado"}, status=status.HTTP_400_BAD_REQUEST)


# ... el resto del código de las otras views no fue alterado ...


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

            """
            # 🔹 Verificar que el viaje está APROBADO
            if viaje.estado != "APROBADO":
                return Response({"error": "Solo puedes iniciar un viaje aprobado"}, status=status.HTTP_400_BAD_REQUEST)
            """

            # 🔹 Verificar que la fecha actual sea mayor o igual a la fecha de inicio

            if date.today() < viaje.fecha_inicio:
                return Response({"error": "Aún no puedes iniciar este viaje, la fecha de inicio no ha llegado"},
                                status=status.HTTP_400_BAD_REQUEST)

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


class CancelarViajeView(APIView):
    """Permite a un empleado cancelar un viaje antes de que comience"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            viaje = Viaje.objects.get(id=viaje_id, empleado__user=request.user)

            # 🔹 Solo se pueden cancelar viajes en estado PENDIENTE
            if viaje.estado != "PENDIENTE":
                return Response({"error": "Solo puedes cancelar un viaje que aún está pendiente"},
                                status=status.HTTP_400_BAD_REQUEST)

            viaje.estado = "CANCELADO"
            viaje.save()

            return Response({"message": "Viaje cancelado correctamente."}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "Viaje no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)


class ViajeEnCursoView(APIView):
    """Devuelve el viaje actual en curso del empleado autenticado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "EMPLEADO":
            return Response({"error": "Solo los empleados pueden acceder a esta vista."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado."},
                            status=status.HTTP_400_BAD_REQUEST)

        viaje_en_curso = Viaje.objects.filter(
            empleado=empleado,
            estado="EN_CURSO"
        ).order_by("-fecha_inicio").first()

        if not viaje_en_curso:
            return Response({"message": "No hay viajes en curso."}, status=status.HTTP_204_NO_CONTENT)

        serializer = ViajeSerializer(viaje_en_curso)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListarViajesFinalizadosView(APIView):
    """Lista los viajes finalizados según el rol del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 🔹 MASTER: ve todos los viajes finalizados
        if user.role == "MASTER":
            viajes = Viaje.objects.filter(estado="FINALIZADO")

        # 🔹 EMPRESA: ve los viajes de sus empleados
        elif user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(empleado__empresa=empresa, estado="FINALIZADO")
            except EmpresaProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empresa asociado"}, status=403)

        # 🔹 EMPLEADO: solo sus propios viajes
        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(empleado=empleado, estado="FINALIZADO")
            except EmpleadoProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empleado asociado"}, status=403)

        else:
            return Response({"error": "Rol de usuario no reconocido"}, status=403)

        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=200)

class ListarTodosLosViajesView(APIView):
    """Lista todos los viajes sin importar el estado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Devuelve todos los viajes en la base de datos"""
        if request.user.role not in ["EMPRESA", "MASTER", "EMPLEADO"]:
            return Response({"error": "No autorizado"}, status=403)

        viajes = Viaje.objects.all()
        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=200)
