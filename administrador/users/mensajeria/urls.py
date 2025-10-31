"""
URLs del módulo de mensajería
"""
from django.urls import path
from .views import (
    ContactListView,
    AdminContactView,
    CrearConversacionView,
    ListarConversacionesView,
    ListarMensajesByIdView,
    EnviarMensajeView,
    DescargarAdjuntoMensajeView
)

urlpatterns = [
    path('contacts/', ContactListView.as_view(), name='contact_list'),
    path('admin-contact/', AdminContactView.as_view(), name='admin_contact'),
    path('conversaciones/', ListarConversacionesView.as_view(), name='listar_conversaciones'),
    path('conversaciones/crear/', CrearConversacionView.as_view(), name='crear_conversacion'),
    path('conversaciones/<int:conversacion_id>/mensajes/', ListarMensajesByIdView.as_view(), name='listar_mensajes'),
    path('mensajes/enviar/', EnviarMensajeView.as_view(), name='enviar_mensaje'),
    path('mensajes/<int:mensaje_id>/file/', DescargarAdjuntoMensajeView.as_view(), name='descargar_adjunto_mensaje'),
]
