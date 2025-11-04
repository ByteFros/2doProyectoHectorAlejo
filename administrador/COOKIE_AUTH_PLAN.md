# Plan de Migración a Cookies para Autenticación

## Objetivo
Reemplazar el almacenamiento del token de autenticación en `localStorage` por cookies HTTP-only para reducir riesgos de XSS, manteniendo la compatibilidad con el stack actual y el despliegue en Docker Compose.

## Cambios en el Backend
- **Login (`users/authentication/views.py`)**
  - Generar el `Token` como hasta ahora, pero enviarlo en una cookie `HttpOnly`, con expiración configurable y atributos `Secure`/`SameSite` adecuados (probablemente `SameSite=None` si el frontend vive en otro dominio/subdominio).
  - Opcional: devolver además un indicador en el cuerpo para confirmar la autenticación.
- **Logout (`users/authentication/views.py`)**
  - Eliminar la cookie (`response.delete_cookie(...)`) y borrar el token en la base de datos.
- **Autenticación DRF**
  - Implementar un `CookieTokenAuthentication` (p.ej. en `users/authentication/auth_backend.py`) que herede de `TokenAuthentication` y obtenga el token desde `request.COOKIES['auth_token']`.
  - Registrar la clase en `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` antes de `TokenAuthentication` tradicional.
- **Middlewares y CSRF (`administrador/settings.py`)**
  - Reactivar `CsrfViewMiddleware` o proporcionar una estrategia alternativa (p.ej. token rotativo).
  - Asegurar que `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS` y `CORS_ALLOW_CREDENTIALS = True` cubren todos los hosts usados (local y Docker).
  - Ajustar `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SAMESITE` y sus flags `Secure` para entorno productivo (HTTPS).
- **Cookies globales**
  - Definir un nombre de cookie coherente (`AUTH_TOKEN`, por ejemplo).
  - Evaluar `COOKIE_DOMAIN` si se necesita compartir cookies entre subdominios.
- **Tests (`users/authentication/tests.py`)**
  - Verificar que el login entrega la cookie correcta y que el flujo funciona sin encabezado `Authorization`.
  - Añadir pruebas para CSRF si se habilita explícitamente.

## Ajustes en el Frontend
- Usar `credentials: 'include'` en las peticiones a la API.
- Recuperar el token CSRF desde cookie o endpoint dedicado y enviarlo en `X-CSRFToken`.
- Eliminar la persistencia manual de tokens en `localStorage`/`sessionStorage`.

## Impacto en Docker Compose
- **Variables de entorno**
  - Añadir valores para `DJANGO_SECURE_COOKIE`, `DJANGO_COOKIE_DOMAIN`, etc., si se necesita parametrizar atributos de cookies por entorno.
  - Asegurar que la URL del frontend en Docker (`crowe_frontend:5173`) está presente en `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS`.
- **HTTPS terminación**
  - Si en producción/Docker se usa un proxy inverso (Nginx, Traefik), habilitar TLS allí para poder marcar las cookies como `Secure`.
  - Verificar que el proxy preserve y reenvía cabeceras como `Cookie` y `X-CSRFToken`.
- **Pruebas en contenedores**
  - Incluir tests end-to-end o smoke tests dentro del pipeline de Docker que validen el flujo de login con cookies.

## Pendientes antes de Desarrollar
1. Definir política de expiración de tokens/cookies y estrategia de renovación.
2. Confirmar dominios finales para configurar `SameSite`, `Secure` y `COOKIE_DOMAIN`.
3. Coordinar con frontend para manejar CSRF y credenciales compartidas.

