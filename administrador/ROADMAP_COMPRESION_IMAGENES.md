# Roadmap — Compresión de Imágenes en Uploads

## Contexto y Objetivos
- **Problema**: Los archivos subidos (chat `Mensaje.archivo` y gastos `Gasto.comprobante`) se almacenan sin optimización, ocupan demasiado espacio y ralentizan transferencias.
- **Meta**: Reducir sistemáticamente el peso de las imágenes sin degradar perceptiblemente la calidad y sin romper los flujos actuales de mensajería ni gastos.
- **Alcance**: Solo imágenes (JPEG/PNG/WebP/HEIC, etc.). Otros tipos de archivo deben seguir subiendo sin cambios.

## Consideraciones Técnicas Previas
- Se añadirá `Pillow` (o `pillow-simd`) en `requirements.txt`. El contenedor Docker deberá reconstruirse para incluir las librerías del sistema necesarias (ej. `libjpeg`).
- Crear un helper centralizado (`users/common/files.py`) para detectar, comprimir y devolver un `ContentFile`. El helper debe:
  - Validar tipo real via `Pillow` (no solo extensión).
  - Respetar orientación EXIF y limitar dimensiones (p. ej. 1920px largo máximo).
  - Re-encodear a WebP/JPEG según transparencia, con calidad configurable (70–80%).
  - Rechazar imágenes corruptas o mayores al límite definido (ej. 10 MB).
- Las vistas que aceptan archivos deben garantizar `MultiPartParser` y límites de tamaño a nivel de servidor (Django + Nginx/Caddy).
- Registrar en BD/response el peso final para monitorear la ganancia.

## Fases de Implementación

### Fase 0 — Preparación
- [x] Medir el estado actual: contar tamaño total de `mensajes_adjuntos/` y `comprobantes/` y casos representativos.  
  Comandos ejecutados:
  - `du -sh media/mensajes_adjuntos media/comprobantes`
  - `python3 - <<'PY' ...` (script puntual para total/promedio/máximo y porcentaje >5 MB/>10 MB).  
  Resultados al 2025-11-10:
  - `media/mensajes_adjuntos`: 7.01 MB totales, 10 archivos, promedio 718 KB, máximo 2.22 MB, 0 % >5 MB.
  - `media/comprobantes`: 9.90 MB totales, 166 archivos, promedio 61 KB, máximo 1.91 MB, 0 % >5 MB.
- [x] Definir KPIs: % de reducción esperado, tiempo de procesamiento máximo por archivo, límites de tamaño aceptables.  
  - **Reducción de peso**: objetivo ≥ 65 % respecto al original, con tamaño final entre 1 MB y 2 MB; se permite hasta 2.5 MB en imágenes de facturas complejas.  
  - **Resolución máxima**: 1920 px en el lado más largo (2560 px para modo “detalle factura”).  
  - **Tiempo de procesamiento**: ≤ 1.5 s por imagen de 10 MB en el entorno Docker objetivo; alertar si se supera 2 s.  
  - **Tasa de error**: < 1 % de cargas rechazadas por compresión (excluye errores de tamaño o formato inválido reportados al usuario).  
  - **Límites de subida**: 10 MB pre‑compresión (rechazo 413/400 si supera), 12 MB límite global de request para contemplar overhead de multipart.
- [x] Ajustar configuraciones de upload (tamaño máximo, tipos permitidos) a nivel Django/Reverse proxy.  
  Plan inicial:
  - Django: setear `FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024` (límite duro por archivo) y `DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024` (para dar margen al multipart) en `administrador/settings.py`.
  - Validadores: aplicar `FileExtensionValidator` + chequeo de tamaño en `MensajeSerializer`/`GastoSerializer` (o en el helper) para devolver un 400 más expresivo cuando exceda 10 MB.
  - Reverse proxy: en `Caddyfile` agregar `request_body { max_size 12MB }` dentro del bloque principal para rechazar cargas grandes antes de llegar a Django.
  - Documentar el nuevo límite en las guías de usuarios (chat y gastos) y en cualquier cliente móvil/web.

### Fase 1 — Infraestructura de Compresión
- [x] Agregar `Pillow` a `requirements.txt` y reconstruir la imagen Docker local.
- [x] Implementar `users/common/files.py` con `compress_if_image(...)` (redimensiona, corrige EXIF y re-encodea a WebP/JPEG).
- [x] Escribir tests unitarios para el helper (`users/common/tests/test_files.py`) validando:
  - Identificación correcta de imágenes/no-imágenes.
  - Mantenimiento de proporciones/orientación (limita a 1920 px/2560 px según modo).
  - Reducción de tamaño frente al archivo original.

### Fase 2 — Integración en Mensajería
- [x] Asegurar que `EnviarMensajeView` use `MultiPartParser` explícitamente.
- [x] Invocar `compress_if_image` antes de llamar a `Mensaje.objects.create`.
- [x] Validar respuesta API (archivo optimizado disponible) y añadir tests de la vista (`users/mensajeria/tests/test_mensajeria.py`).
- [x] Documentar en `users/mensajeria/README.md` el nuevo comportamiento y límites.

### Fase 3 — Integración en Gastos
- [x] Reutilizar el helper en `GastoSerializer.create`/`update` y servicios para forzar compresión y asegurar máximos de 1920 px (detalle 2560 px).
- [x] Incluir validaciones adicionales (tamaño máximo 10 MB) y rechazar adjuntos que superen el límite antes de procesarlos.
- [x] Tests de API para crear/actualizar gasto con comprobante optimizado (`users/gastos/tests/test_adjuntos.py`).
- [x] Actualizar documentación del flujo de gastos/notas de release (`users/gastos/README.md`).

### Fase 4 — Procesamiento Asíncrono (Opcional / según métricas)
- [ ] Si aparecen cuellos de botella, evaluar mover la compresión a una cola (Celery/BullMQ): guardar temporal, encolar, reemplazar archivo.
- [ ] Añadir un estado “procesando adjunto” en la respuesta para manejar este modo.
- [ ] Monitorear tiempos de cola y errores de workers.

### Fase 5 — Migración y Operación Continua
- [ ] (Opcional) Crear un management command para iterar sobre adjuntos existentes y recomprimirlos. No prioritario porque el entorno productivo se desplegará limpio sin datos legacy.
- [ ] Revisar políticas de backup/retención tras la reducción de peso.
- [ ] Configurar métricas y alertas (p. ej. Prometheus/Grafana o logs estructurados) sobre:
  - Tiempos de compresión.
  - Ratio de aciertos (imágenes comprimidas / uploads totales).
  - Errores de procesamiento.
- [ ] Preparar checklist de despliegue Docker (build, push, migraciones, pruebas de smoke).

## Testing & QA en Cada Fase
- Unit tests del helper (`pytest`/`unittest`).
- Tests de integración de APIs de mensajería y gastos usando imágenes reales pequeñas y grandes.
- Validación manual en staging: subir distintos formatos desde clientes reales (web/móvil) y descargar para evaluar calidad.
- Monitoreo tras despliegue: revisar logs y métricas al menos 48 h, con rollback plan listo si se detecta degradación.

---
**Notas**: Este roadmap es incremental. Cada fase debe cerrarse con resultados documentados (tamaño promedio antes/después, incidencias) antes de pasar a la siguiente, asegurando que el despliegue en Docker producción se haga solo cuando las dependencias y tests estén validados en el entorno containerizado.
