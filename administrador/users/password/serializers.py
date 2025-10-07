"""
Serializers para gestión de contraseñas
"""
from rest_framework import serializers


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitar restablecimiento de contraseña"""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar restablecimiento con token"""
    token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text="Mínimo 8 caracteres"
    )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña de usuario autenticado"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Contraseña actual"
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text="Nueva contraseña (mínimo 8 caracteres)"
    )

    def validate(self, data):
        """Validar que las contraseñas no sean iguales"""
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({
                "new_password": "La nueva contraseña no puede ser igual a la anterior."
            })
        return data
