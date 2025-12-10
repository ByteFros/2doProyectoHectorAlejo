"""
Servicio genérico para envío de emails SMTP reutilizable en el proyecto.
"""
from typing import Iterable, List
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail


def _normalize_recipients(recipients: Iterable[str]) -> List[str]:
    """Convierte destinatarios en lista y limpia vacíos."""
    if not recipients:
        return []
    # Filtrar None/strings vacíos y conservar orden
    return [r for r in recipients if r]


def send_email(
    *,
    subject: str,
    message: str,
    recipients: Iterable[str],
    from_email: str | None = None,
    fail_silently: bool = False,
) -> bool:
    """
    Envía un email simple usando el backend configurado en settings.

    Args:
        subject: Asunto del correo
        message: Contenido en texto plano
        recipients: Iterable de direcciones destino
        from_email: Remitente (por defecto usa DEFAULT_FROM_EMAIL o EMAIL_HOST_USER)
        fail_silently: Se pasa al backend de Django

    Returns:
        bool: True si el envío no lanzó excepciones, False en caso contrario
    """
    recipient_list = _normalize_recipients(recipients)
    if not recipient_list:
        return False

    sender = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)

    try:
        print(
            f"[Email] Enviando correo a {', '.join(recipient_list)} "
            f"(from {sender}, host {settings.EMAIL_HOST}:{settings.EMAIL_PORT})"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=sender,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
        )
        return True
    except Exception as e:
        print(f"[Email] Error enviando correo: {e}")
        return False


def send_welcome_email(user, password: str, frontend_url: str | None = None) -> bool:
    """
    Envía un email de bienvenida con las credenciales de acceso.

    Args:
        user: Instancia de usuario recién creada
        password: Contraseña asignada (temporal o definitiva)
        frontend_url: URL base opcional del frontend

    Returns:
        bool: True si el email se envió correctamente
    """
    base_url = (frontend_url or getattr(settings, "FRONTEND_BASE_URL", "https://tr7p.es")).rstrip("/")
    # El login vive en la raíz del frontend
    login_link = f"{base_url}/"

    message = (
        f"Hola {user.username},\n\n"
        f"Se ha creado tu cuenta en la plataforma 7P.\n\n"
        f"Usuario: {user.username}\n"
        f"Email: {user.email}\n"
        f"Contraseña temporal: {password}\n\n"
        f"Accede aquí: {login_link} y cambia tu contraseña al iniciar sesión.\n\n"
        f"Si no reconoces este registro, contacta con el administrador."
    )

    return send_email(
        subject="Bienvenido a 7P - Credenciales de acceso",
        message=message,
        recipients=[user.email],
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
        fail_silently=False,
    )
