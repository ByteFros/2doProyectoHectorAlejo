# Módulo de viajes

## Endpoint para validar días en lote

- **URL:** `PUT /api/users/dias/review/batch/`
- **Payload:**
  ```json
  {
    "dia_ids": [583, 584, 585],
    "exento": true
  }
  ```
- `dia_ids` debe ser una lista de IDs de `DiaViaje` pertenecientes al mismo dominio del usuario autenticado.
- `exento` define si esos días se marcan como exentos (se actualiza también el estado de los gastos asociados: `APROBADO`/`RECHAZADO`).
- **Permisos:**
  - MASTER puede modificar cualquier día.
  - EMPRESA sólo puede modificar días de viajes de su empresa.
  - EMPLEADO no puede validar días.
- **Respuesta:**
  ```json
  {
    "message": "Se actualizaron 5 días de viaje",
    "count": 5,
    "estado_gastos": "APROBADO"
  }
  ```

Usa este endpoint desde el frontend para seleccionar múltiples días (o todos) en una sola operación en lugar de enviar docenas de peticiones individuales a `/dias/<id>/review/`.
