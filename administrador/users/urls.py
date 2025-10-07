from django.urls import path, include

from .dias_views import DiaViajeListView, DiaViajeUpdateView
from .notas_views import NotaViajeListCreateView, NotaViajeDeleteView
from .notificaciones_views import ListaNotificacionesView, CrearNotificacionView
from .report_views import CompanyTripsSummaryView, TripsPerMonthView, TripsTypeView, ExemptDaysView, GeneralInfoView, \
    EmployeeTripsSummaryView, MasterCompanyEmployeesView
from .views import UserDetailView, EmployeeListView, EmpleadosPorEmpresaView

urlpatterns = [
    # Autenticación - Módulo dedicado
    path('', include('users.authentication.urls')),

    # Contraseñas - Módulo dedicado
    path('', include('users.password.urls')),

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

    # Usuarios
    path('profile/', UserDetailView.as_view(), name='profile'),
    path('empleados/', EmployeeListView.as_view(), name='empleados'),
    path('empresas/<int:empresa_id>/empleados/', EmpleadosPorEmpresaView.as_view(), name='empleados_por_empresa'),

    # Validación de días (pendiente de modularizar)
    path('viajes/<int:viaje_id>/dias/', DiaViajeListView.as_view(), name='dias-list'),
    path('viajes/<int:viaje_id>/dias/<int:dia_id>/', DiaViajeUpdateView.as_view(), name='dias-update'),

    # notificaciones
    path("notificaciones/", ListaNotificacionesView.as_view(), name="lista_notificaciones"),
    path("notificaciones/crear/", CrearNotificacionView.as_view(), name="crear_notificacion"),

    # notas
    path("notas/<int:viaje_id>/", NotaViajeListCreateView.as_view(), name="notas_viaje"),
    path("notas/delete/<int:nota_id>/", NotaViajeDeleteView.as_view(), name="eliminar_nota"),

    # endpoints optimizados
    path('report/viajes/', CompanyTripsSummaryView.as_view(), name='company-trips-summary'),
    path('report/trips-per-month/', TripsPerMonthView.as_view(), name='trips-per-month'),
    path('report/trips-type/', TripsTypeView.as_view(), name='trips-type'),
    path('report/exempt-days/', ExemptDaysView.as_view(), name='exempt-days'),
    path('report/general-info/', GeneralInfoView.as_view(), name='general-info'),
    path('report/empleados/', EmployeeTripsSummaryView.as_view(), name='employee-trips-summary'),
    path('report/empresa/<int:empresa_id>/empleados/viajes/', MasterCompanyEmployeesView.as_view()),


]
