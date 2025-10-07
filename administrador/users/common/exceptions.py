"""
Excepciones personalizadas para la aplicación
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class ProfileNotFoundError(APIException):
    """Excepción cuando no se encuentra el perfil de usuario"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Perfil de usuario no encontrado'
    default_code = 'profile_not_found'


class EmpresaProfileNotFoundError(ProfileNotFoundError):
    """Excepción específica para perfil de empresa no encontrado"""
    default_detail = 'No tienes un perfil de empresa asociado'
    default_code = 'empresa_profile_not_found'


class EmpleadoProfileNotFoundError(ProfileNotFoundError):
    """Excepción específica para perfil de empleado no encontrado"""
    default_detail = 'No tienes un perfil de empleado asociado'
    default_code = 'empleado_profile_not_found'


class UnauthorizedAccessError(APIException):
    """Excepción para acceso no autorizado a recursos"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'No tienes permisos para acceder a este recurso'
    default_code = 'unauthorized_access'


class InvalidRoleError(APIException):
    """Excepción para rol de usuario inválido"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Rol de usuario no reconocido'
    default_code = 'invalid_role'


class InvalidStateTransitionError(APIException):
    """Excepción para transición de estado inválida"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Transición de estado no permitida'
    default_code = 'invalid_state_transition'


class DuplicateResourceError(APIException):
    """Excepción para recursos duplicados"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'El recurso ya existe'
    default_code = 'duplicate_resource'


class BusinessRuleViolationError(APIException):
    """Excepción para violaciones de reglas de negocio"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'La operación viola una regla de negocio'
    default_code = 'business_rule_violation'
