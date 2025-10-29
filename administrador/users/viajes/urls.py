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
    CambiarEstadoViajeView,
    EmployeeCityStatsView,
    DiaViajeListView,
    DiaViajeReviewView
)

urlpatterns = [
    # Gestión de viajes
    path('viajes/new/', CrearViajeView.as_view(), name='nuevo_viaje'),
    path('viajes/<int:viaje_id>/transition/', CambiarEstadoViajeView.as_view(), name='viaje_transition'),

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
    path('dias/<int:dia_id>/review/', DiaViajeReviewView.as_view(), name='dias-review'),
]
