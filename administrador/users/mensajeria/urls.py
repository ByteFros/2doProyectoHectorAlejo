"""
URLs del módulo de mensajería
"""
from django.urls import path
from .views import (
    # Mensajes justificantes
    SolicitarJustificanteView,
    ListarMensajesView,
    ResponderMensajeView,
    CambiarEstadoJustificacionView,
    DescargarArchivoMensajeView,
    # Conversaciones
    CrearConversacionView,
    ListarConversacionesView,
    ListarMensajesByIdView,
    EnviarMensajeView,
    DescargarAdjuntoMensajeView
)

urlpatterns = [
    # Mensajes justificantes
    path('gastos/<int:gasto_id>/request-proof/', SolicitarJustificanteView.as_view(), name='solicitar_justificante'),
    path('mensajes/', ListarMensajesView.as_view(), name='listar_mensajes'),
    path('mensajes/<int:mensaje_id>/responder/', ResponderMensajeView.as_view(), name='responder_mensaje'),
    path('mensajes/<int:mensaje_id>/cambiar-estado/', CambiarEstadoJustificacionView.as_view(),
         name='cambiar_estado_justificante'),
    path('mensajes/justificante/<int:mensaje_id>/file/', DescargarArchivoMensajeView.as_view(),
         name='descargar_archivo_justificante'),
    path('mensajes/<int:mensaje_id>/file/', DescargarAdjuntoMensajeView.as_view(), name='descargar_adjunto_mensaje'),

    # Conversaciones
    path('conversaciones/', ListarConversacionesView.as_view(), name='listar_conversaciones'),
    path('conversaciones/crear/', CrearConversacionView.as_view(), name='crear_conversacion'),
    path('conversaciones/<int:conversacion_id>/mensajes/', ListarMensajesByIdView.as_view(), name='listar_mensajes'),
    path('mensajes/enviar/', EnviarMensajeView.as_view(), name='enviar_mensaje'),
]
