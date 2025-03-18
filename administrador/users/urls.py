from django.urls import path

from .auth_views import LoginView, LogoutView, RegisterUserView
from .empresa_views import EliminarEmpresaView, EliminarEmpleadoView, ListarEmpresasView, RegisterEmpresaView, \
    UpdatePermissionsEmpresa, RegisterEmployeeView, BatchRegisterEmployeesView
from .gastos_views import CrearGastoView, AprobarRechazarGastoView, GastoListView
from .notificaciones_views import ListaNotificacionesView, CrearNotificacionView
from .viajes_views import CrearViajeView, AprobarRechazarViajeView, FinalizarViajeView, IniciarViajeView, \
    ListarViajesPendientesView, ListarViajesAprobadosView, ListarViajesFinalizadosView, ListarTodosLosViajesView
from .views import UserDetailView, EmployeeListView, PasswordResetRequestView, \
    PasswordResetConfirmView, ChangePasswordView

urlpatterns = [
    # Autenticación
    path('register/', RegisterUserView.as_view(), name='register'),
    path('empresas/new/', RegisterEmpresaView.as_view(), name='crear_empresa'),
    path('empleados/nuevo/', RegisterEmployeeView.as_view(), name='registrar_empleado'),
    path("empleados/batch-upload/", BatchRegisterEmployeesView.as_view(), name="batch_register_employees"),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Usuarios y empresas
    path('profile/', UserDetailView.as_view(), name='profile'),
    path('empleados/', EmployeeListView.as_view(), name='empleados'),
    path('empresas/<int:empresa_id>/', EliminarEmpresaView.as_view(), name='eliminar_empresa'),
    path('empleados/<str:dni>/', EliminarEmpleadoView.as_view(), name='eliminar_empleado'),
    path('empresas/<int:empresa_id>/permisos/', UpdatePermissionsEmpresa.as_view(), name='actualizar_permiso_empresa'),
    path('listar/empresas/', ListarEmpresasView.as_view(), name='listar_empresas'),

    # Gastos
    path('gastos/', GastoListView.as_view(), name='lista_gastos'),
    path('gastos/nuevo/', CrearGastoView.as_view(), name='nuevo_gasto'),
    path('gastos/<int:gasto_id>/', AprobarRechazarGastoView.as_view(), name='aprobar_rechazar_gasto'),

    # Viajes
    path("viajes/nuevo/", CrearViajeView.as_view(), name="nuevo_viaje"),
    path("viajes/<int:viaje_id>/", AprobarRechazarViajeView.as_view(), name="aprobar_rechazar_viaje"),
    path("viajes/<int:viaje_id>/iniciar/", IniciarViajeView.as_view(), name="iniciar_viaje"),
    path("viajes/<int:viaje_id>/end/", FinalizarViajeView.as_view(), name="finalizar_viaje"),
    path("viajes/pendientes/", ListarViajesPendientesView.as_view(), name="listar_viajes_pendientes"),
    path("viajes/aprobados/", ListarViajesAprobadosView.as_view(), name="viajes_aprobados"),
    path("viajes/list/over/", ListarViajesFinalizadosView.as_view(), name="viajes_aprobados"),
    path("viajes/all/", ListarTodosLosViajesView.as_view(), name="viajes_todos"),

    # Contraseña
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    #notificaciones
    path("notificaciones/",ListaNotificacionesView.as_view(), name="lista_notificaciones"),
    path("notificaciones/crear/", CrearNotificacionView.as_view(), name="crear_notificacion"),


]
