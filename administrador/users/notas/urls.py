"""
URLs del módulo de notas
"""
from django.urls import path
from .views import (
    NotaViajeListCreateView,
    NotaViajeDeleteView
)

urlpatterns = [
    # Gestión de notas de viajes
    path('notas/<int:viaje_id>/', NotaViajeListCreateView.as_view(), name='notas_viaje'),
    path('notas/delete/<int:nota_id>/', NotaViajeDeleteView.as_view(), name='eliminar_nota'),
]
