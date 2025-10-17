"""
URLs del módulo de empresas y empleados usando DRF Routers
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .viewsets import EmpresaViewSet, EmpleadoViewSet

# Crear router y registrar ViewSets
router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'empleados', EmpleadoViewSet, basename='empleado')

# URLs generadas automáticamente por el router:
# GET    /empresas/                       -> list (listar empresas)
# POST   /empresas/                       -> create (crear empresa)
# GET    /empresas/{id}/                  -> retrieve (detalle empresa)
# PUT    /empresas/{id}/                  -> update (actualizar empresa)
# PATCH  /empresas/{id}/                  -> partial_update (actualizar permisos)
# DELETE /empresas/{id}/                  -> destroy (eliminar empresa)
#
# GET    /empleados/                      -> list (listar empleados)
# POST   /empleados/                      -> create (crear empleado)
# GET    /empleados/{id}/                 -> retrieve (detalle empleado)
# PUT    /empleados/{id}/                 -> update (actualizar empleado)
# PATCH  /empleados/{id}/                 -> partial_update (actualizar parcial)
# DELETE /empleados/{id}/                 -> destroy (eliminar empleado)
# POST   /empleados/batch-upload/         -> batch_upload (carga masiva CSV)
# GET    /empleados/pending/              -> pending (empleados con viajes EN_REVISION)

urlpatterns = [
    path('', include(router.urls)),
]
