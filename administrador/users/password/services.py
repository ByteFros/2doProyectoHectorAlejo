"""
Servicios de lógica de negocio para gestión de contraseñas
"""
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.db import transaction
from users.models import PasswordResetToken, CustomUser


def create_password_reset_token(user):
    """
    Crea un token de restablecimiento de contraseña para el usuario.

    Args:
        user: Instancia de CustomUser

    Returns:
        PasswordResetToken: Token creado
    """
    return PasswordResetToken.objects.create(user=user)


def send_password_reset_email(user, token, frontend_url="http://localhost:5173"):
    """
    Envía un email con el enlace para restablecer la contraseña.

    Args:
        user: Instancia de CustomUser
        token: Token de restablecimiento
        frontend_url: URL base del frontend (opcional)

    Returns:
        bool: True si el email se envió correctamente
    """
    reset_link = f"{frontend_url}/reset-password/?token={token.token}"

    try:
        print(
            f"[PasswordReset] Enviando correo a {user.email} "
            f"(from {getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)}, "
            f"host {settings.EMAIL_HOST}:{settings.EMAIL_PORT})"
        )
        send_mail(
            subject="Restablecimiento de contraseña",
            message=f"Usa este enlace para restablecer tu contraseña: {reset_link}",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


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
    # Validar rol MASTER
    if user.role == "MASTER":
        return False, {"error": "Los usuarios master no deberían usar este formulario."}

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
