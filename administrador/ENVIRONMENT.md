# Environment Configuration

Este documento resume las variables de entorno soportadas por el backend y cómo influyen en el despliegue con Docker.

## Variables principales

- `DJANGO_ENV`: `"development"` o `"production"`. Determina la base de datos usada y algunos valores por defecto de seguridad.
- `DEBUG`: Activa o desactiva el modo debug. En producción debe ser `False`.
- `DJANGO_SECRET_KEY`: Clave secreta obligatoria en producción.
- `DJANGO_ALLOWED_HOSTS`: Lista separada por comas de hosts permitidos (`localhost,127.0.0.1`).
- `PORT`: Puerto expuesto por Gunicorn dentro del contenedor (por defecto `8000`).

## Base de datos

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Credenciales y host de PostgreSQL utilizados por Django y los servicios Docker.

## CORS y CSRF

- `CORS_ALLOWED_ORIGINS`: Lista de orígenes permitidos (URLs completas).
- `CORS_ALLOW_ALL_ORIGINS`: Forzar permitir cualquier origen (`True/False`). Solo recomendable en desarrollo.
- `CORS_ALLOW_CREDENTIALS`: Permitir envío de cookies/credenciales.
- `CSRF_TRUSTED_ORIGINS`: Dominio(s) confiables para CSRF.
- `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`: Configuran si las cookies requieren HTTPS. En producción deberían ser `True`.

## Comportamiento de arranque (`entrypoint.sh`)

- `RUN_MIGRATIONS`: Ejecuta `python manage.py migrate` al iniciar el contenedor.
- `RUN_COLLECTSTATIC`: Ejecuta `collectstatic`. Útil en producción cuando se usan archivos estáticos servidos por nginx/S3.
- `SEED_INITIAL_USERS`: Lanza `python manage.py create_test_users` con las credenciales configuradas.
- `GUNICORN_WORKERS`: Número de workers a usar en Gunicorn.
- `GUNICORN_TIMEOUT`: Tiempo de espera antes de reiniciar workers colgados (segundos).

## Configuración de correo

- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`: Configuran el backend SMTP.
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: Credenciales del servicio de correo.
- `DEFAULT_FROM_EMAIL`: Dirección remitente predeterminada para los envíos.

## Datos de seed (usuarios por rol)

Se usan cuando `SEED_INITIAL_USERS=true`. Todos tienen valores predeterminados pero pueden sobreescribirse:

- `SEED_MASTER_USERNAME`, `SEED_MASTER_PASSWORD`, `SEED_MASTER_EMAIL`
- `SEED_EMPRESA_USERNAME`, `SEED_EMPRESA_PASSWORD`, `SEED_EMPRESA_EMAIL`
- `SEED_EMPRESA_NAME`, `SEED_EMPRESA_NIF`, `SEED_EMPRESA_ADDRESS`, `SEED_EMPRESA_CITY`, `SEED_EMPRESA_POSTAL_CODE`, `SEED_EMPRESA_CONTACT_EMAIL`, `SEED_EMPRESA_PERIODICITY`
- `SEED_EMPLEADO_USERNAME`, `SEED_EMPLEADO_PASSWORD`, `SEED_EMPLEADO_EMAIL`, `SEED_EMPLEADO_NOMBRE`, `SEED_EMPLEADO_APELLIDO`, `SEED_EMPLEADO_DNI`

## Uso con Docker Compose

- El archivo `.env` en la raíz se carga automáticamente por `docker-compose`.
- Para producción se recomienda usar `docker-compose.prod.yml`, ajustando valores sensibles mediante variables de entorno o un `.env` seguro.

Siempre valida que las claves y contraseñas no queden en texto plano en repositorios públicos. Utiliza secretos del proveedor de despliegue cuando sea posible.
