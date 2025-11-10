# Módulo de gastos

Gestiona el ciclo de vida de los gastos asociados a viajes: creación por parte de los empleados, revisión/aprobación por empresas o masters, y descarga de comprobantes.

## Endpoints principales

| Método | Ruta | Descripción | Notas |
| --- | --- | --- | --- |
| GET | `/api/users/gastos/` | Lista de gastos visibles para el usuario (según rol y snapshots). | Empareja datos “live” y snapshots si el viaje está revisado. |
| POST | `/api/users/gastos/new/` | Registro de un gasto por un empleado. | Requiere `multipart/form-data` para adjuntar comprobantes. |
| PATCH | `/api/users/gastos/edit/<id>/` | Edición parcial de un gasto propio. | Restringe campos cuando el viaje está `REABIERTO`. |
| DELETE | `/api/users/gastos/edit/<id>/` | Elimina un gasto (si el viaje no está `REABIERTO`). | |
| PUT | `/api/users/gastos/<id>/` | Aprueba o rechaza un gasto (EMPRESA/MASTER). | Cambios en viajes revisados marcan `has_pending_review_changes`. |
| GET | `/api/users/gastos/<id>/file/` | Descarga del comprobante. | Responde inline si existe archivo. |

## Adjuntos y compresión

* **Límite de tamaño**: cada comprobante tiene un máximo de **10 MB**. Se devuelve 400 si se excede, tanto en la creación como en la actualización.
* **Procesamiento automático**: cuando el archivo es una imagen (JPEG/PNG/WebP, etc.) se corrige la orientación EXIF, se limita el lado más largo a **1920 px** (modo detalle hasta 2560 px) y se re-encodea a WebP/JPEG apuntando a 1–2 MB. Archivos no-imagen se mantienen intactos.
* **Aplicación universal**: la compresión ocurre tanto en el serializer (`GastoSerializer`) como en los servicios (`crear_gasto`/`actualizar_gasto`) para cubrir cualquier flujo que escriba comprobantes.
* **Descarga**: la ruta `/gastos/<id>/file/` devuelve el archivo ya optimizado que quedó almacenado tras el procesamiento. |

## Flujo resumido

1. El empleado crea un gasto (`POST /gastos/new/`) enviando `viaje_id`, `concepto`, `monto`, `fecha_gasto` y opcionalmente `comprobante`. El backend valida que el viaje no esté revisado y que el archivo cumpla el límite.
2. Si el viaje está `REABIERTO`, sólo se permite subir/actualizar el comprobante; los demás campos quedan bloqueados hasta que cambie el estado.
3. Masters/empresas utilizan `PUT /gastos/<id>/` para aprobar o rechazar. Cuando el viaje ya fue revisado, cualquier cambio obliga a sincronizar snapshots y marca `has_pending_review_changes` en la empresa.
4. Los listados combinan gastos en vivo y snapshots (si el viaje tiene versión publicada) para garantizar visibilidad consistente.

## Tests relevantes

`users/gastos/tests/test_adjuntos.py` contiene pruebas de integración que verifican:

* Compresión efectiva al crear y actualizar comprobantes.
* Rechazo de archivos mayores a 10 MB.
* Preservación de archivos no-imagen (mediante pruebas específicas para texto/PDF en otros módulos).

Mantén este archivo actualizado cuando se introduzcan nuevas reglas (límite distinto, nuevos tipos de archivo permitidos, etc.).
