from django.urls import path

from .auth_views import LoginView, LogoutView, RegisterUserView
from .empresa_views import EliminarEmpleadoView, RegisterEmpresaView, \
    RegisterEmployeeView, BatchRegisterEmployeesView, EmpresaManagementView
from .gastos_views import CrearGastoView, AprobarRechazarGastoView, GastoListView, GastoUpdateDeleteView, \
    GastoComprobanteDownloadView
from .notas_views import NotaViajeListCreateView, NotaViajeDeleteView
from .notificaciones_views import ListaNotificacionesView, CrearNotificacionView
from .viajes_views import CrearViajeView, AprobarRechazarViajeView, FinalizarViajeView, IniciarViajeView, \
    ListarViajesFinalizadosView, ListarTodosLosViajesView, CancelarViajeView, ViajeEnCursoView
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
    path('empleados/<str:dni>/', EliminarEmpleadoView.as_view(), name='eliminar_empleado'),
    path('empresas2/', EmpresaManagementView.as_view(), name='gestionar_empresas'),  # GET
    path('empresas2/<int:empresa_id>/', EmpresaManagementView.as_view(), name='gestionar_una_empresa'),  # PUT & DELETE

    # Gastos
    path('gastos/', GastoListView.as_view(), name='lista_gastos'),
    path('gastos/new/', CrearGastoView.as_view(), name='nuevo_gasto'),
    path('gastos/<int:gasto_id>/', AprobarRechazarGastoView.as_view(), name='aprobar_rechazar_gasto'),
    path("gastos/edit/<int:gasto_id>/", GastoUpdateDeleteView.as_view(), name="gasto_crud"),
    path("gastos/<int:gasto_id>/file/", GastoComprobanteDownloadView.as_view(), name="gasto_archivo"),

    # Viajes
    path("viajes/new/", CrearViajeView.as_view(), name="nuevo_viaje"),
    path("viajes/<int:viaje_id>/", AprobarRechazarViajeView.as_view(), name="aprobar_rechazar_viaje"),
    path("viajes/<int:viaje_id>/iniciar/", IniciarViajeView.as_view(), name="iniciar_viaje"),
    path("viajes/<int:viaje_id>/end/", FinalizarViajeView.as_view(), name="finalizar_viaje"),
    path("viajes/over/", ListarViajesFinalizadosView.as_view(), name="viajes_aprobados"),
    path("viajes/en-curso/", ViajeEnCursoView.as_view(), name="viaje_en_curso"),
    path("viajes/all/", ListarTodosLosViajesView.as_view(), name="viajes_todos"),
    path("viajes/<int:viaje_id>/cancelar/", CancelarViajeView.as_view(), name="cancel"),

    # Contraseña
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    #notificaciones
    path("notificaciones/",ListaNotificacionesView.as_view(), name="lista_notificaciones"),
    path("notificaciones/crear/", CrearNotificacionView.as_view(), name="crear_notificacion"),

    #notas
    path("notas/<int:viaje_id>/", NotaViajeListCreateView.as_view(), name="notas_viaje"),
    path("notas/delete/<int:nota_id>/", NotaViajeDeleteView.as_view(), name="eliminar_nota")


]
