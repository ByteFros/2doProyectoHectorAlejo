from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import EmpresaProfile, EmpleadoProfile
from .serializers import CustomUserSerializer, EmpleadoProfileSerializer

User = get_user_model()


class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener datos del usuario autenticado."""
        user = request.user
        empresa_id = None
        nombre = None
        apellido = None

        if user.role == "EMPRESA":
            empresa_profile = EmpresaProfile.objects.filter(user=user).first()
            empresa_id = empresa_profile.id if empresa_profile else None

        elif user.role == "EMPLEADO":
            empleado_profile = EmpleadoProfile.objects.filter(user=user).first()
            if empleado_profile:
                empresa_id = empleado_profile.empresa.id
                nombre = empleado_profile.nombre
                apellido = empleado_profile.apellido

        return Response({
            "username": user.username,
            "role": user.role,
            "empresa_id": empresa_id,
            "must_change_password": user.must_change_password,
            "nombre": nombre,
            "apellido": apellido
        })

    def put(self, request):
        """Actualizar datos del usuario autenticado."""
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Perfil actualizado correctamente", "data": serializer.data})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Eliminar usuario autenticado y su token."""
        user = request.user
        user.delete()
        return Response({"message": "Usuario eliminado exitosamente."}, status=status.HTTP_204_NO_CONTENT)


class EmpresaEmpleadosView(APIView):
    """Obtener empleados de la empresa autenticada"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Devuelve la lista de empleados asociados a la empresa autenticada"""
        user = request.user

        if user.role != "EMPRESA":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        empresa = EmpresaProfile.objects.filter(user=user).first()
        if not empresa:
            return Response({"error": "No tienes un perfil de empresa registrado"}, status=status.HTTP_404_NOT_FOUND)

        empleados = EmpleadoProfile.objects.filter(empresa=empresa)
        empleados_data = [
            {
                "id": emp.user.id,
                "username": emp.user.username,
                "nombre": emp.nombre,
                "apellido": emp.apellido,
                "email": emp.user.email,
            }
            for emp in empleados
        ]

        return Response(empleados_data, status=status.HTTP_200_OK)


class EmployeeListView(APIView):
    """Vista para listar los empleados"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista los empleados según el rol del usuario"""
        user = request.user

        if user.role == "MASTER":
            # 🔹 El usuario MASTER ve todos los empleados
            empleados = EmpleadoProfile.objects.all()
        elif user.role == "EMPRESA":
            # 🔹 La EMPRESA solo ve los empleados de su empresa
            empleados = EmpleadoProfile.objects.filter(empresa__user=user)
        else:
            return Response({"error": "No autorizado"}, status=403)

        serializer = EmpleadoProfileSerializer(empleados, many=True)
        return Response(serializer.data, status=200)



class EmpleadosPorEmpresaView(APIView):
    """MASTER puede ver empleados de cualquier empresa; EMPRESA sólo los suyos"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empresa_id):
        # Recuperamos la empresa o 404
        empresa = get_object_or_404(EmpresaProfile, id=empresa_id)

        # Si soy EMPRESA, sólo puedo consultar mi propia empresa
        if request.user.role == "EMPRESA":
            mi_empresa = getattr(request.user, "empresa_profile", None)
            if not mi_empresa or mi_empresa.id != empresa.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        # Si soy EMPLEADO, no tengo permiso
        if request.user.role == "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        # Llegados aquí, MASTER o EMPRESA dueña
        empleados = EmpleadoProfile.objects.filter(empresa=empresa)
        serializer = EmpleadoProfileSerializer(empleados, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
