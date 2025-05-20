from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import EmpresaProfile, EmpleadoProfile
from .serializers import CustomUserSerializer, RegisterUserSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Autentica un usuario y devuelve su token y sus IDs."""
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)

        # Base de la respuesta
        resp = {
            "token": token.key,
            "role": user.role,
            "must_change_password": user.must_change_password,
            "user_id": user.id,
        }

        # Si es empresa, adjuntamos su perfil
        if user.role == "EMPRESA":
            try:
                resp["empresa_id"] = user.empresa_profile.id
            except EmpresaProfile.DoesNotExist:
                # opcional: log / warning de inconsistencia
                resp["empresa_id"] = None

        # Si es empleado, adjuntamos su perfil
        if user.role == "EMPLEADO":
            try:
                resp["empleado_id"] = user.empleado_profile.id
            except EmpleadoProfile.DoesNotExist:
                resp["empleado_id"] = None

        return Response(resp, status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Cerrar sesión eliminando el token"""
        try:
            request.auth.delete()  # Elimina el token actual
            return Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Registrar usuario con perfil de empresa o empleado"""
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(user, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        token = request.auth  # Este es el token enviado por el cliente

        resp = {
            "username": user.username,
            "role": user.role,
            "token": token.key if token else None,
            "must_change_password": user.must_change_password,
            "user_id": user.id,
        }

        if user.role == "EMPRESA":
            try:
                resp["empresa_id"] = user.empresa_profile.id
            except EmpresaProfile.DoesNotExist:
                resp["empresa_id"] = None

        if user.role == "EMPLEADO":
            try:
                resp["empleado_id"] = user.empleado_profile.id
            except EmpleadoProfile.DoesNotExist:
                resp["empleado_id"] = None

        return Response(resp)
