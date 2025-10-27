# Plan de transición de estados para viajes

## Contexto

Actualmente el modelo `Viaje` maneja los estados `PENDIENTE`, `APROBADO`, `EN_CURSO`, `EN_REVISION`, `FINALIZADO` y `CANCELADO`. El flujo original contemplaba viajes programados a futuro y actualizaciones automáticas en función de la fecha. El nuevo proceso registra únicamente viajes que ya ocurrieron para validar gastos, por lo que sólo necesitamos conservar dos estados operativos:

- `EN_REVISION`: estado inicial por defecto al crear un viaje.
- `REVISADO`: estado final cuando la revisión administrativa concluye (sustituye al estado `FINALIZADO`).

Los estados `PENDIENTE`, `APROBADO`, `EN_CURSO` y `CANCELADO` dejan de tener sentido en este escenario.

## Objetivos

- Simplificar el ciclo de vida de los viajes al flujo `EN_REVISION → REVISADO`.
- Eliminar lógica y endpoints heredados que dependían de estados antiguos.
- Mantener la trazabilidad de gastos y revisiones sin estados intermedios obsoletos.
- Alinear scripts de datos, documentación y tests con el nuevo comportamiento.

## Roadmap técnico

1. **Modelos y migraciones**
   - Actualizar `users/models.py` para que `ESTADO_CHOICES` sólo contenga `EN_REVISION` y `REVISADO` (default `EN_REVISION`).
   - Crear migración que renombre el estado `FINALIZADO` a `REVISADO` y una data migration que mapée todos los estados anteriores (`PENDIENTE`, `APROBADO`, `EN_CURSO`, `CANCELADO`) a `EN_REVISION`, conservando los ya finalizados como `REVISADO`.

2. **Servicios de viajes (`users/viajes/services.py`)**
   - Ajustar `crear_viaje` para asignar siempre `EN_REVISION` y eliminar `determinar_estado_inicial` y validaciones de solape que ya no aplican.
   - Depurar funciones obsoletas (`iniciar_viaje`, `cancelar_viaje`, `aprobar_rechazar_viaje`, `tiene_viaje_en_curso`, `obtener_viaje_en_curso`) y revisar dependencias.
   - Mantener `procesar_revision_viaje` como único punto que cambia a `REVISADO`.

3. **Vistas (`users/viajes/views.py`)**
   - Retirar endpoints ligados a aprobación, inicio, cancelación y verificación de viajes en curso.
   - Actualizar listados para filtrar únicamente por `EN_REVISION` o `REVISADO` según corresponda.
   - Renombrar cualquier endpoint que aún haga referencia a “finalizar viaje” para reflejar la terminología “revisión completada”.

4. **Serializers y validadores**
   - Revisar validaciones que consultan `estado='PENDIENTE'` (por ejemplo en `ViajeSerializer`) y ajustarlas al nuevo flujo.
   - Verificar que `PendingTripSerializer` continúe funcionando con viajes en `EN_REVISION`.

5. **Tests y documentación**
   - Actualizar suites en `users/viajes/tests/` y `users/empresas/tests/` eliminando escenarios de estados eliminados.
   - Reescribir la documentación (`users/viajes/README.md`, `ANALISIS_LOGICA_VIAJES.md`) para reflejar el flujo reducido.

6. **Reportes, exportaciones y scripts**
   - Revisar `users/exportacion` y `users/reportes` para que no filtren por estados inexistentes ni excluyan `CANCELADO`.
   - Actualizar scripts de comandos (`users/management/commands/actualizar_viajes.py`, `create_sample_trips.py`, etc.) y cargas de datos de prueba.

7. **Frontend**
   - Ajustar consumidores para que trabajen sólo con `EN_REVISION` y `REVISADO`, adaptando filtros, textos y flujos de UI.

## Registro de ejecución

| Fecha | Responsable | Acción | Estado |
|-------|-------------|--------|--------|
| 2025-10-24 | Backend | Definir especificación final del flujo en el backend | Completado |
| 2025-10-24 | Backend | Implementar migraciones de modelo y datos | Completado |
| 2025-10-24 | Backend | Refactorizar servicios y vistas correspondientes | Completado |
| 2025-10-24 | Backend | Actualizar tests, documentación y scripts (parcial) | En progreso |
| _pendiente_ | Frontend | Adaptar integración frontend | Abierto |

Actualizaremos esta tabla conforme avancemos en cada hito.
