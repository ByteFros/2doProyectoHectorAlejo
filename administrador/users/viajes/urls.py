"""
URLs del módulo de viajes
"""
from django.urls import path
from .views import (
    CrearViajeView,
    ListarViajesRevisadosView,
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
    path('viajes/<int:viaje_id>/finalizar_revision/', FinalizarRevisionViajeView.as_view(),
         name='finalizar_revision_viaje'),

    # Listado de viajes
    path('viajes/revisados/', ListarViajesRevisadosView.as_view(), name='viajes-revisados'),
    path('viajes/all/', ListarTodosLosViajesView.as_view(), name='viajes_todos'),
    path('viajes/pending/', PendingTripsDetailView.as_view(), name='pending-trips-count'),

    # Viajes por empleado
    path('empresas/<int:empresa_id>/empleados/<int:empleado_id>/viajes/pending/',
         PendingTripsByEmployeeView.as_view(), name='pending-trips-by-employee'),

    # Verificación y estadísticas
    path('viajes/empleados/ciudades/', EmployeeCityStatsView.as_view(), name='employee_city_stats'),

    # Gestión de días de viaje
    path('viajes/<int:viaje_id>/dias/', DiaViajeListView.as_view(), name='dias-list'),
    path('viajes/<int:viaje_id>/dias/<int:dia_id>/', DiaViajeUpdateView.as_view(), name='dias-update'),
]
