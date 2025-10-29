"""Servicios auxiliares para el módulo de mensajería."""

from django.shortcuts import get_object_or_404

from users.models import (
    Conversacion,
    CustomUser,
    EmpresaProfile,
    EmpleadoProfile,
)
from users.common.exceptions import UnauthorizedAccessError


def get_target_user_or_400(user: CustomUser, target_user_id: int) -> CustomUser:
    """Obtiene el usuario destino validando roles y relaciones."""
    target_user = get_object_or_404(CustomUser, id=target_user_id)

    if target_user == user:
        raise UnauthorizedAccessError("No puedes iniciar una conversación contigo mismo")

    if user.role == "MASTER":
        if target_user.role not in ["EMPRESA", "EMPLEADO"]:
            raise UnauthorizedAccessError("Sólo puedes contactar empresas o empleados")
        return target_user

    if user.role == "EMPRESA":
        empresa_profile = EmpresaProfile.objects.filter(user=user).first()
        if not empresa_profile:
            raise UnauthorizedAccessError("No se encontró el perfil de empresa")

        if target_user.role == "MASTER":
            return target_user

        if target_user.role == "EMPLEADO":
            empleado = getattr(target_user, "empleado_profile", None)
            if not empleado or empleado.empresa_id != empresa_profile.id:
                raise UnauthorizedAccessError("Este empleado no pertenece a tu empresa")
            return target_user

        raise UnauthorizedAccessError("Rol destino no permitido para tu empresa")

    if user.role == "EMPLEADO":
        empleado_profile = getattr(user, "empleado_profile", None)
        if not empleado_profile:
            raise UnauthorizedAccessError("No se encontró el perfil de empleado")

        if target_user.role == "EMPRESA":
            empresa_user = empleado_profile.empresa.user
            if target_user != empresa_user:
                raise UnauthorizedAccessError("Sólo puedes contactar con tu empresa")
            return target_user

        if target_user.role == "EMPLEADO":
            target_profile = getattr(target_user, "empleado_profile", None)
            if not target_profile or target_profile.empresa_id != empleado_profile.empresa_id:
                raise UnauthorizedAccessError("Sólo puedes contactar compañeros de tu empresa")
            return target_user

        raise UnauthorizedAccessError("Rol destino no permitido para empleados")

    raise UnauthorizedAccessError("Rol no permitido para crear conversaciones")


def get_existing_conversation(user_a: CustomUser, user_b: CustomUser) -> Conversacion | None:
    """Busca una conversación 1:1 existente entre dos usuarios."""
    for conversacion in Conversacion.objects.filter(participantes=user_a).prefetch_related('participantes'):
        participantes_ids = list(conversacion.participantes.values_list('id', flat=True))
        if len(participantes_ids) == 2 and user_b.id in participantes_ids:
            return conversacion
    return None
def create_conversation(user: CustomUser, target_user: CustomUser) -> Conversacion:
    """Crea una conversación 1:1 (ya verificado que no existe)."""
    conversacion = Conversacion.objects.create()
    conversacion.participantes.add(user, target_user)
    return conversacion
