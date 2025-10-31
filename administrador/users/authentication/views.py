"""
Vistas para autenticación de usuarios
"""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterUserSerializer
from .services import build_auth_response, build_session_response


class LoginView(APIView):
    """
    Autentica un usuario y devuelve su token y datos de perfil.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        response_data = build_auth_response(user, token)

        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Cierra la sesión del usuario eliminando su token.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.auth.delete()
            return Response(
                {"message": "Sesión cerrada correctamente"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegisterUserView(APIView):
    """Registra nuevos usuarios controlando el rol del solicitante."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        actor = request.user

        if actor.role == "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        if hasattr(data, "_mutable"):
            data._mutable = True

        if actor.role == "EMPRESA":
            empresa_profile = getattr(actor, "empresa_profile", None)
            if not empresa_profile:
                return Response({"error": "El usuario autenticado no tiene perfil de empresa"}, status=status.HTTP_400_BAD_REQUEST)
            data["role"] = "EMPLEADO"
            data["empresa_id"] = empresa_profile.id
        else:  # MASTER
            role = data.get("role")
            if not role:
                return Response({"role": ["Este campo es obligatorio."]}, status=status.HTTP_400_BAD_REQUEST)
            data["role"] = str(role).upper()

        serializer = RegisterUserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(user, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionView(APIView):
    """
    Valida la sesión actual y devuelve los datos del usuario autenticado.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        token = request.auth
        response_data = build_session_response(user, token)

        return Response(response_data)
