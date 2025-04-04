from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from .models import CustomUser, PasswordResetToken, EmpresaProfile, EmpleadoProfile
from .serializers import CustomUserSerializer, EmpleadoProfileSerializer
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

User = get_user_model()


class UserDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener datos del usuario autenticado."""
        user = request.user
        empresa_id = None

        if user.role == "EMPRESA":
            empresa_profile = EmpresaProfile.objects.filter(user=user).first()
            empresa_id = empresa_profile.id if empresa_profile else None

        return Response({
            "username": user.username,
            "role": user.role,
            "empresa_id": empresa_id,
            "must_change_password": user.must_change_password
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
        Token.objects.filter(user=user).delete()  # 🔹 Elimina el token antes de borrar el usuario
        user.delete()
        return Response({"message": "Usuario eliminado exitosamente."}, status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    """Permite solicitar un restablecimiento de contraseña"""

    def post(self, request):
        email = request.data.get("email")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "No se encontró un usuario con ese email"}, status=status.HTTP_404_NOT_FOUND)

        # 🔹 Generar un nuevo token
        reset_token = PasswordResetToken.objects.create(user=user)

        # 🔹 Enviar el email con el enlace de restablecimiento
        reset_link = f"http://localhost:5173/reset-password/?token={reset_token.token}"  # ✅ Ahora apunta a React
        send_mail(
            subject="Restablecimiento de contraseña",
            message=f"Usa este enlace para restablecer tu contraseña: {reset_link}",
            from_email="soporte@tuempresa.com",
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"message": "Se ha enviado un enlace para restablecer tu contraseña"},
                        status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    """Permite restablecer la contraseña con un token válido"""

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Verificar si el token sigue siendo válido
        if not reset_token.is_valid():
            return Response({"error": "El token ha expirado"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Cambiar la contraseña del usuario
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # 🔹 Eliminar el token para que no pueda usarse otra vez
        reset_token.delete()

        return Response({"message": "Tu contraseña ha sido restablecida con éxito"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Permite a un usuario cambiar su contraseña si es su primer inicio de sesión"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if user.role == "MASTER":
            return Response({"error": "Los usuarios master no deberian usar este formulario."},
                            status=status.HTTP_403_FORBIDDEN)

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"error": "Debes ingresar tu contraseña actual y la nueva."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"error": "La contraseña actual es incorrecta."}, status=status.HTTP_400_BAD_REQUEST)

        if old_password == new_password:
            return Response({"error": "La nueva contraseña no puede ser igual a la anterior."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Cambia la contraseña correctamente
        user.password = make_password(new_password)
        user.must_change_password = False  # ✅ Cambiamos el estado

        with transaction.atomic():  # ✅ Asegura que ambos cambios se guarden correctamente
            user.save(update_fields=["password", "must_change_password"])

        # 🔹 Verifica si se guardaron los cambios correctamente
        print(f"DEBUG: must_change_password después de guardar: {user.must_change_password}")
        print(f"DEBUG: Contraseña hash guardado: {user.password}")

        return Response({
            "message": "Contraseña cambiada con éxito.",
            "must_change_password": user.must_change_password  # ✅ Debería devolver `false`
        }, status=status.HTTP_200_OK)


class EmpresaEmpleadosView(APIView):
    """Obtener empleados de la empresa autenticada"""
    authentication_classes = [TokenAuthentication]
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
    authentication_classes = [TokenAuthentication]
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
    """MASTER: Lista empleados de una empresa específica"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empresa_id):
        if request.user.role != "MASTER":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empresa = EmpresaProfile.objects.get(id=empresa_id)
        except EmpresaProfile.DoesNotExist:
            return Response({"error": "Empresa no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        empleados = EmpleadoProfile.objects.filter(empresa=empresa)
        serializer = EmpleadoProfileSerializer(empleados, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
