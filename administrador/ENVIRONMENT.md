# Environment Configuration

Este documento resume las variables de entorno soportadas por el backend y cómo influyen en el despliegue con Docker.

## Variables principales

- `DJANGO_ENV`: `"development"` o `"production"`. Determina la base de datos usada y algunos valores por defecto de seguridad.
- `DEBUG`: Activa o desactiva el modo debug. En producción debe ser `False`.
- `DJANGO_SECRET_KEY`: Clave secreta obligatoria en producción.
- `DJANGO_ALLOWED_HOSTS`: Lista separada por comas de hosts permitidos (`localhost,127.0.0.1`).
- `PORT`: Puerto expuesto por Gunicorn dentro del contenedor (por defecto `8000`).

### JWT

- `JWT_ACCESS_TTL_MINUTES`: duración del access token JSON Web Token en minutos (p.ej. 15).
- `JWT_REFRESH_TTL_DAYS`: duración del refresh token en días para obligar al usuario a reautenticarse pasado ese plazo.
- `JWT_ROTATE_REFRESH_TOKENS`: si es `True`, cada refresh entrega un nuevo par y el anterior queda invalidado.
- `JWT_BLACKLIST_AFTER_ROTATION`: requiere la app `token_blacklist`; marca el refresh previo como inválido al rotar.

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

## Frontend (cuando se despliega con Docker)

- `VITE_API_BASE_URL`: URL base usada por el frontend para llamar al backend. Debe apuntar al nombre del servicio dentro de la red (`http://web:8000/api` en Compose) o al dominio público en producción.

## Datos de seed (usuarios por rol)

Se usan cuando `SEED_INITIAL_USERS=true`. Todos tienen valores predeterminados pero pueden sobreescribirse:

- `SEED_MASTER_USERNAME`, `SEED_MASTER_PASSWORD`, `SEED_MASTER_EMAIL`
- `SEED_EMPRESA_USERNAME`, `SEED_EMPRESA_PASSWORD`, `SEED_EMPRESA_EMAIL`
- `SEED_EMPRESA_NAME`, `SEED_EMPRESA_NIF`, `SEED_EMPRESA_ADDRESS`, `SEED_EMPRESA_CITY`, `SEED_EMPRESA_POSTAL_CODE`, `SEED_EMPRESA_CONTACT_EMAIL`, `SEED_EMPRESA_PERIODICITY`
- `SEED_EMPLEADO_USERNAME`, `SEED_EMPLEADO_PASSWORD`, `SEED_EMPLEADO_EMAIL`, `SEED_EMPLEADO_NOMBRE`, `SEED_EMPLEADO_APELLIDO`, `SEED_EMPLEADO_DNI`

## Comandos de gestión adicionales

- `EXTRA_MANAGEMENT_COMMANDS`: lista de comandos de `manage.py` a ejecutar tras el seeding, separados por salto de línea o `;`. Ejemplos:  
  `EXTRA_MANAGEMENT_COMMANDS=load_sample_data --clear;create_sample_trips --clear;create_sample_expenses`

## Uso con Docker Compose

- El archivo `.env` en la raíz se carga automáticamente por `docker-compose`.
- Para producción se recomienda usar `docker-compose.prod.yml`, ajustando valores sensibles mediante variables de entorno o un `.env` seguro.

Siempre valida que las claves y contraseñas no queden en texto plano en repositorios públicos. Utiliza secretos del proveedor de despliegue cuando sea posible.
