# Migración a JWT

Este documento define el plan para reemplazar la autenticación basada en `TokenAuthentication` por **JWT con expiración controlada**.

## Objetivos

- Emitir `access` y `refresh` tokens con tiempos de vida configurables.
- Forzar re‑inicio de sesión cuando el `refresh` expire o se coloque en blacklist.
- Simplificar la invalidez de tokens desde el backend (logout → blacklist).
- Garantizar compatibilidad con el frontend actual (Axios) una vez se actualice a `Bearer` tokens.

## Fase 1 · Preparación backend

1. **Dependencias**
   - Agregar `djangorestframework-simplejwt` al `requirements.txt`.
   - Habilitar `rest_framework_simplejwt.token_blacklist` en `INSTALLED_APPS`.
2. **Settings y entorno**
   - Definir variables de entorno:
     - `JWT_ACCESS_TTL_MINUTES` → duración del access token.
     - `JWT_REFRESH_TTL_DAYS` → duración del refresh token.
     - `JWT_ROTATE_REFRESH_TOKENS` / `JWT_BLACKLIST_AFTER_ROTATION` (booleans).
   - Configurar `SIMPLE_JWT` en `settings.py` leyendo dichos valores.
   - Actualizar `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` para usar `JWTAuthentication`.
3. **Hardening**
   - Registrar `SIMPLE_JWT['SIGNING_KEY']` sólo si se requiere una clave distinta a `SECRET_KEY`.
   - Documentar políticas de rotación y ubicación segura de los tokens (no cookies si se decide usar storage).

## Fase 2 · Sustituir endpoints

1. **Login**
   - Crear `CustomTokenObtainPairSerializer` que extienda `TokenObtainPairSerializer` y añada al payload `role`, `must_change_password`, `empresa_id` / `empleado_id`.
   - `LoginView` puede heredar de `TokenObtainPairView` y retornar ambos tokens + metadatos.
2. **Refresh & logout**
   - Exponer `POST /auth/token/refresh/` (`TokenRefreshView`).
   - Implementar `LogoutView` que reciba el `refresh` y lo agregue a la blacklist (`RefreshToken.blacklist()`).
3. **Session**
   - Mantener `/session/` pero validar únicamente que el `access` sea válido (no más consultas a `Token` model).
4. **Limpieza**
   - Eliminar dependencias de `rest_framework.authtoken` (apps, migraciones, creación de tokens en tests).
   - Actualizar tests (`users/authentication/tests.py`) para usar `Bearer <access>` y cubrir refresh/blacklist.

## Fase 3 · Frontend (Axios)

1. Guardar `access` y `refresh` (p.ej. en `localStorage` o memoria) tras el login.
2. Configurar interceptores para:
   - Adjuntar `Authorization: Bearer <access>`.
   - Detectar `401`/exp expirado → solicitar nuevo `access` con el `refresh`.
   - Si el refresh expira o está en blacklist, redirigir al login.
3. Ajustar flujo de logout para enviar el `refresh` al backend y limpiar ambos tokens.
4. Opcional: decodificar `access` (claim `exp`) para refrescar proactivamente antes de que caduque.

### Migración desde token DRF

1. **Captura de login**
   - Reemplazar cualquier consumo de `response.data.token` por (`access`, `refresh`).
   - Guardar ambos; el `access` se usa en encabezados, el `refresh` en un almacén seguro para solicitar nuevos pares.
2. **Headers**
   - Donde antes se enviaba `Authorization: Token xxx`, actualizar a `Authorization: Bearer ${access}`.
   - Si existe un interceptor que también mandaba `X-CSRFToken`, no cambia.
3. **Renovación automática**
   - Crear un interceptor de respuesta que, ante `401` por expiración, llame a `/api/users/auth/token/refresh/` con el `refresh` almacenado y reintente la petición con el nuevo `access`.
   - Si el refresh también falla, limpiar sesión y redirigir al login.
4. **Logout**
   - Mandar `POST /api/users/auth/logout/` con body `{"refresh": "..."}` y limpiar ambos tokens al completar. Esto garantiza que el refresh quede en blacklist.
5. **Sesión / perfil**
   - Cualquier lugar donde el frontend pedía `/session/` y esperaba un `token` debe actualizarse: ahora el endpoint sólo devuelve los metadatos del usuario; el cliente mantiene el JWT en memoria.
6. **Manejo de expiración**
   - Opcionalmente decodificar el `access` (payload JWT) para refrescar unos segundos antes de `exp`; evita ráfagas de 401.
7. **Herramientas comunes**
   - Actualizar scripts utilitarios (`test-empresa-endpoints.js`, `test-from-browser-console.js`, etc.) para que lean/envíen `Bearer` en vez de `Token`.
8. **Validación**
   - Después de los cambios, ejecutar un recorrido completo (login, endpoints protegidos, refresh, logout) para confirmar que no quedan headers antiguos y que las llamadas 401 se manejan correctamente.

## Consideraciones adicionales

- **Blacklisting**: imprescindible para poder invalidar refresh tokens comprometidos. Requiere ejecutar `python manage.py migrate` tras habilitar la app `token_blacklist`.
- **Clock skew**: si servidores/clients tienen desfase horario, SimpleJWT soporta `LEEWAY`; evaluarlo si aparecen falsos expirados.
- **Pruebas**: además de los tests existentes, crear casos que simulen expiración rápida (usar `override_settings` para TTL cortos) y validen que el backend responde con `401` una vez vencido el token.
- **Rollout**: como estamos en desarrollo, se puede eliminar la autenticación previa sin compatibilidad hacia atrás. En producción, planear ventana de mantenimiento para invalidar tokens antiguos.

Este roadmap debe actualizarse conforme se vayan completando las fases (marcar checklists, anotar decisiones de configuración o cambios en endpoints).
