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
    confirm_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text="Debe coincidir con la nueva contraseña"
    )

    def validate(self, data):
        confirm_password = data.pop('confirm_password')
        if data['new_password'] != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Las contraseñas no coinciden."
            })
        return data


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
