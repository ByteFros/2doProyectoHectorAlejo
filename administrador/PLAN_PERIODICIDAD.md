# Plan de Implementación Periodicidad Empresas

## Objetivo
Incorporar un mecanismo de visibilidad diferida para usuarios con rol `EMPRESA`, de modo que las modificaciones realizadas por `MASTER` sobre viajes/gastos revisados (estado, días exentos, importes, etc.) sólo sean visibles cuando se cumpla una periodicidad configurable (trimestral o semestral) o cuando se dispare manualmente una publicación anticipada.

## Resumen de Alcance
- Añadir campos de periodicidad y control de publicación al modelo `EmpresaProfile`.
- Introducir snapshots de datos "publicados" para viajes, días y gastos revisados, accesibles por empresas/empleados.
- Sincronizar snapshots siguiendo la periodicidad o al recibir un release manual.
- Adaptar endpoints afectados para servir siempre los datos publicados cuando el consumidor es `EMPRESA` o `EMPLEADO`.
- Gestionar notificaciones que informen la fecha límite de revisión vigente para cada empresa.
- Definir herramientas (API/comando) para forzar publicación o fijar fechas límite personalizadas.
- Cubrir el comportamiento con pruebas unitarias e integrales.

---

## Fase 1 · Modelo y Migraciones
1. **Campos en `EmpresaProfile`:**
   - `periodicity` (`choices=[TRIMESTRAL, SEMESTRAL]`, default configurable).
   - `last_release_at` (DateTimeField, nullable).
   - `next_release_at` (DateTimeField, nullable, opcional si preferimos cálculo on the fly).
   - `manual_release_at` (DateTimeField, nullable) y `force_release` (BooleanField, default `False`).
2. **Tablas de snapshots** para la capa publicada:
   - `ViajeReviewSnapshot` con FK → `Viaje` e información congelada (estado revisado, fechas, destinos, días viajados, flags de revisión, referencias a gastos).
   - `DiaViajeSnapshot` y `GastoReviewSnapshot` ligados a los anteriores para reflejar días exentos/no exentos y estados de gastos revisados.
   - Cada snapshot incluye `published_at` y garantiza unicidad por entidad origen.
3. Migraciones + valores iniciales:
   - Scripts para poblar snapshots con la situación actual de viajes/gastos en estado `REVISADO`.
   - Setear `last_release_at` y `next_release_at` según la periodicidad default.
   - Generar notificación inicial por empresa con la fecha límite calculada.

## Fase 2 · Servicios y Dominios
1. Servicio en `users.common.services` (o módulo nuevo) con utilidades:
   - `get_periodicity_delta(empresa)` → `timedelta`.
   - `ensure_company_is_up_to_date(empresa)`:
     - Si `force_release` o `manual_release_at` vencido → sincroniza y resetea flags.
     - Si `next_release_at` alcanzado → sincroniza y avanza ciclo.
   - `sync_company_review_snapshots(empresa)` que replica viajes/días/gastos revisados al esquema publicado.
2. Hooks sobre modelos de revisión: ✅
   - Al marcar un `Viaje` como `REVISADO` (creación o update) se marca la empresa con cambios pendientes.
   - Ediciones posteriores hechas por `MASTER` sobre viajes/días/gastos revisados marcan `has_pending_review_changes`.
3. Opcional: flag `has_pending_review_changes` en `EmpresaProfile` para detección rápida de pendientes. ✅
4. Servicio auxiliar `sync_company_review_notification(empresa)` que crea/actualiza la notificación de fecha límite (elimina la anterior si existe) siempre que cambie la periodicidad o se reprograme la fecha. ✅

## Fase 3 · Integración en Endpoints
1. Centralizar acceso visible para empresas/empleados: ✅
   - Helper `get_visible_viajes(user)` que:
     - Para `MASTER`: devuelve queryset real.
     - Para `EMPRESA`/`EMPLEADO`: ejecuta `ensure_company_is_up_to_date` y retorna snapshots.
   - Endpoints de viajes, días exentos y gastos reutilizan el helper para garantizar visibilidad diferida. ✅
2. Revisar reportes (`CompanyTripsSummaryView`, `TripsTypeView`, `ExemptDaysView`, reportes de gastos, etc.) para que consuman snapshots cuando el consumidor no sea `MASTER`. ✅ (reportes principales migrados; resta validar exportaciones / listados directos)
3. Ajustar serializadores para que sepan mapear datos provenientes de snapshots sin romper la respuesta actual. ✅ (CompanyTripsSummary y period updates cubiertos)

## Fase 4 · Controles y Operativa
1. Endpoint o acción administrable (`POST /empresas/{id}/publish/`) disponible sólo para `MASTER`:
   - Marca `force_release=True` o ejecuta sincronización directa. ✅
2. Permitir `PATCH /empresas/{id}/manual-release-at` para fijar una fecha límite exacta. ✅ (via EmpresaViewSet)
3. Comando de management opcional (`manage.py release_empresas --all` / `--empresa ID`) para sincronizaciones programadas (cron). *(Pendiente)*
4. Documentar proceso para soporte (cómo forzar, cómo resetear periodicidad, cómo se envían/actualizan notificaciones). *(Pendiente)*

---

## Estrategia de Publicación
1. **Feature flag (opcional)**: activar la lógica de snapshots gradualmente mediante setting o flag.
2. **Migración controlada**: desplegar migraciones con la app en modo mantenimiento (o en ventana de baja actividad) para generar snapshots iniciales.
3. **Monitorización**: registrar logs cuando se sincronizan empresas, se aplican releases manuales o cuando un usuario empresa consulta antes de tiempo.
4. **Rollout progresivo**:
   - Activar para un subconjunto de empresas (si usamos flag per company).
   - Confirmar con usuarios clave antes de habilitar globalmente.

---

## Plan de Pruebas
### Unitarias
- `get_periodicity_delta` devuelve delta correcto para cada periodicidad.
- `ensure_company_is_up_to_date`:
  - Publica cuando `next_release_at` llega.
  - Responde al flag `force_release`.
  - Respeta `manual_release_at` y lo limpia tras publicar.
- `sync_company_review_snapshots` replica correctamente viajes/días/gastos.
- Hooks de `Viaje`/`DiaViaje`/`Gasto` crean y actualizan snapshots sólo cuando procede.
- `sync_company_review_notification` crea, actualiza y reemplaza notificaciones sin duplicados.

### Integración
- **Flujo base**: empresa crea viaje y el MASTER lo marca `REVISADO` → empresa ve datos inmediatos.
- **Cambios diferidos**: MASTER ajusta un viaje/gasto ya revisado → empresa sigue viendo snapshot antiguo hasta `next_release_at`.
- **Forzar release**: llamada al endpoint/admin → empresa ve datos actualizados al instante.
- **Manual release date**: fijar fecha futura → verificar que sólo publica al alcanzarla.
- **Endpoints**:
  - Listas de viajes/gastos entregan snapshots para empresa/empleado y datos reales para MASTER. ✅
  - Detalles puntuales (viaje individual, gasto individual) siguen pendientes de revisión si se requiere congelar esos responses.
  - Reportes (`CompanyTripsSummaryView`, exentos, gastos) muestran cifras consistentes con la visibilidad publicada. ✅
- **Notificaciones**:
  - Crear empresa (periodicidad inicial) → existe una única notificación con la fecha límite correcta.
  - Cambiar periodicidad (3→6 meses) o ajustar manualmente la fecha → notificación previa eliminada/reemplazada con nuevo mensaje.

### End-to-End (opcional)
- Simular empresa con periodicidad trimestral, introducir cambios revisados, avanzar reloj (usando `freeze_time` o similar) y confirmar liberación automática.

---

## Próximos Pasos
1. Validar con stakeholders exactamente qué atributos de viajes/días/gastos deben congelarse (estado, montos, notas, adjuntos, etc.).
2. Confirmar defaults de periodicidad y comportamiento para empresas existentes.
3. Preparar documentación para equipo de soporte/operaciones sobre cómo manejar releases manuales y revisar las notificaciones generadas. ✅ (ver `SOP_PERIODICIDAD.md`)
4. (Descartado) No se implementará cron por ahora; el enfoque lazy on demand es suficiente.
