"""
Servicios de lógica de negocio para autenticación
"""
from users.models import EmpresaProfile, EmpleadoProfile


def get_user_profile_data(user):
    """
    Obtiene los datos adicionales del perfil del usuario según su rol.

    Args:
        user: Instancia de CustomUser

    Returns:
        dict: Diccionario con los datos del perfil específico del rol
    """
    profile_data = {}

    if user.role == "EMPRESA":
        try:
            profile_data["empresa_id"] = user.empresa_profile.id
        except EmpresaProfile.DoesNotExist:
            profile_data["empresa_id"] = None

    elif user.role == "EMPLEADO":
        try:
            profile_data["empleado_id"] = user.empleado_profile.id
        except EmpleadoProfile.DoesNotExist:
            profile_data["empleado_id"] = None

    return profile_data


def build_auth_response(user):
    """Datos comunes incluidos en las respuestas de autenticación."""
    response = {
        "role": user.role,
        "must_change_password": user.must_change_password,
        "user_id": user.id,
    }

    profile_data = get_user_profile_data(user)
    response.update(profile_data)

    return response


def build_session_response(user):
    """Respuesta serializada para `/session/`."""
    response = {
        "username": user.username,
        "email": user.email,
    }
    response.update(build_auth_response(user))
    return response
