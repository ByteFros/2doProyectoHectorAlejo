from django.urls import path, include

from .views import UserDetailView, EmployeeListView, EmpleadosPorEmpresaView

urlpatterns = [
    # Autenticación - Módulo dedicado
    path('auth/', include('users.authentication.urls')),

    # Contraseñas - Módulo dedicado
    path('auth/', include('users.password.urls')),

    # Empresas y Empleados - Módulo dedicado
    path('', include('users.empresas.urls')),

    # Viajes - Módulo dedicado
    path('', include('users.viajes.urls')),

    # Gastos - Módulo dedicado
    path('', include('users.gastos.urls')),

    # Mensajería - Módulo dedicado
    path('', include('users.mensajeria.urls')),

    # Exportación - Módulo dedicado
    path('', include('users.exportacion.urls')),

    # Notas - Módulo dedicado
    path('', include('users.notas.urls')),

    # Notificaciones - Módulo dedicado
    path('', include('users.notificaciones.urls')),

    # Reportes - Módulo dedicado
    path('', include('users.reportes.urls')),

    # Usuarios
    path('profile/', UserDetailView.as_view(), name='profile'),
    # Las siguientes rutas están comentadas porque el módulo empresas usa ViewSets con Router
    # que ya genera estas rutas automáticamente. Descomentar solo si se necesitan las vistas legacy.
    # path('empleados/', EmployeeListView.as_view(), name='empleados'),
    # path('empresas/<int:empresa_id>/empleados/', EmpleadosPorEmpresaView.as_view(), name='empleados_por_empresa'),
]
