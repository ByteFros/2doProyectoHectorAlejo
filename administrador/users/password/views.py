"""
Vistas para gestión de contraseñas
"""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer
)
from .services import (
    get_user_by_email,
    create_password_reset_token,
    send_password_reset_email,
    validate_reset_token,
    reset_user_password,
    delete_reset_token,
    change_user_password
)


class PasswordResetRequestView(APIView):
    """
    Permite solicitar un restablecimiento de contraseña por email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = get_user_by_email(email)

        if not user:
            return Response(
                {"error": "No se encontró un usuario con ese email"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generar token y enviar email
        reset_token = create_password_reset_token(user)
        email_sent = send_password_reset_email(user, reset_token)

        if not email_sent:
            return Response(
                {"error": "Error al enviar el email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Se ha enviado un enlace para restablecer tu contraseña"},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    Permite restablecer la contraseña con un token válido.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        # Validar token
        reset_token, error = validate_reset_token(token_str)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        # Cambiar contraseña
        user = reset_token.user
        reset_user_password(user, new_password)

        # Eliminar token usado
        delete_reset_token(reset_token)

        return Response(
            {"message": "Tu contraseña ha sido restablecida con éxito"},
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    """
    Permite a un usuario autenticado cambiar su contraseña.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Cambiar contraseña usando el servicio
        success, response_data = change_user_password(
            request.user,
            old_password,
            new_password
        )

        if not success:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)
