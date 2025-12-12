from rest_framework.permissions import BasePermission


class IsMaster(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "MASTER"

class IsEmpresa(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "EMPRESA"

class IsEmpleado(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "EMPLEADO"

