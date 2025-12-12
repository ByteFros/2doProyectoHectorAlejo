"""
Permisos personalizados para ViewSets de empresas y empleados.
Estos permissions son wrappers ligeros que reutilizan la lógica
de negocio definida en users.common.services.
"""
from rest_framework import permissions

from users.common.services import can_access_empleado, can_access_empresa, get_user_empresa


class IsMaster(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol MASTER.

    Usage:
        class MyViewSet(ModelViewSet):
            permission_classes = [IsAuthenticated, IsMaster]
    """
    message = "Solo usuarios MASTER pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "MASTER"
        )


class IsEmpresa(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol EMPRESA.

    Usage:
        class MyViewSet(ModelViewSet):
            permission_classes = [IsAuthenticated, IsEmpresa]
    """
    message = "Solo usuarios EMPRESA pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "EMPRESA"
        )


class IsMasterOrEmpresa(permissions.BasePermission):
    """
    Permite acceso a usuarios con rol MASTER o EMPRESA.

    Usage:
        class MyViewSet(ModelViewSet):
            permission_classes = [IsAuthenticated, IsMasterOrEmpresa]
    """
    message = "Solo usuarios MASTER o EMPRESA pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["MASTER", "EMPRESA"]
        )


class CanAccessEmpresa(permissions.BasePermission):
    """
    Verifica si el usuario puede acceder a una empresa específica.
    Reutiliza la lógica de can_access_empresa() de common.services.

    - MASTER: Puede acceder a todas las empresas
    - EMPRESA: Solo puede acceder a su propia empresa
    - EMPLEADO: No puede acceder (retorna False)

    Usage:
        class EmpresaViewSet(ModelViewSet):
            permission_classes = [IsAuthenticated, CanAccessEmpresa]
    """
    message = "No tienes permisos para acceder a esta empresa"

    def has_permission(self, request, view):
        # Permitir a nivel de acción (list, create)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Validar a nivel de objeto específico (retrieve, update, destroy)
        return can_access_empresa(request.user, obj)


class CanAccessEmpleado(permissions.BasePermission):
    """
    Verifica si el usuario puede acceder a un empleado específico.
    Reutiliza la lógica de can_access_empleado() de common.services.

    - MASTER: Puede acceder a todos los empleados
    - EMPRESA: Solo puede acceder a empleados de su empresa
    - EMPLEADO: Solo puede acceder a su propio perfil

    Usage:
        class EmpleadoViewSet(ModelViewSet):
            permission_classes = [IsAuthenticated, CanAccessEmpleado]
    """
    message = "No tienes permisos para acceder a este empleado"

    def has_permission(self, request, view):
        # Permitir a nivel de acción (list, create)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Validar a nivel de objeto específico (retrieve, update, destroy)
        return can_access_empleado(request.user, obj)


class CanManageEmpleados(permissions.BasePermission):
    """
    Permite gestionar empleados (crear, modificar, eliminar).
    Solo MASTER y EMPRESA pueden gestionar empleados.

    - MASTER: Puede gestionar todos los empleados
    - EMPRESA: Solo puede gestionar empleados de su empresa
    - EMPLEADO: No puede gestionar empleados

    Usage:
        class EmpleadoViewSet(ModelViewSet):
            def get_permissions(self):
                if self.action in ['create', 'update', 'destroy']:
                    return [IsAuthenticated(), CanManageEmpleados()]
                return [IsAuthenticated()]
    """
    message = "No tienes permisos para gestionar empleados"

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["MASTER", "EMPRESA"]
        )

    def has_object_permission(self, request, view, obj):
        # Reutiliza la función de common
        return can_access_empleado(request.user, obj)


class CanViewPendingReviews(permissions.BasePermission):
    """
    Permite ver viajes/empleados con revisiones pendientes.

    - MASTER: Puede ver todos los pendientes
    - EMPRESA: Puede ver pendientes de sus empleados (independiente de autogestión)
    - EMPLEADO: No puede ver (403)
    """
    message = "No tienes permisos para ver revisiones pendientes"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # MASTER siempre puede ver
        if request.user.role == "MASTER":
            return True

        # EMPRESA siempre puede ver (la edición sigue controlada por otros permisos)
        if request.user.role == "EMPRESA":
            empresa = get_user_empresa(request.user)
            if not empresa:
                return False
            return True

        # EMPLEADO no puede ver
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite lectura a todos, pero solo el propietario puede modificar.
    Útil para operaciones donde queremos que MASTER y el dueño puedan editar.

    Usage:
        class MyViewSet(ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    """
    message = "Solo el propietario puede modificar este recurso"

    def has_object_permission(self, request, view, obj):
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # MASTER puede todo
        if request.user.role == "MASTER":
            return True

        # Verificar propiedad según el tipo de objeto
        if hasattr(obj, 'user'):  # Es una Empresa
            return can_access_empresa(request.user, obj)
        if hasattr(obj, 'empresa'):  # Es un Empleado
            return can_access_empleado(request.user, obj)

        return False
