"""
URLs del módulo de gastos
"""
from django.urls import path

from .views import (
    AprobarRechazarGastoView,
    CrearGastoView,
    GastoComprobanteDownloadView,
    GastoListView,
    GastoUpdateDeleteView,
)

urlpatterns = [
    # Gestión de gastos
    path('gastos/', GastoListView.as_view(), name='lista_gastos'),
    path('gastos/new/', CrearGastoView.as_view(), name='nuevo_gasto'),
    path('gastos/<int:gasto_id>/', AprobarRechazarGastoView.as_view(), name='aprobar_rechazar_gasto'),
    path('gastos/edit/<int:gasto_id>/', GastoUpdateDeleteView.as_view(), name='gasto_crud'),
    path('gastos/<int:gasto_id>/file/', GastoComprobanteDownloadView.as_view(), name='gasto_archivo'),
]
