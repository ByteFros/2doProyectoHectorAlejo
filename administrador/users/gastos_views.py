from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Gasto, EmpleadoProfile, EmpresaProfile, Viaje
from .serializers import GastoSerializer


from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.parsers import MultiPartParser, FormParser

class CrearGastoView(APIView):
    """Permite a un empleado registrar un gasto en un viaje aprobado o finalizado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # ✅ Asegura que acepta archivos opcionales

    def post(self, request):
        """Registrar un nuevo gasto"""
        if request.user.role != "EMPLEADO":
            return Response({"error": "Solo los empleados pueden registrar gastos"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
            data = request.data.copy()
            data["empleado_id"] = empleado.id
            data["empresa_id"] = empleado.empresa.id

            # 🔥 Verificar que el viaje existe y está en el estado correcto
            viaje_id = data.get("viaje_id")
            try:
                viaje = Viaje.objects.get(id=viaje_id)
                if viaje.estado not in ["APROBADO", "EN_CURSO", "FINALIZADO"]:
                    return Response({"error": "Solo puedes registrar gastos en viajes aprobados o finalizados"}, status=400)
            except Viaje.DoesNotExist:
                return Response({"error": "El viaje no existe"}, status=404)

            serializer = GastoSerializer(data=data)

            if serializer.is_valid():
                gasto = serializer.save()
                return Response(GastoSerializer(gasto).data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado"}, status=status.HTTP_400_BAD_REQUEST)


class AprobarRechazarGastoView(APIView):
    """Permite a una EMPRESA o MASTER aprobar o rechazar gastos"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, gasto_id):
        """Aprobar o rechazar un gasto"""
        user = request.user

        try:
            gasto = Gasto.objects.get(id=gasto_id)
            estado = request.data.get("estado")

            if estado not in ["APROBADO", "RECHAZADO"]:
                return Response({"error": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST)

            # 🔹 Si es MASTER, puede aprobar/rechazar cualquier gasto
            if user.role == "MASTER":
                gasto.estado = estado
                gasto.save()
                return Response({"message": "Estado del gasto actualizado correctamente"}, status=status.HTTP_200_OK)

            # 🔹 Si es EMPRESA, solo puede aprobar gastos de su propia empresa
            elif user.role == "EMPRESA":
                empresa = EmpresaProfile.objects.filter(user=user).first()
                if not empresa:
                    return Response({"error": "No tienes una empresa asociada"}, status=status.HTTP_404_NOT_FOUND)

                if gasto.empresa != empresa:
                    return Response({"error": "No tienes permiso para gestionar este gasto"}, status=status.HTTP_403_FORBIDDEN)

                gasto.estado = estado
                gasto.save()
                return Response({"message": "Estado actualizado correctamente"}, status=status.HTTP_200_OK)

            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        except Gasto.DoesNotExist:
            return Response({"error": "Gasto no encontrado"}, status=status.HTTP_404_NOT_FOUND)


class GastoListView(APIView):
    """Vista para listar los gastos con detalles de los viajes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista todos los gastos dependiendo del rol"""
        user = request.user

        if user.role == "MASTER":
            gastos = Gasto.objects.all()
        elif user.role == "EMPRESA":
            gastos = Gasto.objects.filter(empresa__user=user)
        elif user.role == "EMPLEADO":
            gastos = Gasto.objects.filter(empleado__user=user)
        else:
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        serializer = GastoSerializer(gastos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
