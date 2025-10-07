"""
URLs del módulo de empresas y empleados
"""
from django.urls import path
from .views import (
    RegisterEmpresaView,
    RegisterEmployeeView,
    BatchRegisterEmployeesView,
    EliminarEmpleadoView,
    EmpresaManagementView,
    PendingCompaniesView,
    PendingEmployeesByCompanyView
)

urlpatterns = [
    # Gestión de empresas
    path('empresas/new/', RegisterEmpresaView.as_view(), name='crear_empresa'),
    path('empresas/', EmpresaManagementView.as_view(), name='listar_empresas'),
    path('empresas/<int:empresa_id>/', EmpresaManagementView.as_view(), name='gestionar_empresa'),

    # Gestión de empleados
    path('empleados/nuevo/', RegisterEmployeeView.as_view(), name='registrar_empleado'),
    path('empleados/batch-upload/', BatchRegisterEmployeesView.as_view(), name='batch_register_employees'),
    path('empleados/<int:empleado_id>/', EliminarEmpleadoView.as_view(), name='eliminar_empleado'),

    # Empresas y empleados con viajes pendientes
    path('empresas/pending/', PendingCompaniesView.as_view(), name='pending_companies'),
    path('empresas/<int:empresa_id>/empleados/pending/', PendingEmployeesByCompanyView.as_view(),
         name='pending_employees_by_company'),
]
