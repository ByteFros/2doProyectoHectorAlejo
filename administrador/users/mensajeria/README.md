# Módulo de mensajería

Permite que usuarios con roles MASTER, EMPRESA y EMPLEADO intercambien mensajes 1:1. Incluye:

* Árbol de contactos filtrado por rol (`ContactListView`).
* Creación de conversaciones privadas (`CrearConversacionView`).
* Listado y envío de mensajes con adjuntos (`ListarMensajesByIdView`, `EnviarMensajeView`, `DescargarAdjuntoMensajeView`).
* Control de lecturas por participante para saber si hay mensajes pendientes (`ConversacionLectura`).

## API principales

| Método | Ruta | Descripción | Notas |
| --- | --- | --- | --- |
| GET | `/api/users/contacts/` | Devuelve masters, empresas y empleados visibles para el usuario autenticado. | Estructura jerárquica para construir la libreta de contactos. |
| GET | `/api/users/admin-contact/` | Lista sólo usuarios MASTER. | Útil para atajos rápidos desde empresas/empleados. |
| GET | `/api/users/conversaciones/` | Conversaciones del usuario con `last_message` y `has_unread`. | Prefetch de participantes y lecturas. |
| POST | `/api/users/conversaciones/crear/` | Inicia una conversación 1:1. | Valida relaciones (empresa-empleado, master, etc.). |
| GET | `/api/users/conversaciones/<id>/mensajes/` | Mensajes ordenados por fecha ascendente. | Marca la conversación como leída para el solicitante. |
| POST | `/api/users/mensajes/enviar/` | Envía un mensaje con texto y/o archivo. | Crea conversación si sólo se pasa `to_user_id`. Requiere `multipart/form-data`. Archivos >10 MB se rechazan y, si el adjunto es una imagen, se comprime automáticamente (máx. 1920 px, 1–2 MB). |
| GET | `/api/users/mensajes/<id>/file/` | Descarga el adjunto de un mensaje. | Verifica que el usuario participe en la conversación. |

### Adjuntos y compresión de imágenes

* El endpoint `POST /api/users/mensajes/enviar/` acepta archivos mediante `multipart/form-data`. Se debe enviar al menos `contenido` o `archivo`.
* El límite duro por adjunto es **10 MB**; el servidor devuelve 400 si se intenta subir un archivo mayor.
* Cuando el archivo es una imagen (JPEG, PNG, WebP, etc.) se optimiza automáticamente: se corrige la orientación EXIF, se limita la dimensión larga a **1920 px** y se re-encodea (WebP/JPEG) apuntando a 1–2 MB para mantener la legibilidad.
* Los archivos que no son imágenes (PDF, TXT, ZIP, etc.) no se modifican y se guardan tal cual.
* La descarga (`GET /mensajes/<id>/file/`) siempre expone el archivo final almacenado tras la optimización.

## Estado de lectura (pull)

El backend persiste la última lectura por usuario mediante `ConversacionLectura` (`users/models.py`). Cada vez que se lista una conversación se adjunta `has_unread`, calculado así:

1. Obtener el mensaje más reciente (`obj.mensajes.order_by('-fecha_creacion').first()`).
2. Buscar la marca de lectura del usuario. Si no existe o es nula, se asume pendiente.
3. Comparar `last_message.fecha_creacion > last_read_at`.

Las marcas se actualizan automáticamente en dos puntos:

* `GET /conversaciones/<id>/mensajes/`: después de recuperar el queryset, se registra `last_read_at` con la fecha del último mensaje mostrado.
* `POST /mensajes/enviar/`: tras crear el mensaje, se marca la conversación como leída para el autor (evita falsos pendientes con sus propios mensajes).

## Flujo frontend actual

1. **Listar conversaciones**: llamar a `GET /api/users/conversaciones/` y mostrar un badge por cada item donde `has_unread` sea `true`. Para un indicador global, basta con evaluar si existe al menos una conversación con ese flag.
2. **Abrir conversación**: invocar `GET /api/users/conversaciones/<id>/mensajes/` antes de renderizar el detalle. Esta lectura actualiza el backend; al volver a la lista, refrescarla para ver el estado limpio.
3. **Enviar mensaje**: usar `POST /api/users/mensajes/enviar/`. La respuesta trae `conversation_id`; refrescar la vista de mensajes si se trata de una nueva conversación.
4. **Polling / alertas**: dado que no hay push, el cliente decide la frecuencia de refresco (al abrir la pestaña, cada cierto tiempo, etc.). Mientras se consulte la lista con regularidad, los pendientes se reflejarán vía `has_unread`.

Consideraciones:

* El seguimiento es por usuario autenticado; cada participante mantiene su propia marca.
* Para “marcar leído” de fondo, basta con consumir `GET /conversaciones/<id>/mensajes/` (aunque no se rendericen los datos).
* El módulo no interactúa con el sistema general de notificaciones (`users.notificaciones`); cualquier banner debe decidirlo el frontend.

## Hoja de ruta hacia WebSockets

La arquitectura actual es 100% HTTP pull. Para evolucionar hacia WebSockets/tempo real se recomienda:

1. **Infraestructura**: introducir Django Channels (o stack equivalente) y configurar un backend de WebSocket (Redis para channel layer, workers ASGI, etc.).
2. **Suscripción**: al autenticar al usuario, abrir un socket y suscribirlo a rooms basadas en sus conversaciones (p. ej. `conversation_<id>`). El servidor debe exponer un consumer que valide permiso antes de unir al room.
3. **Eventos**:
   * `message.new`: emitido cuando se crea un `Mensaje`. Incluir contenido serializado y, opcionalmente, un indicador para que el receptor actualice `has_unread` localmente sin reconsultar.
   * `message.read`: cuando el cliente abra una conversación, además de llamar al endpoint actual (para compatibilidad), puede enviar un evento indicando `last_read_message_id`. El backend actualiza `ConversacionLectura` y retransmite el evento a otros participantes para reflejar “visto”.
4. **Compatibilidad**: mantener los endpoints REST para clientes legacy o en caso de reconexiones. El socket actuaría como capa adicional (optimiza la latencia, pero no es el único camino).
5. **Escalabilidad**: definir límites de reconexión, heartbeat y colas para evitar perder eventos. Documentar cómo retomar via REST si se pierde un socket.

Con esta migración, el frontend podría reaccionar en tiempo real ante nuevos mensajes o lecturas, reduciendo la necesidad de polling constante. Mientras tanto, el flujo descrito arriba sigue siendo la referencia oficial.
