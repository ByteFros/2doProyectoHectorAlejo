from django.urls import path

from .auth_views import LoginView, LogoutView, RegisterUserView
from .dias_views import DiaViajeListView, DiaViajeUpdateView
from .empresa_views import EliminarEmpleadoView, RegisterEmpresaView, \
    RegisterEmployeeView, BatchRegisterEmployeesView, EmpresaManagementView, PendingCompaniesView, \
    PendingEmployeesByCompanyView
from .export_views import ExportMasterCSVView, ExportEmpresaCSVView
from .gastos_views import CrearGastoView, AprobarRechazarGastoView, GastoListView, GastoUpdateDeleteView, \
    GastoComprobanteDownloadView
from .messages_views import SolicitarJustificanteView, ListarMensajesView, ResponderMensajeView, \
    CambiarEstadoJustificacionView, DescargarArchivoMensajeView, EnviarMensajeView, ListarConversacionesView, \
    CrearConversacionView, ListarMensajesByIdView, DescargarAdjuntoMensajeView
from .notas_views import NotaViajeListCreateView, NotaViajeDeleteView
from .notificaciones_views import ListaNotificacionesView, CrearNotificacionView
from .report_views import CompanyTripsSummaryView, TripsPerMonthView, TripsTypeView, ExemptDaysView, GeneralInfoView, \
    EmployeeTripsSummaryView, MasterCompanyEmployeesView
from .viajes_views import CrearViajeView, AprobarRechazarViajeView, FinalizarViajeView, IniciarViajeView, \
    ListarViajesFinalizadosView, ListarTodosLosViajesView, CancelarViajeView, ViajeEnCursoView, \
    PendingTripsByEmployeeView, PendingTripsDetailView, FinalizarRevisionViajeView, EmployeeCityStatsView
from .views import UserDetailView, EmployeeListView, PasswordResetRequestView, \
    PasswordResetConfirmView, ChangePasswordView, EmpleadosPorEmpresaView

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
    path('empleados/ciudades/', EmployeeCityStatsView.as_view()),
    path('empleados/<int:empleado_id>/', EliminarEmpleadoView.as_view(), name='eliminar_empleado'),
    path('empresas/', EmpresaManagementView.as_view(), name='gestionar_empresas'),  # GET
    path('empresas/<int:empresa_id>/', EmpresaManagementView.as_view(), name='gestionar_una_empresa'),  # PUT & DELETE
    path('empresas/<int:empresa_id>/empleados/', EmpleadosPorEmpresaView.as_view(), name='empleados_por_empresa'),

    # Gastos
    path('gastos/', GastoListView.as_view(), name='lista_gastos'),
    path('gastos/new/', CrearGastoView.as_view(), name='nuevo_gasto'),
    path('gastos/<int:gasto_id>/', AprobarRechazarGastoView.as_view(), name='aprobar_rechazar_gasto'),
    path("gastos/edit/<int:gasto_id>/", GastoUpdateDeleteView.as_view(), name="gasto_crud"),
    path("gastos/<int:gasto_id>/file/", GastoComprobanteDownloadView.as_view(), name="gasto_archivo"),
    path("gastos/<int:gasto_id>/request-proof/", SolicitarJustificanteView.as_view(), name="solicitar_justificante"),

    # Viajes
    path("viajes/new/", CrearViajeView.as_view(), name="nuevo_viaje"),
    path("viajes/<int:viaje_id>/", AprobarRechazarViajeView.as_view(), name="aprobar_rechazar_viaje"),
    path("viajes/<int:viaje_id>/iniciar/", IniciarViajeView.as_view(), name="iniciar_viaje"),
    path("viajes/<int:viaje_id>/end/", FinalizarViajeView.as_view(), name="finalizar_viaje"),
    path("viajes/over/", ListarViajesFinalizadosView.as_view(), name="viajes-finalizados"),
    path('empresas/<int:empresa_id>/empleados/<int:empleado_id>/viajes/pending/', PendingTripsByEmployeeView.as_view(),
         name='pending-trips-by-employee'),

    path('empresas/<int:empresa_id>/empleados/pending/', PendingEmployeesByCompanyView.as_view(),
         name='pending-employees-by-company'),

    path("viajes/en-curso/", ViajeEnCursoView.as_view(), name="viaje_en_curso"),
    path("viajes/all/", ListarTodosLosViajesView.as_view(), name="viajes_todos"),
    path('viajes/pending/', PendingTripsDetailView.as_view(), name='pending-trips-count'),
    path("viajes/<int:viaje_id>/cancelar/", CancelarViajeView.as_view(), name="cancel"),
    # validacion de dias
    path('viajes/<int:viaje_id>/dias/', DiaViajeListView.as_view(), name='dias-list'),
    path('viajes/<int:viaje_id>/dias/<int:dia_id>/', DiaViajeUpdateView.as_view(), name='dias-update'),
    path("viajes/<int:viaje_id>/finalizar_revision/", FinalizarRevisionViajeView.as_view(),
         name="finalizar_revision_viaje"),



    # Contraseña
    path("password-reset-request/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # notificaciones
    path("notificaciones/", ListaNotificacionesView.as_view(), name="lista_notificaciones"),
    path("notificaciones/crear/", CrearNotificacionView.as_view(), name="crear_notificacion"),

    # notas
    path("notas/<int:viaje_id>/", NotaViajeListCreateView.as_view(), name="notas_viaje"),
    path("notas/delete/<int:nota_id>/", NotaViajeDeleteView.as_view(), name="eliminar_nota"),

    # Mensajes
    path("mensajes/", ListarMensajesView.as_view(), name="listar_mensajes"),
    path('mensajes/enviar/', EnviarMensajeView.as_view(), name='enviar_mensaje'),
    path("mensajes/<int:mensaje_id>/responder/", ResponderMensajeView.as_view(), name="responder_mensaje"),
    path("mensajes/<int:mensaje_id>/cambiar-estado/", CambiarEstadoJustificacionView.as_view(),
         name="cambiar_estado_justificante"),
    path("mensajes/justificante/<int:mensaje_id>/file/", DescargarArchivoMensajeView.as_view()),
    path("mensajes/<int:mensaje_id>/file/", DescargarAdjuntoMensajeView.as_view(), name="descargar_adjunto_mensaje"),

    # Conversaciones
    path('conversaciones/', ListarConversacionesView.as_view(), name='listar_conversaciones'),
    path('conversaciones/crear/', CrearConversacionView.as_view(), name='crear_conversacion'),
    path('conversaciones/<int:conversacion_id>/mensajes/', ListarMensajesByIdView.as_view(), name='listar_mensajes'),

    # endpoints optimizados
    path('report/viajes/', CompanyTripsSummaryView.as_view(), name='company-trips-summary'),
    path('report/trips-per-month/', TripsPerMonthView.as_view(), name='trips-per-month'),
    path('report/trips-type/', TripsTypeView.as_view(), name='trips-type'),
    path('report/exempt-days/', ExemptDaysView.as_view(), name='exempt-days'),
    path('report/general-info/', GeneralInfoView.as_view(), name='general-info'),
    path('report/companies/pending/', PendingCompaniesView.as_view(), name='pending-companies'),
    path('report/empleados/', EmployeeTripsSummaryView.as_view(), name='employee-trips-summary'),
    path('report/empresa/<int:empresa_id>/empleados/viajes/', MasterCompanyEmployeesView.as_view()),

    #exports
    path('export/viajes/exportar/', ExportMasterCSVView.as_view()),
    path('export/empresa/viajes/exportar/', ExportEmpresaCSVView.as_view()),


]
