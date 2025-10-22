"""
URLs del módulo de viajes
"""
from django.urls import path
from .views import (
    CrearViajeView,
    VerificarViajeEnCursoView,
    AprobarRechazarViajeView,
    IniciarViajeView,
    FinalizarViajeView,
    CancelarViajeView,
    ViajeEnCursoView,
    ListarViajesFinalizadosView,
    PendingTripsByEmployeeView,
    ListarTodosLosViajesView,
    PendingTripsDetailView,
    FinalizarRevisionViajeView,
    EmployeeCityStatsView,
    DiaViajeListView,
    DiaViajeUpdateView
)

urlpatterns = [
    # Gestión de viajes
    path('viajes/new/', CrearViajeView.as_view(), name='nuevo_viaje'),
    path('viajes/<int:viaje_id>/', AprobarRechazarViajeView.as_view(), name='aprobar_rechazar_viaje'),
    path('viajes/<int:viaje_id>/iniciar/', IniciarViajeView.as_view(), name='iniciar_viaje'),
    path('viajes/<int:viaje_id>/end/', FinalizarViajeView.as_view(), name='finalizar_viaje'),
    path('viajes/<int:viaje_id>/cancelar/', CancelarViajeView.as_view(), name='cancelar_viaje'),
    path('viajes/<int:viaje_id>/finalizar_revision/', FinalizarRevisionViajeView.as_view(),
         name='finalizar_revision_viaje'),

    # Listado de viajes
    path('viajes/en-curso/', ViajeEnCursoView.as_view(), name='viaje_en_curso'),
    path('viajes/over/', ListarViajesFinalizadosView.as_view(), name='viajes-finalizados'),
    path('viajes/all/', ListarTodosLosViajesView.as_view(), name='viajes_todos'),
    path('viajes/pending/', PendingTripsDetailView.as_view(), name='pending-trips-count'),

    # Viajes por empleado
    path('empresas/<int:empresa_id>/empleados/<int:empleado_id>/viajes/pending/',
         PendingTripsByEmployeeView.as_view(), name='pending-trips-by-employee'),

    # Verificación y estadísticas
    # NOTA: Prefijadas con 'viajes/' para evitar conflicto con el router de empleados del módulo empresas
    path('viajes/empleados/viaje-en-curso/', VerificarViajeEnCursoView.as_view(), name='verificar_viaje_en_curso'),
    path('viajes/empleados/ciudades/', EmployeeCityStatsView.as_view(), name='employee_city_stats'),

    # Gestión de días de viaje
    path('viajes/<int:viaje_id>/dias/', DiaViajeListView.as_view(), name='dias-list'),
    path('viajes/<int:viaje_id>/dias/<int:dia_id>/', DiaViajeUpdateView.as_view(), name='dias-update'),
]
