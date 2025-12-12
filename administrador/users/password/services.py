"""
Servicios de lógica de negocio para gestión de contraseñas
"""
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction

from users.email.services import send_email
from users.models import CustomUser, PasswordResetToken


def create_password_reset_token(user):
    """
    Crea un token de restablecimiento de contraseña para el usuario.

    Args:
        user: Instancia de CustomUser

    Returns:
        PasswordResetToken: Token creado
    """
    return PasswordResetToken.objects.create(user=user)


def send_password_reset_email(user, token, frontend_url=None):
    """
    Envía un email con el enlace para restablecer la contraseña.

    Args:
        user: Instancia de CustomUser
        token: Token de restablecimiento
        frontend_url: URL base del frontend (opcional, por defecto settings.FRONTEND_BASE_URL)

    Returns:
        bool: True si el email se envió correctamente
    """
    base_frontend_url = (
        frontend_url
        or getattr(settings, "FRONTEND_BASE_URL", "https://tr7p.es")
    ).rstrip("/")
    reset_path = f"reset-password/?token={token.token}"
    reset_link = urljoin(f"{base_frontend_url}/", reset_path)

    return send_email(
        subject="Restablecimiento de contraseña",
        message=f"Usa este enlace para restablecer tu contraseña: {reset_link}",
        recipients=[user.email],
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
        fail_silently=False,
    )


def get_user_by_email(email):
    """
    Obtiene un usuario por su email.

    Args:
        email: Email del usuario

    Returns:
        CustomUser o None si no existe
    """
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return None


def validate_reset_token(token_str):
    """
    Valida un token de restablecimiento de contraseña.

    Args:
        token_str: String del token UUID

    Returns:
        tuple: (PasswordResetToken o None, mensaje de error o None)
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token_str)
        if not reset_token.is_valid():
            return None, "El token ha expirado"
        return reset_token, None
    except PasswordResetToken.DoesNotExist:
        return None, "Token inválido"


def reset_user_password(user, new_password):
    """
    Restablece la contraseña de un usuario.

    Args:
        user: Instancia de CustomUser
        new_password: Nueva contraseña en texto plano

    Returns:
        bool: True si se cambió correctamente
    """
    user.set_password(new_password)
    user.save()
    return True


def change_user_password(user, old_password, new_password):
    """
    Cambia la contraseña de un usuario autenticado.

    Args:
        user: Instancia de CustomUser
        old_password: Contraseña actual
        new_password: Nueva contraseña

    Returns:
        tuple: (bool éxito, dict datos de respuesta o error)
    """
    # Validar contraseña actual
    if not user.check_password(old_password):
        return False, {"error": "La contraseña actual es incorrecta."}

    # Cambiar contraseña y actualizar flag
    user.password = make_password(new_password)
    user.must_change_password = False

    with transaction.atomic():
        user.save(update_fields=["password", "must_change_password"])

    return True, {
        "message": "Contraseña cambiada con éxito.",
        "must_change_password": user.must_change_password
    }


def delete_reset_token(token):
    """
    Elimina un token de restablecimiento después de usarlo.

    Args:
        token: Instancia de PasswordResetToken
    """
    token.delete()
