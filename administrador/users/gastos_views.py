from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Gasto, EmpleadoProfile, EmpresaProfile, Viaje
from .serializers import GastoSerializer
from django.http import FileResponse, Http404
import mimetypes


class CrearGastoView(APIView):
    """Permite a un empleado registrar un gasto en un viaje aprobado o finalizado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # ✅ Asegura que acepta archivos opcionales

    def post(self, request):

        print("Data recibida", request.data.dict())

        """Registrar un nuevo gasto"""
        if request.user.role != "EMPLEADO":
            return Response({"error": "Solo los empleados pueden registrar gastos"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
            data = request.data.dict()
            data["empleado_id"] = empleado.id
            data["empresa_id"] = empleado.empresa.id

            # 🔥 Verificar que el viaje existe y no está cancelado
            viaje_id = data.get("viaje_id")
            try:
                viaje = Viaje.objects.get(id=viaje_id)
                if viaje.estado == "CANCELADO":
                    return Response({"error": "No puedes registrar gastos en viajes cancelados"},
                                    status=400)
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
                    return Response({"error": "No tienes permiso para gestionar este gasto"},
                                    status=status.HTTP_403_FORBIDDEN)

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


class GastoUpdateDeleteView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, gasto_id):
        try:
            gasto = Gasto.objects.get(id=gasto_id, empleado__user=request.user)
        except Gasto.DoesNotExist:
            return Response({"error": "Gasto no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = GastoSerializer(gasto, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, gasto_id):
        try:
            gasto = Gasto.objects.get(id=gasto_id, empleado__user=request.user)
            gasto.delete()
            return Response({"message": "Gasto eliminado correctamente"}, status=status.HTTP_200_OK)
        except Gasto.DoesNotExist:
            return Response({"error": "Gasto no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)


class GastoComprobanteDownloadView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, gasto_id):
        try:
            gasto = Gasto.objects.get(id=gasto_id)

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

        except Gasto.DoesNotExist:
            raise Http404("Gasto no encontrado")
