# Plan de migración de endpoints de viajes a ViewSets

## Contexto

El módulo de viajes está compuesto principalmente por clases `APIView` con rutas definidas manualmente. Aunque esto funciona, genera duplicación de lógica (serialización, validación, permisos) y dificulta aprovechar características nativas de DRF como routers, filtrado o acciones personalizadas. Dado que aún no hay consumidores externos que dependan de estas URLs, tenemos margen para reestructurar los endpoints antes de que se utilicen en producción.

## Objetivos

- Centralizar la gestión de viajes en un `ModelViewSet`.
- Estandarizar rutas REST (`/viajes/`, `/viajes/{id}/`, etc.) usando `DefaultRouter`.
- Trasladar lógica repetida (permisos, validaciones por rol, serialización) a un único punto.
- Exponer acciones especiales (finalizar revisión, reabrir, ver pendientes) como `@action`.
- Mantener endpoints auxiliares necesarios (revisión de días) pero revisando su coherencia.
- Actualizar documentación y pruebas para reflejar la nueva estructura.

## Cambios propuestos

1. **Crear `ViajeViewSet`**
   - Basado en `ModelViewSet`.
   - Sobrescribir `get_queryset()` para devolver viajes según el rol del usuario (MASTER ve todos, EMPRESA sólo los suyos, EMPLEADO sólo su viaje).
   - Usar un serializer base (`ViajeSerializer`) y, si hace falta, serializers alternos para listados simplificados.

2. **Registrar el ViewSet en un router**
   - `router.register('viajes', ViajeViewSet)`.
   - Esto expone automáticamente `GET /viajes/`, `POST /viajes/`, `GET /viajes/{id}/`, `PUT/PATCH /viajes/{id}/`, `DELETE /viajes/{id}/`.
   - Ajustar o eliminar las rutas manuales actuales (`/viajes/new/`, `/viajes/all/`, etc.).

3. **Migrar endpoints personalizados a `@action`**
   - **Finalizar revisión** → `@action(detail=True, methods=['post'])`.
   - **Reabrir viaje** → `@action(detail=True, methods=['patch'])`.
   - **Pendientes** → `@action(detail=False, methods=['get'])` (con filtros `?empresa=`, `?empleado=`).
   - **Viajes revisados** → `list` filtrado por query param (`?estado=REVISADO`) o `@action` adicional, según convenga.

4. **Gestión de días**
   - `GET /viajes/{id}/dias/` puede convertirse en `@action(detail=True, methods=['get'], url_path='dias')`.
   - Mantener `PUT /dias/{dia_id}/review/` como vista independiente o considerar un `DiaViewSet` si se desea gestionar días de forma uniforme.

5. **Permisos y validaciones**
   - Centralizar en el ViewSet la lógica de roles (p.ej. `get_permissions()` según acción).
   - Reutilizar permisos existentes (`CanViewPendingReviews`, etc.) mediante `permission_classes` dentro de cada `@action`.

6. **Documentación**
   - Actualizar `users/viajes/README.md` para reflejar rutas estándar (`/viajes/`, `/viajes/{id}/`).
   - Documentar las acciones (`/viajes/{id}/finalizar_revision/`, `/viajes/{id}/reabrir/`, `/viajes/pending/`) y sus query params.
   - Aclarar cómo se obtiene el listado de días (`/viajes/{id}/dias/`) y cómo se revierten gastos/días.

7. **Pruebas**
   - Adaptar tests que consumen rutas antiguas para usar los nuevos endpoints (`reverse('viaje-list')`, `reverse('viaje-detail', args=[...])`, etc.).
   - Agregar pruebas para las acciones personalizadas dentro del ViewSet.

## Beneficios esperados

- Rutas más coherentes y fáciles de consumir desde frontend.
- Menos código repetido en vistas (`APIView`).
- Uso pleno de funcionalidades DRF (router, actions, filtros).
- Facilita extender el módulo (p.ej. nuevos filtros, paginación, permisos por acción).

## Impacto

- Cambian las URLs actuales, por lo que hay que coordinar con frontend antes de desplegar.
- Las pruebas y documentación deben actualizarse en paralelo.
- Los endpoints auxiliares (día, gastos) seguirán disponibles, con nombres y rutas revisadas para mantener claridad.

## Próximos pasos

1. Implementar `ViajeViewSet` y adaptar rutas.
2. Migrar lógica existente (listados, creación, acciones) al ViewSet.
3. Revisar permisos/serializers en función del rol.
4. Ajustar documentación y tests.
5. Validar con datos de prueba y scripts (`create_sample_trips`, `create_sample_expenses`).

Una vez completada esta migración, el módulo de viajes quedará mejor alineado con el patrón REST de DRF, simplificando el mantenimiento y futuras extensiones.

