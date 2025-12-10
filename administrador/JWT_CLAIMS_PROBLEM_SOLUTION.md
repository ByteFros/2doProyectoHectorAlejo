# Problema de Permisos JWT: Error 403 en Producción

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Problema Detectado](#problema-detectado)
3. [Diagnóstico Realizado](#diagnóstico-realizado)
4. [Causa Raíz](#causa-raíz)
5. [Solución Propuesta](#solución-propuesta)
6. [Pasos de Implementación](#pasos-de-implementación)
7. [Verificación](#verificación)
8. [Despliegue a Producción](#despliegue-a-producción)

---

## 🎯 Resumen Ejecutivo

### Problema
En **producción**, los usuarios con rol `EMPRESA` reciben errores **403 Forbidden** al intentar acceder al endpoint `/api/users/empleados/pending/`, mientras que en **desarrollo** funciona correctamente.

### Causa
El JWT generado por Django **no incluye los claims personalizados** (`role`, `empresa_id`, `empleado_id`) necesarios para que el sistema de permisos funcione correctamente.

### Solución
Modificar el backend de Django para incluir claims personalizados en el JWT usando SimpleJWT.

### Impacto
- ✅ Soluciona errores 403 en producción
- ✅ Mejora el rendimiento (menos queries a BD)
- ✅ Estandariza el manejo de permisos
- ✅ No requiere cambios en el frontend

---

## 🔴 Problema Detectado

### Síntomas

**En Desarrollo:**
```
✅ GET /users/empleados/ → 200 OK (funciona)
✅ GET /users/empleados/pending/ → 200 OK (funciona)
```

**En Producción:**
```
✅ GET /users/empleados/ → 200 OK (funciona)
❌ GET /users/empleados/pending/ → 403 Forbidden (falla)
```

### Error Específico

```
GET /api/users/empleados/pending/ 403 (Forbidden)
{
  "detail": "No tienes permisos para ver revisiones pendientes"
}
```

### Logs del Backend (Producción)

```
WARNING:django.request:Forbidden: /api/users/empleados/pending/
WARNING:django.request:Forbidden: /api/users/empleados/pending/
WARNING:django.request:Forbidden: /api/users/empleados/pending/
...
```

---

## 🔍 Diagnóstico Realizado

### 1. Inspección del JWT

Al decodificar el JWT enviado en las peticiones, se encontró:

**JWT Actual (Desarrollo y Producción):**
```json
{
  "token_type": "access",
  "exp": 1765363582,
  "iat": 1765362682,
  "jti": "0f7520429be541f2aec95223a565fffd",
  "user_id": "91"
}
```

**Campos disponibles:**
- ✅ `token_type` - Tipo de token
- ✅ `exp` - Fecha de expiración
- ✅ `iat` - Fecha de emisión
- ✅ `jti` - JWT ID único
- ✅ `user_id` - ID del usuario
- ❌ `role` - **FALTA** (debería ser "EMPRESA", "MASTER", "EMPLEADO")
- ❌ `empresa_id` - **FALTA** (ID de la empresa si es usuario EMPRESA)
- ❌ `empleado_id` - **FALTA** (ID del empleado si es usuario EMPLEADO)

### 2. Análisis del Código de Permisos

**Clase de Permisos (`permissions.py`):**
```python
class CanViewPendingReviews(permissions.BasePermission):
    """
    Permite ver viajes/empleados con revisiones pendientes.
    """
    message = "No tienes permisos para ver revisiones pendientes"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # MASTER siempre puede ver
        if request.user.role == "MASTER":  # ← Intenta acceder a .role
            return True

        # EMPRESA solo si tiene permisos
        if request.user.role == "EMPRESA":  # ← Intenta acceder a .role
            empresa = get_user_empresa(request.user)
            if not empresa:
                return False
            return empresa.permisos

        # EMPLEADO no puede ver
        return False
```

**Problema:** El código intenta acceder a `request.user.role`, pero como el JWT no incluye este claim, el atributo no está disponible.

### 3. Comparación Desarrollo vs Producción

| Aspecto | Desarrollo | Producción |
|---------|-----------|------------|
| **DEBUG** | `True` | `False` |
| **Validación de Permisos** | Laxa | Estricta |
| **Queries a BD** | Más frecuentes | Optimizadas |
| **Comportamiento** | Hace queries adicionales para obtener role | Rechaza inmediatamente si no encuentra role en JWT |

**Conclusión:** En desarrollo, Django probablemente hace queries adicionales a la base de datos para obtener el rol del usuario, compensando la falta del claim. En producción, con `DEBUG=False`, el sistema de permisos es más estricto y rechaza la petición inmediatamente si no encuentra el rol en el JWT.

---

## 🎯 Causa Raíz

### Análisis de SimpleJWT

Django usa **`djangorestframework-simplejwt`** para generar los tokens JWT. Por defecto, SimpleJWT solo incluye claims básicos:

```python
# Comportamiento por defecto de SimpleJWT
def get_token(cls, user):
    token = super().get_token(user)
    # Solo incluye: user_id, exp, iat, jti, token_type
    return token
```

### Flujo del Problema

```
1. Usuario hace login
   ↓
2. Backend genera JWT con SimpleJWT (sin claims personalizados)
   ↓
3. Frontend almacena JWT y lo envía en cada petición
   ↓
4. Backend recibe petición a /empleados/pending/
   ↓
5. CanViewPendingReviews intenta acceder a request.user.role
   ↓
6. Como role no existe en JWT → AttributeError o None
   ↓
7. Backend rechaza con 403 Forbidden
```

### Por qué funciona parcialmente en desarrollo

1. `DEBUG=True` puede tener manejo de errores más permisivo
2. Django puede hacer queries adicionales a la BD para obtener el rol
3. Algunos endpoints no validan permisos tan estrictamente
4. El ORM de Django puede cachear resultados de queries

---

## ✅ Solución Propuesta

### Estrategia

Extender SimpleJWT para incluir **claims personalizados** en el JWT que contengan la información necesaria para la validación de permisos:

- `role`: El rol del usuario (MASTER, EMPRESA, EMPLEADO)
- `empresa_id`: ID de la empresa (si el usuario es EMPRESA)
- `empleado_id`: ID del empleado (si el usuario es EMPLEADO)

### Beneficios

1. ✅ **Soluciona el error 403** - El sistema de permisos tendrá la información necesaria
2. ✅ **Mejora el rendimiento** - Menos queries a la base de datos
3. ✅ **Seguridad** - Los permisos están firmados en el JWT
4. ✅ **Escalabilidad** - Facilita la implementación de microservicios
5. ✅ **No requiere cambios en frontend** - Transparente para el cliente
6. ✅ **Consistencia** - Mismo comportamiento en desarrollo y producción

### Arquitectura de la Solución

```
┌─────────────────────────────────────────────────────────────┐
│                    LOGIN REQUEST                             │
│  POST /auth/login/                                           │
│  { username: "user@empresa.com", password: "***" }          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           CustomTokenObtainPairSerializer                    │
│                                                              │
│  1. Valida credenciales                                     │
│  2. Obtiene el usuario de la BD                             │
│  3. Genera JWT base con SimpleJWT                           │
│  4. Agrega claims personalizados:                           │
│     ├─ token['role'] = user.role                           │
│     ├─ token['empresa_id'] = empresa.id (si EMPRESA)       │
│     └─ token['empleado_id'] = empleado.id (si EMPLEADO)    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   JWT GENERADO                               │
│  {                                                           │
│    "token_type": "access",                                  │
│    "exp": 1765363582,                                       │
│    "iat": 1765362682,                                       │
│    "jti": "abc123...",                                      │
│    "user_id": "91",                                         │
│    "role": "EMPRESA",          ← NUEVO                      │
│    "empresa_id": 5,            ← NUEVO                      │
│    "empleado_id": null         ← NUEVO                      │
│  }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               PETICIONES SUBSECUENTES                        │
│  GET /empleados/pending/                                     │
│  Authorization: Bearer [JWT]                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            CustomJWTAuthentication/Middleware                │
│                                                              │
│  1. Decodifica JWT                                          │
│  2. Valida firma y expiración                               │
│  3. Extrae claims personalizados                            │
│  4. Agrega al request.user:                                 │
│     ├─ request.user.role = "EMPRESA"                       │
│     ├─ request.user.empresa_id = 5                         │
│     └─ request.user.empleado_id = null                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CanViewPendingReviews Permission                │
│                                                              │
│  def has_permission(self, request, view):                   │
│      if request.user.role == "MASTER":  ← AHORA FUNCIONA   │
│          return True                                        │
│      if request.user.role == "EMPRESA":                     │
│          return empresa.permisos                            │
│      return False                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                    ✅ 200 OK
```

---

## 🛠️ Pasos de Implementación

### Paso 1: Crear Serializer Personalizado

**Archivo: `users/serializers.py`**

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado que agrega claims adicionales al JWT.

    Claims agregados:
    - role: El rol del usuario (MASTER, EMPRESA, EMPLEADO)
    - empresa_id: ID de la empresa (si el usuario es EMPRESA)
    - empleado_id: ID del empleado (si el usuario es EMPLEADO)
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar rol del usuario
        token['role'] = user.role if hasattr(user, 'role') else None

        # Si es EMPRESA, agregar empresa_id
        if hasattr(user, 'role') and user.role == 'EMPRESA':
            try:
                from users.models import EmpresaProfile
                empresa = EmpresaProfile.objects.get(user=user)
                token['empresa_id'] = empresa.id
            except EmpresaProfile.DoesNotExist:
                token['empresa_id'] = None
        else:
            token['empresa_id'] = None

        # Si es EMPLEADO, agregar empleado_id
        if hasattr(user, 'role') and user.role == 'EMPLEADO':
            try:
                from users.models import EmpleadoProfile
                empleado = EmpleadoProfile.objects.get(user=user)
                token['empleado_id'] = empleado.id
            except EmpleadoProfile.DoesNotExist:
                token['empleado_id'] = None
        else:
            token['empleado_id'] = None

        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada que usa el serializer personalizado"""
    serializer_class = CustomTokenObtainPairSerializer
```

### Paso 2: Actualizar URLs

**Archivo: `urls.py` (rutas de autenticación)**

```python
from rest_framework_simplejwt.views import TokenRefreshView
from users.serializers import CustomTokenObtainPairView  # Importar

urlpatterns = [
    # ... otras rutas

    # Reemplazar la vista por defecto de SimpleJWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ... otras rutas
]
```

### Paso 3: Agregar Claims al Request User (OPCIÓN 1 - Middleware)

**Archivo: `users/middleware.py` (crear nuevo archivo)**

```python
from rest_framework_simplejwt.tokens import AccessToken

class JWTClaimsMiddleware:
    """
    Middleware que agrega los claims personalizados del JWT al request.user

    Esto hace que request.user.role, request.user.empresa_id, etc.
    estén disponibles sin tener que decodificar el token manualmente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Agregar claims del JWT al user si está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Intentar obtener el token del header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token_string = auth_header.split(' ')[1]
                try:
                    token = AccessToken(token_string)

                    # Agregar claims como atributos del user
                    request.user.role = token.get('role')
                    request.user.empresa_id = token.get('empresa_id')
                    request.user.empleado_id = token.get('empleado_id')
                except Exception:
                    # Si falla la decodificación, continuar sin los claims
                    pass

        response = self.get_response(request)
        return response
```

**Registrar en `settings.py`:**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Agregar DESPUÉS de AuthenticationMiddleware
    'users.middleware.JWTClaimsMiddleware',  # ← AGREGAR AQUÍ
]
```

### Paso 3 (ALTERNATIVA): Authentication Class Personalizada (OPCIÓN 2)

**Archivo: `users/authentication.py` (crear nuevo archivo)**

```python
from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication

class CustomJWTAuthentication(BaseJWTAuthentication):
    """
    Autenticación JWT personalizada que agrega los claims al user object.
    """
    def authenticate(self, request):
        result = super().authenticate(request)

        if result is not None:
            user, token = result

            # Agregar claims del token al objeto user
            user.role = token.get('role')
            user.empresa_id = token.get('empresa_id')
            user.empleado_id = token.get('empleado_id')

            return (user, token)

        return None
```

**Actualizar ViewSets (`users/views.py`):**

```python
# Reemplazar:
from rest_framework_simplejwt.authentication import JWTAuthentication

# Por:
from users.authentication import CustomJWTAuthentication

class EmpresaViewSet(viewsets.ModelViewSet):
    # ...
    authentication_classes = [CustomJWTAuthentication]  # ← CAMBIAR
    # ...

class EmpleadoViewSet(viewsets.ModelViewSet):
    # ...
    authentication_classes = [CustomJWTAuthentication]  # ← CAMBIAR
    # ...
```

### Recomendación: Usar OPCIÓN 1 (Middleware)

La opción del middleware es más limpia y centralizada. Se aplica automáticamente a todas las vistas sin tener que modificar cada ViewSet.

---

## ✅ Verificación

### 1. Reiniciar Servidor

```bash
# En el directorio del backend
python manage.py runserver
```

### 2. Hacer Login desde el Frontend

1. Cerrar sesión en el navegador
2. Limpiar localStorage (opcional pero recomendado):
   ```javascript
   localStorage.clear()
   ```
3. Volver a iniciar sesión

### 3. Inspeccionar el JWT

Abrir la consola del navegador y verificar los logs:

```javascript
🔑 JWT COMPLETO para /users/empleados/:
{
  token_type: 'access',
  exp: 1765363582,
  iat: 1765362682,
  jti: '0f7520429be541f2aec95223a565fffd',
  user_id: '91',
  role: 'EMPRESA',          // ✅ DEBE APARECER
  empresa_id: 5,             // ✅ DEBE APARECER
  empleado_id: null          // ✅ DEBE APARECER
}
📋 Campos disponibles:
['token_type', 'exp', 'iat', 'jti', 'user_id', 'role', 'empresa_id', 'empleado_id']
```

### 4. Probar Endpoint Problemático

**En Desarrollo:**
```bash
curl -H "Authorization: Bearer [TOKEN]" \
     http://localhost:8000/api/users/empleados/pending/
```

**Resultado esperado:** `200 OK` con lista de empleados

### 5. Verificar Logs del Backend

No deberían aparecer errores 403:

```
✅ GET /api/users/empleados/pending/ 200 OK
✅ GET /api/users/empleados/ 200 OK
```

---

## 🚀 Despliegue a Producción

### Checklist Pre-Deploy

- [ ] **Todos los cambios están en el repositorio**
  - [ ] `users/serializers.py` - CustomTokenObtainPairSerializer agregado
  - [ ] `urls.py` - CustomTokenObtainPairView configurado
  - [ ] `users/middleware.py` - Middleware creado (OPCIÓN 1)
  - [ ] `settings.py` - Middleware registrado (OPCIÓN 1)
  - [ ] `users/authentication.py` - Authentication class (OPCIÓN 2)
  - [ ] `users/views.py` - ViewSets actualizados (OPCIÓN 2)

- [ ] **Código testeado en desarrollo**
  - [ ] JWT contiene los claims personalizados
  - [ ] Endpoint `/empleados/pending/` funciona
  - [ ] Otros endpoints no se rompen
  - [ ] Login/Logout funciona correctamente

### Pasos de Despliegue

#### 1. Backup de Producción

```bash
# Backup de la base de datos
pg_dump nombre_bd > backup_$(date +%Y%m%d_%H%M%S).sql

# O para MySQL
mysqldump -u usuario -p nombre_bd > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 2. Desplegar Cambios

```bash
# En el servidor de producción
git pull origin main  # o la rama correspondiente

# Activar entorno virtual
source venv/bin/activate

# Instalar/actualizar dependencias (por si acaso)
pip install -r requirements.txt

# Migrar BD (aunque no hay migraciones nuevas, es buena práctica)
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

#### 3. Reiniciar Servicios

```bash
# Si usas Gunicorn
sudo systemctl restart gunicorn

# Si usas uWSGI
sudo systemctl restart uwsgi

# Si usas Nginx
sudo systemctl reload nginx
```

#### 4. Invalidar Sesiones Existentes (Importante)

**⚠️ CRÍTICO:** Los JWT antiguos no tienen los nuevos claims. Hay dos opciones:

**Opción A: Forzar logout de todos los usuarios (Recomendado)**

```python
# En Django shell de producción
python manage.py shell

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
OutstandingToken.objects.all().delete()
```

**Opción B: Esperar a que expiren naturalmente**

Los usuarios tendrán que volver a hacer login cuando sus tokens expiren (normalmente 1 hora para access tokens).

### 5. Verificación Post-Deploy

#### A. Verificar que el servidor está corriendo

```bash
curl https://tu-dominio.com/api/health/  # o endpoint de health check
```

#### B. Hacer login de prueba

1. Ir a https://tu-dominio.com
2. Iniciar sesión con una cuenta EMPRESA
3. Abrir DevTools → Console
4. Verificar que el JWT tiene los campos `role`, `empresa_id`

#### C. Probar endpoint problemático

```bash
# Desde la consola del navegador en producción
fetch('/api/users/empleados/pending/', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('auth_access_token')
  }
})
.then(r => r.json())
.then(console.log)
```

**Resultado esperado:** Lista de empleados, no error 403

#### D. Monitorear logs en tiempo real

```bash
# En el servidor
tail -f /var/log/gunicorn/error.log  # o la ruta de tus logs

# Buscar errores 403
grep "403" /var/log/gunicorn/access.log
```

**Resultado esperado:** No deberían aparecer nuevos errores 403 para `/empleados/pending/`

---

## 📊 Comparativa Antes/Después

### Antes (JWT sin claims personalizados)

```json
{
  "token_type": "access",
  "exp": 1765363582,
  "iat": 1765362682,
  "jti": "0f7520429be541f2aec95223a565fffd",
  "user_id": "91"
}
```

**Problemas:**
- ❌ Sistema de permisos no puede determinar rol sin query a BD
- ❌ En producción con `DEBUG=False` → 403 Forbidden
- ❌ Múltiples queries a BD para verificar permisos
- ❌ Inconsistencia entre desarrollo y producción

### Después (JWT con claims personalizados)

```json
{
  "token_type": "access",
  "exp": 1765363582,
  "iat": 1765362682,
  "jti": "0f7520429be541f2aec95223a565fffd",
  "user_id": "91",
  "role": "EMPRESA",
  "empresa_id": 5,
  "empleado_id": null
}
```

**Beneficios:**
- ✅ Sistema de permisos accede directamente a `request.user.role`
- ✅ Funciona igual en desarrollo y producción
- ✅ Menos queries a BD → mejor rendimiento
- ✅ Permisos verificables sin estado en servidor

---

## 🔒 Consideraciones de Seguridad

### Claims en JWT

✅ **Ventajas:**
- Los claims están **firmados** por el servidor (no se pueden falsificar)
- Reduce la superficie de ataque (menos queries a BD)
- Los permisos son consistentes durante la vida del token

⚠️ **Consideraciones:**
- Si cambias el rol de un usuario, el cambio **no se reflejará** hasta que el token expire
- Los JWT pueden ser grandes si incluyes muchos datos
- Cualquiera que obtenga el token puede **leer** los claims (pero no modificarlos)

### Rotación de Tokens

Si necesitas que un cambio de permisos se refleje inmediatamente:

1. **Opción 1:** Usar tokens de corta duración (ej: 15 minutos)
2. **Opción 2:** Implementar blacklist de tokens
3. **Opción 3:** Forzar logout del usuario específico

### Datos Sensibles

❌ **NO incluir** en el JWT:
- Contraseñas
- Números de tarjeta de crédito
- Información personal sensible (domicilio, teléfono, etc.)

✅ **SÍ incluir** en el JWT:
- ID de usuario
- Rol/permisos básicos
- IDs de entidades relacionadas (empresa_id, empleado_id)
- Metadatos no sensibles

---

## 📞 Soporte y Troubleshooting

### Problema: JWT sigue sin tener los claims

**Causa:** Estás usando un token antiguo generado antes del cambio.

**Solución:**
```javascript
// En el navegador
localStorage.clear()
// Hacer logout y login de nuevo
```

### Problema: Error al importar CustomTokenObtainPairView

**Causa:** Importación circular o archivo no encontrado.

**Solución:**
1. Verificar que el archivo `users/serializers.py` existe
2. Verificar que la clase está bien definida
3. Reiniciar el servidor Django

### Problema: 500 Internal Server Error después del cambio

**Causa:** Error en el código del middleware o authentication class.

**Solución:**
1. Revisar logs del servidor: `tail -f logs/error.log`
2. Verificar que no hay errores de sintaxis
3. Comentar temporalmente el middleware y probar

### Problema: Algunos endpoints siguen dando 403

**Causa:** Otros viewsets no están usando la autenticación personalizada.

**Solución (OPCIÓN 2):**
Verificar que todos los ViewSets usen `CustomJWTAuthentication`:

```python
class MiViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomJWTAuthentication]  # ← Verificar
```

**Solución (OPCIÓN 1):**
El middleware debería aplicarse automáticamente. Verificar que está registrado en `MIDDLEWARE` de `settings.py`.

---

## 📚 Referencias

- [SimpleJWT Documentation](https://django-rest-framework-simplejwt.readthedocs.io/)
- [JWT.io - JSON Web Tokens](https://jwt.io/)
- [Django REST Framework - Permissions](https://www.django-rest-framework.org/api-guide/permissions/)
- [Django Middleware](https://docs.djangoproject.com/en/stable/topics/http/middleware/)

---

## ✅ Checklist Final

### Implementación
- [ ] Crear `CustomTokenObtainPairSerializer`
- [ ] Crear `CustomTokenObtainPairView`
- [ ] Actualizar URLs para usar vista personalizada
- [ ] Elegir e implementar OPCIÓN 1 (Middleware) o OPCIÓN 2 (Auth Class)
- [ ] Probar en desarrollo
- [ ] Commit y push de cambios

### Testing
- [ ] Verificar JWT contiene `role`, `empresa_id`, `empleado_id`
- [ ] Probar endpoint `/empleados/pending/` → 200 OK
- [ ] Probar otros endpoints afectados
- [ ] Probar con diferentes roles (MASTER, EMPRESA, EMPLEADO)

### Despliegue
- [ ] Backup de producción
- [ ] Deploy a producción
- [ ] Reiniciar servicios
- [ ] Invalidar tokens antiguos (logout forzado)
- [ ] Verificar logs de producción
- [ ] Monitorear errores durante 24h

### Documentación
- [ ] Actualizar README con cambios
- [ ] Documentar nuevos claims en wiki/docs
- [ ] Informar al equipo sobre necesidad de re-login

---

**Fecha de creación:** Diciembre 2025
**Última actualización:** Diciembre 2025
**Autor:** Equipo de Desarrollo
**Estado:** ✅ Listo para implementar
