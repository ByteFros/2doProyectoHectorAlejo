"""
URLs del módulo de exportación
"""
from django.urls import path
from .views import (
    # Exportación CSV
    ExportMasterCSVView,
    ExportEmpresaCSVView,
    ExportViajesGastosView,
    ExportEmpleadoIndividualView,
    # Exportación ZIP
    ExportViajesGastosZipView,
    ExportEmpleadoIndividualZipView
)

urlpatterns = [
    # Exportación CSV
    path('export/viajes/exportar/', ExportMasterCSVView.as_view(), name='export_master_csv'),
    path('export/empresa/viajes/exportar/', ExportEmpresaCSVView.as_view(), name='export_empresa_csv'),
    path('export/viajes-gastos/', ExportViajesGastosView.as_view(), name='export_viajes_gastos'),
    path('export/empleado/<int:empleado_id>/viajes-gastos/', ExportEmpleadoIndividualView.as_view(),
         name='export_empleado_individual'),

    # Exportación ZIP
    path('export/viajes-gastos-zip/', ExportViajesGastosZipView.as_view(), name='export_viajes_gastos_zip'),
    path('export/empleado/<int:empleado_id>/viajes-gastos-zip/', ExportEmpleadoIndividualZipView.as_view(),
         name='export_empleado_individual_zip'),
]
