# Módulo de Empresas y Empleados

Este módulo proporciona la funcionalidad completa para la gestión de empresas y empleados dentro del sistema. Utiliza Django REST Framework ViewSets con permisos basados en roles.

## Estructura del Módulo

```
empresas/
├── __init__.py
├── permissions.py       # Permisos personalizados por rol
├── serializers.py       # Validación y serialización de datos
├── services.py          # Lógica de negocio
├── urls.py              # Configuración del router DRF
├── viewsets.py          # ViewSets de empresas y empleados
└── tests/               # Tests unitarios e integración
```

## Roles de Usuario

El sistema maneja tres roles principales:

- **MASTER**: Administrador del sistema con acceso total
- **EMPRESA**: Usuarios que representan a una empresa y gestionan sus empleados
- **EMPLEADO**: Usuarios trabajadores asociados a una empresa

## Query Parameters

### Parámetro `include` - Carga de Datos Anidados

El sistema soporta el query parameter `include` para cargar datos relacionados de forma eficiente en una sola request. Esto es ideal para reducir el número de llamadas al API desde el frontend.

#### Valores soportados:

| Endpoint | Parámetro | Descripción |
|----------|-----------|-------------|
| `/empresas/` | `?include=empleados` | Incluye lista de empleados anidados en cada empresa |
| `/empleados/` | `?include=viajes` | Incluye lista de viajes anidados en cada empleado |

#### Características:

- ✅ **Optimizado**: Usa `prefetch_related` para evitar N+1 queries
- ✅ **Combinable**: Funciona con filtros, búsquedas y paginación
- ✅ **Condicional**: Si no se especifica, devuelve solo datos básicos
- ✅ **Performance**: Añade solo 1-2 queries adicionales (no N queries)

#### Ejemplos de uso:

```bash
# Empresas básicas (solo datos de empresa)
GET /api/users/empresas/

# Empresas con empleados anidados
GET /api/users/empresas/?include=empleados

# Empresa específica con empleados
GET /api/users/empresas/1/?include=empleados

# Empleados básicos (sin viajes)
GET /api/users/empleados/

# Empleados con todos sus viajes anidados
GET /api/users/empleados/?include=viajes

# Empleado específico con viajes
GET /api/users/empleados/5/?include=viajes

# Combinar con filtros: empleados de una empresa con viajes
GET /api/users/empleados/?empresa=1&include=viajes

# Combinar con búsqueda: buscar empleado por nombre con viajes
GET /api/users/empleados/?search=Juan&include=viajes
```

#### Respuesta con `include=empleados`:

```json
{
  "id": 1,
  "nombre_empresa": "Acme Corp",
  "nif": "A12345678",
  "correo_contacto": "contacto@acme.com",
  "permisos": true,
  "empleados_count": 25,
  "empleados": [
    {
      "id": 10,
      "nombre": "Juan",
      "apellido": "Pérez",
      "dni": "12345678A",
      "email": "juan@acme.com",
      "username": "juan.perez",
      "salario": 28000.0
    },
    {
      "id": 11,
      "nombre": "María",
      "apellido": "García",
      "dni": "87654321B",
      "email": "maria@acme.com",
      "username": "maria.garcia",
      "salario": 26500.0
    }
  ]
}
```

#### Respuesta con `include=viajes`:

```json
{
  "id": 10,
  "nombre": "Juan",
  "apellido": "Pérez",
  "dni": "12345678A",
  "email": "juan@acme.com",
  "username": "juan.perez",
  "salario": 28000.0,
  "empresa": {
    "id": 1,
    "nombre_empresa": "Acme Corp",
    "nif": "A12345678",
    "correo_contacto": "contacto@acme.com",
    "permisos": true
  },
  "viajes_count": 3,
  "viajes": [
    {
      "id": 5,
      "destino": "Madrid, España",
      "ciudad": "Madrid",
      "pais": "España",
      "es_internacional": false,
      "fecha_inicio": "2025-10-25",
      "fecha_fin": "2025-10-27",
      "estado": "PENDIENTE",
      "dias_viajados": 3,
      "empresa_visitada": "Cliente XYZ",
      "motivo": "Reunión comercial",
      "fecha_solicitud": "2025-10-23T10:00:00Z"
    }
  ]
}
```

### Caso de Uso: Dashboard de React

**Escenario**: Dashboard con lista de empresas → al seleccionar empresa muestra empleados → al seleccionar empleado muestra viajes.

**Estrategia recomendada**: Lazy loading (carga bajo demanda)

```javascript
// 1. Carga inicial: Lista de empresas (ligera)
fetch('/api/users/empresas/')
  .then(res => res.json())
  .then(empresas => setEmpresas(empresas))

// 2. Usuario selecciona empresa → cargar empleados
const handleEmpresaClick = (empresaId) => {
  fetch(`/api/users/empleados/?empresa=${empresaId}`)
    .then(res => res.json())
    .then(empleados => setEmpleados(empleados))
}

// 3. Usuario selecciona empleado → cargar empleado CON viajes
const handleEmpleadoClick = (empleadoId) => {
  fetch(`/api/users/empleados/${empleadoId}/?include=viajes`)
    .then(res => res.json())
    .then(empleado => setEmpleadoSeleccionado(empleado))
}
```

**Ventajas de este enfoque:**
- ✅ Carga inicial rápida (<500ms)
- ✅ Solo trae datos cuando el usuario los necesita
- ✅ Datos siempre actualizados (no se cachean por 1 hora)
- ✅ Funciona con 10 o 10,000 empresas

**Alternativa**: Si necesitas prefetching al hover para mejorar UX:

```javascript
const handleMouseEnter = (empresaId) => {
  // Pre-cargar empleados antes del click
  queryClient.prefetchQuery(['empleados', empresaId],
    () => fetch(`/api/users/empleados/?empresa=${empresaId}`)
  )
}
```

## Endpoints Disponibles

### Gestión de Empresas

#### `GET /empresas/`
Lista todas las empresas registradas.

**Permisos:**
- ✅ MASTER: Puede ver todas las empresas
- ❌ EMPRESA: No autorizado
- ❌ EMPLEADO: No autorizado

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre_empresa": "Acme Corp",
    "nif": "A12345678",
    "address": "Calle Principal 123",
    "city": "Madrid",
    "postal_code": "28001",
    "correo_contacto": "contacto@acme.com",
    "permisos": true,
    "user": {
      "id": 5,
      "email": "contacto@acme.com",
      "username": "acme_corp"
    }
  }
]
```

---

#### `POST /empresas/`
Crea una nueva empresa con su usuario asociado.

**Permisos:**
- ✅ MASTER: Puede crear empresas
- ❌ EMPRESA: No autorizado
- ❌ EMPLEADO: No autorizado

**Body:**
```json
{
  "nombre_empresa": "Acme Corp",
  "nif": "A12345678",
  "address": "Calle Principal 123",
  "city": "Madrid",
  "postal_code": "28001",
  "correo_contacto": "contacto@acme.com",
  "permisos": true
}
```

**Validaciones:**
- El NIF debe ser válido y único
- El correo no debe estar registrado previamente
- Se genera automáticamente un usuario con rol EMPRESA

---

#### `GET /empresas/{id}/`
Obtiene los detalles de una empresa específica.

**Permisos:**
- ✅ MASTER: Puede ver cualquier empresa
- ✅ EMPRESA: Solo puede ver su propia empresa
- ❌ EMPLEADO: No autorizado

---

#### `PUT /empresas/{id}/`
Actualiza completamente una empresa.

**Permisos:**
- ✅ MASTER: Puede actualizar cualquier empresa
- ❌ EMPRESA: No autorizado
- ❌ EMPLEADO: No autorizado

---

#### `PATCH /empresas/{id}/`
Actualiza parcialmente una empresa (principalmente permisos).

**Permisos:**
- ✅ MASTER: Puede actualizar cualquier empresa
- ✅ EMPRESA: Puede actualizar su propia empresa
- ❌ EMPLEADO: No autorizado

**Body (actualizar permisos):**
```json
{
  "permisos": true
}
```

**Nota:** El campo `permisos` controla si la empresa puede ver y gestionar viajes en estado `EN_REVISION`.

---

#### `DELETE /empresas/{id}/`
Elimina una empresa y todos sus empleados asociados.

**Permisos:**
- ✅ MASTER: Puede eliminar cualquier empresa
- ❌ EMPRESA: No autorizado
- ❌ EMPLEADO: No autorizado

**Advertencia:** Esta operación es irreversible y eliminará también todos los empleados asociados.

---

### Gestión de Empleados

#### `GET /empleados/`
Lista empleados (filtrados según el rol del usuario).

**Permisos:**
- ✅ MASTER: Ve todos los empleados del sistema
- ✅ EMPRESA: Solo ve empleados de su propia empresa
- ✅ EMPLEADO: Solo ve su propio perfil

**Query Parameters disponibles:**
- `?empresa=1` - Filtrar por ID de empresa (solo MASTER)
- `?dni=12345678Z` - Buscar por DNI/NIE
- `?search=Juan` - Buscar por nombre, apellido o email
- `?include=viajes` - Incluir viajes anidados del empleado

**Ejemplos:**
```bash
# Buscar empleado con filtros básicos
GET /empleados/?search=Juan&empresa=1

# Obtener empleado con todos sus viajes
GET /empleados/5/?include=viajes

# Combinar búsqueda con include
GET /empleados/?search=Juan&include=viajes
```

**Respuesta:**
```json
[
  {
    "id": 10,
    "nombre": "Juan",
    "apellido": "Pérez",
    "dni": "12345678Z",
    "empresa": {
      "id": 1,
      "nombre_empresa": "Acme Corp"
    },
    "user": {
      "id": 20,
      "email": "juan.perez@acme.com",
      "username": "juan.perez"
    },
    "salario": 28000.0
  }
]
```

---

#### `POST /empleados/`
Crea un nuevo empleado.

**Permisos:**
- ✅ MASTER: Puede crear empleados para cualquier empresa (debe especificar `empresa_id`)
- ✅ EMPRESA: Puede crear empleados para su propia empresa
- ❌ EMPLEADO: No autorizado

**Body (como EMPRESA):**
```json
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "dni": "12345678Z",
  "email": "juan.perez@acme.com",
  "username": "juan.perez",
  "password": "empleado123",
  "salario": 28000.0
}
```

**Body (como MASTER):**
```json
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "dni": "12345678Z",
  "email": "juan.perez@acme.com",
  "empresa_id": 1,
  "username": "juan.perez",
  "password": "empleado123",
  "salario": 28000.0
}
```

**Validaciones:**
- El DNI/NIE debe ser válido y único
- El email no debe estar registrado previamente
- El username (si se proporciona) debe ser único
- Password por defecto: "empleado" (si no se especifica)

---

#### `GET /empleados/{id}/`
Obtiene los detalles de un empleado específico.

**Permisos:**
- ✅ MASTER: Puede ver cualquier empleado
- ✅ EMPRESA: Solo puede ver empleados de su empresa
- ✅ EMPLEADO: Solo puede ver su propio perfil

---

#### `PUT /empleados/{id}/`
Actualiza completamente un empleado.

**Permisos:**
- ✅ MASTER: Puede actualizar cualquier empleado
- ✅ EMPRESA: Solo puede actualizar empleados de su empresa
- ❌ EMPLEADO: No autorizado

---

#### `PATCH /empleados/{id}/`
Actualiza parcialmente un empleado.

**Permisos:**
- ✅ MASTER: Puede actualizar cualquier empleado
- ✅ EMPRESA: Solo puede actualizar empleados de su empresa
- ❌ EMPLEADO: No autorizado

---

#### `DELETE /empleados/{id}/`
Elimina un empleado y su usuario asociado.

**Permisos:**
- ✅ MASTER: Puede eliminar cualquier empleado
- ✅ EMPRESA: Solo puede eliminar empleados de su empresa
- ❌ EMPLEADO: No autorizado

---

### Endpoints Especiales

#### `POST /empleados/batch-upload/`
Carga masiva de empleados desde un archivo CSV.

**Permisos:**
- ✅ MASTER: Puede cargar empleados indicando `empresa_id`
- ✅ EMPRESA: Puede cargar empleados para su empresa
- ❌ EMPLEADO: No autorizado

**Body (multipart/form-data):**
```
file: archivo.csv
empresa_id: 3   # Obligatorio solo para MASTER
```

**Formato CSV esperado:**
```csv
nombre,apellido,dni,email,salario
Juan,Pérez,12345678Z,juan@empresa.com,28000
María,García,87654321A,maria@empresa.com,29500.75
```

- La columna `salario` es opcional; si se omite o queda vacía, el empleado se crea sin salario.
- Si se proporciona, debe ser un número positivo (se admite decimal con punto).

**Respuesta:**
```json
{
  "empleados_registrados": [
    {
      "id": 10,
      "nombre": "Juan",
      "apellido": "Pérez",
      "dni": "12345678Z",
      "email": "juan@empresa.com"
    }
  ],
  "empleados_omitidos": [
    {
      "fila": 3,
      "dni": "87654321A",
      "razon": "Email duplicado"
    }
  ],
  "errores": []
}
```

**Comportamiento:**
- Los empleados duplicados (por DNI o email) se omiten automáticamente
- Los empleados válidos se crean con password por defecto: "empleado"
- Se asignan automáticamente a la empresa del usuario autenticado (o a la indicada por MASTER)

---

#### `GET /empleados/pending/`
Lista empleados que tienen viajes en estado `EN_REVISION` o `REVISADO`.

**Permisos:**
- ✅ MASTER: Ve todos los empleados con viajes pendientes o revisados
- ✅ EMPRESA (con permisos=true): Ve solo sus empleados con viajes pendientes o revisados
- ❌ EMPRESA (con permisos=false): No autorizado
- ❌ EMPLEADO: No autorizado

**Filtros opcionales:**
- `?empresa=1` - Filtrar por empresa (solo MASTER)

**Respuesta:**
```json
[
  {
    "id": 10,
    "nombre": "Juan",
    "apellido": "Pérez",
    "dni": "12345678Z",
    "empresa": {
      "id": 1,
      "nombre_empresa": "Acme Corp"
    },
    "viajes_pendientes": [
      {
        "id": 5,
        "destino": "Madrid",
        "ciudad": "Madrid",
        "pais": "España",
        "fecha_inicio": "2025-10-25",
        "fecha_fin": "2025-10-27",
        "estado": "EN_REVISION",
        "dias_viajados": 3,
        "empresa_visitada": "Cliente ABC",
        "motivo": "Reunión comercial",
        "fecha_solicitud": "2025-10-23T10:00:00Z"
      }
    ],
    "total_viajes_pendientes": 1
  }
]
```

**Uso típico:** Este endpoint es útil para que las empresas vean qué empleados tienen viajes esperando aprobación/revisión y los que ya han sido revisados.

---

## Sistema de Permisos

### Permisos Personalizados

El módulo define los siguientes permisos personalizados:

| Permiso | Descripción |
|---------|-------------|
| `IsMaster` | Solo usuarios con rol MASTER |
| `IsEmpresa` | Solo usuarios con rol EMPRESA |
| `IsMasterOrEmpresa` | Usuarios MASTER o EMPRESA |
| `CanAccessEmpresa` | Acceso controlado a empresas según rol |
| `CanAccessEmpleado` | Acceso controlado a empleados según rol |
| `CanManageEmpleados` | Puede crear/modificar/eliminar empleados |
| `CanViewPendingReviews` | Puede ver viajes pendientes de revisión |

### Matriz de Permisos

#### Empresas

| Acción | MASTER | EMPRESA | EMPLEADO |
|--------|--------|---------|----------|
| Listar todas | ✅ | ❌ | ❌ |
| Ver detalle | ✅ Todas | ✅ Solo la suya | ❌ |
| Crear | ✅ | ❌ | ❌ |
| Actualizar completa | ✅ | ❌ | ❌ |
| Actualizar permisos | ✅ | ✅ Solo la suya | ❌ |
| Eliminar | ✅ | ❌ | ❌ |

#### Empleados

| Acción | MASTER | EMPRESA | EMPLEADO |
|--------|--------|---------|----------|
| Listar | ✅ Todos | ✅ Solo sus empleados | ✅ Solo él mismo |
| Ver detalle | ✅ Todos | ✅ Solo sus empleados | ✅ Solo él mismo |
| Crear | ✅ Para cualquier empresa | ✅ Para su empresa | ❌ |
| Actualizar | ✅ Todos | ✅ Solo sus empleados | ❌ |
| Eliminar | ✅ Todos | ✅ Solo sus empleados | ❌ |
| Carga masiva CSV | ❌ | ✅ Para su empresa | ❌ |
| Ver pendientes | ✅ Todos | ✅ Si permisos=true | ❌ |

---

## Validaciones

### Empresa
- **NIF**: Formato válido de NIF español (validador personalizado)
- **NIF único**: No puede haber dos empresas con el mismo NIF
- **Email único**: El correo de contacto debe ser único en el sistema
- **Campos requeridos**: `nombre_empresa`, `nif`, `correo_contacto`

### Empleado
- **DNI/NIE**: Formato válido (validador personalizado)
- **DNI/NIE único**: No puede haber dos empleados con el mismo DNI
- **Email único**: Cada empleado debe tener un email único
- **Username único**: Si se proporciona, debe ser único
- **Campos requeridos**: `nombre`, `apellido`, `dni`, `email`

---

## Ejemplos de Uso

### Ejemplo 1: MASTER crea una empresa

```bash
# Autenticación
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "master@sistema.com",
    "password": "masterpass"
  }'

# Respuesta: { "token": "abc123..." }

# Crear empresa
curl -X POST http://localhost:8000/api/users/empresas/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_empresa": "TechCorp",
    "nif": "B87654321",
    "address": "Av. Tecnología 456",
    "city": "Barcelona",
    "postal_code": "08001",
    "correo_contacto": "admin@techcorp.com",
    "permisos": true
  }'
```

### Ejemplo 2: EMPRESA registra empleados individualmente

```bash
# Autenticación como empresa
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@techcorp.com",
    "password": "empresapass"
  }'

# Crear empleado
curl -X POST http://localhost:8000/api/users/empleados/ \
  -H "Authorization: Token def456..." \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Ana",
    "apellido": "Martínez",
    "dni": "45678901B",
    "email": "ana.martinez@techcorp.com",
    "username": "ana.martinez",
    "password": "empleado123"
  }'
```

### Ejemplo 3: EMPRESA carga empleados masivamente

```bash
# Preparar archivo empleados.csv
cat > empleados.csv << EOF
nombre,apellido,dni,email
Pedro,López,11111111A,pedro@techcorp.com
Laura,Sánchez,22222222B,laura@techcorp.com
Carlos,Ruiz,33333333C,carlos@techcorp.com
EOF

# Subir CSV
curl -X POST http://localhost:8000/api/users/empleados/batch-upload/ \
  -H "Authorization: Token def456..." \
  -F "file=@empleados.csv"
```

### Ejemplo 4: EMPRESA consulta empleados con viajes pendientes

```bash
# Solo funciona si la empresa tiene permisos=true
curl -X GET http://localhost:8000/api/users/empleados/pending/ \
  -H "Authorization: Token def456..."
```

### Ejemplo 5: MASTER actualiza permisos de una empresa

```bash
# Dar permisos de gestión de viajes a una empresa
curl -X PATCH http://localhost:8000/api/users/empresas/1/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "permisos": true
  }'
```

---

## Notas Técnicas

### Arquitectura
- **ViewSets**: Uso de `ModelViewSet` de DRF para operaciones CRUD completas
- **Router**: Configuración automática de URLs con `DefaultRouter`
- **Permissions**: Sistema de permisos personalizados que extiende `BasePermission`
- **Services**: Lógica de negocio separada en `services.py` para reutilización

### Filtrado Automático
El sistema aplica filtrado automático en el método `get_queryset()`:
- MASTER ve todos los registros
- EMPRESA solo ve registros relacionados con su empresa
- EMPLEADO solo ve su propio perfil

### Relaciones
- Cada `EmpresaProfile` tiene un `CustomUser` asociado con rol EMPRESA
- Cada `EmpleadoProfile` tiene un `CustomUser` asociado con rol EMPLEADO
- Cada `EmpleadoProfile` pertenece a una `EmpresaProfile`

### Eliminación en Cascada
- Al eliminar una empresa, se eliminan automáticamente:
  - Su usuario asociado
  - Todos sus empleados
  - Los usuarios de todos sus empleados

---

## Solución de Problemas Comunes

### Error: "Solo MASTER puede listar empresas"
**Solución:** El endpoint `GET /empresas/` solo está disponible para usuarios MASTER. Las empresas solo pueden ver su propio perfil en `GET /empresas/{id}/`.

### Error: "El DNI/NIE ya está asociado a un empleado"
**Solución:** El DNI debe ser único. Verifica si el empleado ya existe en el sistema.

### Error: "No tienes permisos para ver revisiones pendientes"
**Solución:** Para usuarios EMPRESA, el campo `permisos` debe estar en `true`. Solo MASTER puede modificarlo.

### Error: "MASTER debe especificar empresa_id"
**Solución:** Al crear empleados como MASTER, debes incluir el campo `empresa_id` en el body.

### Carga masiva CSV: Algunos empleados se omiten
**Comportamiento esperado:** El sistema omite automáticamente empleados duplicados (por DNI o email) y devuelve la lista de omitidos con la razón.

---

## Changelog

- **v2.0** - Migración completa a ViewSets con DRF Router
- **v1.5** - Añadido endpoint `/empleados/pending/`
- **v1.0** - Versión inicial con vistas basadas en clases

---

## Contacto y Soporte

Para reportar bugs o solicitar nuevas funcionalidades, contacta con el equipo de desarrollo.
