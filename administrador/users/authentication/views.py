"""Vistas para autenticación de usuarios."""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterUserSerializer, CustomTokenObtainPairSerializer
from .services import build_session_response


class LoginView(TokenObtainPairView):
    """Entrega pares access/refresh junto con los metadatos del usuario."""

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """Invalida el refresh token recibido (requiere blacklist habilitado)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Debes proporcionar el refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Sesión cerrada correctamente"},
            status=status.HTTP_205_RESET_CONTENT,
        )


class RegisterUserView(APIView):
    """Registra nuevos usuarios controlando el rol del solicitante."""

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
    """Devuelve los datos del usuario autenticado usando el JWT actual."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        response_data = build_session_response(user)
        return Response(response_data)
