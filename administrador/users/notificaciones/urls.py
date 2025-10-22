"""
URLs del módulo de notificaciones
"""
from django.urls import path
from .views import (
    ListaNotificacionesView,
    CrearNotificacionView
)

urlpatterns = [
    # Gestión de notificaciones
    path('notificaciones/', ListaNotificacionesView.as_view(), name='lista_notificaciones'),
    path('notificaciones/crear/', CrearNotificacionView.as_view(), name='crear_notificacion'),
]
