# SOP Periodicidad de Visibilidad

Guía operativa para soporte sobre cómo gestionar la publicación diferida de viajes/gastos revisados.

---

## Roles y conceptos clave
- **Periodicidad**: Frecuencia con la que las empresas ven reflejadas las revisiones (`TRIMESTRAL` = 90 días, `SEMESTRAL` = 180 días por defecto).
- **Snapshots**: Copias congeladas de viajes/días/gastos revisados. Lo que ven usuarios `EMPRESA`/`EMPLEADO` proviene de aquí.
- **Cambios pendientes**: Cuando un MASTER modifica un viaje/gasto revisado o reabre un viaje, la empresa queda marcada con `has_pending_review_changes = True` hasta la siguiente publicación (manual o automática).
- **Liberación automática**: Cada vez que un usuario `EMPRESA`/`EMPLEADO` consulta un endpoint sensible, el backend verifica si llegó `next_release_at` o `manual_release_at` y publica en ese momento (“lazy publish”).

---

## Consultar estado actual
1. **Obtener la empresa**: `GET /api/users/empresas/{id}/` (MASTER o la propia empresa).
   - Campos relevantes: `periodicity`, `last_release_at`, `next_release_at`, `manual_release_at`, `has_pending_review_changes`.
2. **Ver notificaciones**: `GET /api/users/notificaciones/` (autenticado como la empresa).
   - Debe existir a lo sumo una notificación con `tipo = REVISION_FECHA_LIMITE` que indica la próxima liberación prevista.

---

## Cambiar periodicidad o fecha límite
Endpoint: `PATCH /api/users/empresas/{id}/` (MASTER o la propia empresa).

Campos útiles:
```json
{
  "periodicity": "SEMESTRAL",      // Opcional: TRIMESTRAL | SEMESTRAL
  "manual_release_at": "2025-07-15T00:00:00Z"  // Opcional: borrar/null para limpiar
}
```

Efectos inmediatos:
- Se recalcula `next_release_at` de acuerdo a la nueva periodicidad (si se cambió).
- Se actualiza o borra `manual_release_at` según el payload.
- Se regenera la notificación `REVISION_FECHA_LIMITE` con la nueva fecha.

> **Nota**: Si solo se desea limpiar la fecha manual, enviar `"manual_release_at": null`.

---

## Publicar manualmente (forzar release)
Endpoint exclusivo para MASTER: `POST /api/users/empresas/{id}/publish/`

Respuesta tipo:
```json
{
  "message": "Datos publicados correctamente",
  "empresa": {
    "...": "...",
    "last_release_at": "2025-04-10T09:30:00Z",
    "next_release_at": "2025-07-09T09:30:00Z",
    "has_pending_review_changes": false
  }
}
```

Qué ocurre:
- Se sincronizan los snapshots con los datos actuales en `Viaje/DiaViaje/Gasto`.
- Se limpian `has_pending_review_changes`, `manual_release_at` y `force_release`.
- Se recalcula `next_release_at = now + delta(periodicidad)`.
- Se actualiza la notificación `REVISION_FECHA_LIMITE`.

---

## Confirmar que los cambios se publicaron
1. Revisar `has_pending_review_changes` (debe quedar en `false`).
2. Volver a consultar `viajes`/`gastos` como empresa o empleado y verificar que aparecen los cambios de MASTER.
3. Revisar notificaciones: debe existir la nueva fecha límite.

---

## Flujo sugerido para soporte
1. **Verificar estado** (empresa y notificaciones).
2. **Modificar periodicidad/fechas** según solicitud.
3. **Publicar manualmente** si se requiere visibilidad inmediata.
4. **Comunicar al cliente** la próxima fecha de liberación (`next_release_at`).
5. **Recordar** que, aun sin release manual, al alcanzar la fecha o si el cliente navega después de la hora programada, los snapshots se sincronizan solos.

---

## Preguntas frecuentes

**Q: El cliente afirma que no ve los cambios que hizo el MASTER. ¿Qué hago?**  
A: Verifica `has_pending_review_changes`. Si está en `true`, publica manualmente (`POST /publish/`) o informa la fecha `next_release_at`. Tras el release, pide que refresquen el reporte/endpoint.

**Q: Necesito liberar datos antes de la fecha programada.**  
A: Usa `POST /empresas/{id}/publish/`. No hace falta modificar `manual_release_at` a menos que quieras agendar otra fecha específica.

**Q: Puedo establecer un calendario diferente para una empresa?**  
A: Sí, con `manual_release_at`. Puedes añadir cualquier `datetime` en UTC. El sistema publicará automáticamente cuando llegue esa fecha o si ejecutas un release manual antes.

**Q: Qué pasa si se elimina un gasto después de publicado?**  
A: La empresa seguirá viendo la última versión publicada hasta que se sincronice de nuevo (manual o automática). Tras el release, la empresa verá el gasto eliminado.

---

## Checklist de soporte
- [ ] Consulté el estado de la empresa (`last_release_at`, `next_release_at`, `has_pending_review_changes`).
- [ ] Ajusté periodicidad/fecha manual si me lo pidieron.
- [ ] Ejecuté `POST /publish/` cuando era necesario.
- [ ] Verifiqué notificaciones y estado final (`has_pending_review_changes = false`).
- [ ] Informé al cliente la próxima fecha de visibilidad (`next_release_at`). 
