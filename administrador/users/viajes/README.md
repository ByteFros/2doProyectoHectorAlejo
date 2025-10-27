⚠️ **Estados actualizados**: Desde ahora solo se usan `EN_REVISION` y `REVISADO`. Las secciones que mencionan estados previos (`PENDIENTE`, `APROBADO`, `EN_CURSO`, `CANCELADO`) están en revisión y se consideran legacy.

# Módulo de Viajes

Este módulo gestiona el ciclo completo de viajes de negocio de los empleados, desde la solicitud inicial hasta la revisión final, incluyendo la gestión de días de viaje y gastos asociados.

## Tabla de Contenidos

1. [Flujo de Estados](#flujo-de-estados)
2. [Modelos Relacionados](#modelos-relacionados)
3. [Lógica de Negocio](#lógica-de-negocio)
4. [Endpoints Disponibles](#endpoints-disponibles)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Scripts de Datos](#scripts-de-datos)

---

## Flujo de Estados

```
┌─────────────┐
│  PENDIENTE  │ ← Viaje solicitado
└──────┬──────┘
       │ iniciar_viaje()
       ↓
┌─────────────┐
│  EN_CURSO   │ ← Viaje en progreso (se crean DiaViaje)
└──────┬──────┘
       │ finalizar_viaje()
       ↓
┌─────────────┐
│ EN_REVISION │ ← Esperando aprobación de empresa
└──────┬──────┘
       │ procesar_revision_viaje()
       ↓
┌─────────────┐
│ FINALIZADO  │ ← Viaje completado y revisado
└─────────────┘

       ┌─────────────┐
       │  CANCELADO  │ ← Viaje cancelado (desde PENDIENTE)
       └─────────────┘
```

### Estados Disponibles

| Estado | Descripción | Quién puede cambiar |
|--------|-------------|---------------------|
| `PENDIENTE` | Viaje solicitado, esperando inicio | Sistema (automático si fecha >= hoy) |
| `EN_CURSO` | Viaje en progreso | EMPLEADO (iniciar) |
| `EN_REVISION` | Finalizado, esperando revisión | EMPLEADO (finalizar) |
| `FINALIZADO` | Revisado y completado | EMPRESA/MASTER (revisar) |
| `CANCELADO` | Viaje cancelado | EMPLEADO/EMPRESA |

---

## Modelos Relacionados

### Viaje

Representa un viaje de negocio completo.

```python
class Viaje(models.Model):
    empleado = ForeignKey(EmpleadoProfile)
    empresa = ForeignKey(EmpresaProfile)
    destino = CharField(max_length=255)  # "Madrid, España"
    ciudad = CharField(max_length=255)
    pais = CharField(max_length=255)
    es_internacional = BooleanField()
    fecha_inicio = DateField()
    fecha_fin = DateField()
    dias_viajados = PositiveIntegerField()
    estado = CharField(choices=ESTADO_CHOICES)
    empresa_visitada = CharField()
    motivo = TextField()
    fecha_solicitud = DateTimeField(auto_now_add=True)
```

**Relaciones:**
- `viaje.dias` → Lista de DiaViaje
- `viaje.gasto_set` → Lista de Gastos

---

### DiaViaje

Representa cada día individual de un viaje.

```python
class DiaViaje(models.Model):
    viaje = ForeignKey(Viaje, related_name='dias')
    fecha = DateField()
    exento = BooleanField(default=True)    # ¿Día aprobado?
    revisado = BooleanField(default=False) # ¿Ya fue revisado?
```

**Relaciones:**
- `dia.gastos` → Lista de Gastos de ese día
- `dia.viaje` → Viaje al que pertenece

**Uso en Dashboard:**
- Contador de días exentos/no exentos por empleado
- Validación de gastos por día

---

### Gasto

Representa un gasto asociado a un día de viaje.

```python
class Gasto(models.Model):
    empleado = ForeignKey(EmpleadoProfile)
    empresa = ForeignKey(EmpresaProfile)
    viaje = ForeignKey(Viaje)
    dia = ForeignKey(DiaViaje, related_name='gastos')
    concepto = TextField()
    monto = DecimalField(max_digits=10, decimal_places=2)
    fecha_gasto = DateField()
    estado = CharField(choices=ESTADO_CHOICES)  # PENDIENTE, APROBADO, RECHAZADO, JUSTIFICAR
    comprobante = FileField(upload_to='comprobantes/')
    fecha_solicitud = DateTimeField(auto_now_add=True)
```

---

## Lógica de Negocio

### Creación de DiaViaje

Los `DiaViaje` se crean automáticamente en diferentes momentos:

1. **Al iniciar viaje** (`iniciar_viaje()`):
   ```python
   viaje.estado = "EN_CURSO"
   crear_dias_viaje(viaje)  # Crea todos los DiaViaje
   ```

2. **Viajes históricos** (scripts):
   ```python
   inicializar_dias_viaje_finalizado(viaje, exentos=True)
   ```

3. **Fallback al finalizar** (viajes antiguos sin días):
   ```python
   if viaje.dias.count() < dias_esperados:
       crear_dias_viaje(viaje)
   ```

### Validaciones Importantes

1. **Conflicto de fechas**: Un empleado no puede tener viajes solapados
2. **Completitud de días**: Un viaje EN_REVISION debe tener todos sus DiaViaje
3. **Gastos por día**: Los gastos deben estar asociados a un DiaViaje válido
4. **Permisos de empresa**: Solo empresas con `permisos=True` pueden revisar viajes

---

## Endpoints Disponibles

### Gestión de Viajes

#### `POST /viajes/new/`
Crea un nuevo viaje.

**Permisos:**
- ✅ EMPLEADO: Puede crear sus propios viajes
- ✅ EMPRESA: Puede crear viajes para sus empleados
- ✅ MASTER: Puede crear viajes para cualquier empleado

**Body:**
```json
{
  "destino": "Madrid, España",
  "fecha_inicio": "2025-11-15",
  "fecha_fin": "2025-11-17",
  "motivo": "Reunión con cliente",
  "empresa_visitada": "Acme Corp"
}
```

**Respuesta:**
```json
{
  "id": 123,
  "empleado": {...},
  "empresa": {...},
  "destino": "Madrid, España",
  "ciudad": "Madrid",
  "pais": "España",
  "es_internacional": false,
  "fecha_inicio": "2025-11-15",
  "fecha_fin": "2025-11-17",
  "dias_viajados": 3,
  "estado": "PENDIENTE",
  "empresa_visitada": "Acme Corp",
  "motivo": "Reunión con cliente",
  "fecha_solicitud": "2025-10-23T14:30:00Z"
}
```

---

#### `POST /viajes/{id}/iniciar/`
Inicia un viaje (PENDIENTE → EN_CURSO) y crea todos los DiaViaje.

**Permisos:**
- ✅ EMPLEADO: Solo sus propios viajes
- ✅ EMPRESA: Viajes de sus empleados
- ✅ MASTER: Cualquier viaje

**Validaciones:**
- La fecha de inicio debe ser hoy o pasada
- No se puede iniciar un viaje futuro

**Efecto:**
- Cambia estado a EN_CURSO
- Crea N objetos DiaViaje (uno por cada día)
- Los DiaViaje se crean con `exento=True`, `revisado=False`

---

#### `PUT /viajes/{id}/end/`
Finaliza un viaje (EN_CURSO → EN_REVISION).

**Permisos:**
- ✅ EMPLEADO: Solo sus propios viajes
- ✅ EMPRESA: Viajes de sus empleados
- ✅ MASTER: Cualquier viaje

**Validaciones:**
- El viaje debe estar EN_CURSO
- Verifica que existan todos los DiaViaje

**Efecto:**
- Cambia estado a EN_REVISION
- El viaje queda listo para revisión por la empresa

---

#### `POST /viajes/{id}/finalizar_revision/`
Procesa la revisión final de un viaje (EN_REVISION → FINALIZADO).

**Permisos:**
- ✅ EMPRESA (con permisos=true): Viajes de sus empleados
- ✅ MASTER: Cualquier viaje
- ❌ EMPLEADO: No autorizado

**Body:**
```json
{
  "dias_data": [
    {"id": 1, "exento": true},
    {"id": 2, "exento": false},
    {"id": 3, "exento": true}
  ],
  "motivo": "Día 2 requiere justificación adicional"
}
```

**Efecto:**
- Marca cada día como revisado
- Actualiza `exento` según lo enviado
- Actualiza estado de gastos del día:
  - Día exento=true → gastos APROBADO
  - Día exento=false → gastos RECHAZADO
- Cambia viaje a FINALIZADO
- Crea conversación si hay días no exentos

**Respuesta:**
```json
{
  "viaje": {...},
  "dias_procesados": 3,
  "dias_no_exentos": 1,
  "conversacion_creada": true
}
```

---

#### `DELETE /viajes/{id}/cancelar/`
Cancela un viaje (PENDIENTE → CANCELADO).

**Permisos:**
- ✅ EMPLEADO: Solo sus propios viajes PENDIENTES
- ✅ EMPRESA: Viajes pendientes de sus empleados
- ✅ MASTER: Cualquier viaje pendiente

**Validaciones:**
- Solo se pueden cancelar viajes PENDIENTES

---

### Consulta de Viajes

#### `GET /viajes/all/`
Lista todos los viajes (filtrados por rol).

**Permisos:**
- ✅ MASTER: Ve todos los viajes
- ✅ EMPRESA: Solo viajes de sus empleados
- ✅ EMPLEADO: Solo sus propios viajes

**Query Parameters:**
- `?estado=PENDIENTE` - Filtrar por estado
- `?empleado=5` - Filtrar por empleado (solo MASTER/EMPRESA)
- `?fecha_inicio__gte=2025-01-01` - Filtrar por fecha

**Respuesta:**
```json
[
  {
    "id": 123,
    "empleado": {
      "id": 10,
      "nombre": "Juan",
      "apellido": "Pérez"
    },
    "empresa": {...},
    "destino": "Madrid, España",
    "fecha_inicio": "2025-11-15",
    "fecha_fin": "2025-11-17",
    "estado": "EN_REVISION",
    "dias_viajados": 3
  }
]
```

---

#### `GET /viajes/en-curso/`
Obtiene el viaje en curso del empleado autenticado.

**Permisos:**
- ✅ EMPLEADO: Su viaje en curso
- ❌ EMPRESA/MASTER: No aplica (deben usar `/viajes/all/`)

**Respuesta:**
```json
{
  "id": 123,
  "destino": "Barcelona, España",
  "fecha_inicio": "2025-10-22",
  "fecha_fin": "2025-10-24",
  "estado": "EN_CURSO",
  "dias_viajados": 3
}
```

Si no hay viaje en curso: `404 Not Found`

---

#### `GET /viajes/over/`
Lista viajes finalizados del empleado autenticado.

**Permisos:**
- ✅ EMPLEADO: Sus viajes finalizados
- ✅ EMPRESA: Viajes finalizados de sus empleados
- ✅ MASTER: Todos los viajes finalizados

**Respuesta:**
```json
[
  {
    "id": 100,
    "destino": "París, Francia",
    "fecha_inicio": "2025-09-10",
    "fecha_fin": "2025-09-12",
    "estado": "FINALIZADO",
    "dias_viajados": 3
  }
]
```

---

#### `GET /viajes/pending/`
Obtiene información de viajes pendientes de revisión.

**Permisos:**
- ✅ MASTER: Todos los viajes EN_REVISION
- ✅ EMPRESA (con permisos=true): Viajes EN_REVISION de sus empleados
- ❌ EMPRESA (sin permisos): No autorizado
- ❌ EMPLEADO: No autorizado

**Respuesta:**
```json
{
  "pending_count": 5,
  "trips": [
    {
      "id": 120,
      "tripDates": ["2025-10-15", "2025-10-17"],
      "destination": "Lisboa, Portugal",
      "info": "Conferencia anual",
      "employeeName": "María García",
      "companyVisited": "Cliente Beta"
    }
  ]
}
```

---

#### `GET /empresas/{empresa_id}/empleados/{empleado_id}/viajes/pending/`
Lista viajes pendientes de un empleado específico.

**Permisos:**
- ✅ MASTER: Cualquier empleado
- ✅ EMPRESA: Solo empleados de su empresa
- ❌ EMPLEADO: No autorizado

**Respuesta:**
```json
[
  {
    "id": 125,
    "destino": "Berlín, Alemania",
    "fecha_inicio": "2025-11-01",
    "fecha_fin": "2025-11-03",
    "estado": "EN_REVISION"
  }
]
```

---

### Gestión de Días de Viaje

#### `GET /viajes/{viaje_id}/dias/`
Lista todos los días de un viaje con sus gastos.

**Permisos:**
- ✅ MASTER: Cualquier viaje
- ✅ EMPRESA: Viajes de sus empleados
- ✅ EMPLEADO: Sus propios viajes

**Respuesta:**
```json
[
  {
    "id": 1,
    "fecha": "2025-11-15",
    "exento": true,
    "revisado": true,
    "gastos": [
      {
        "id": 50,
        "concepto": "Hotel - Habitación individual",
        "monto": "120.00",
        "estado": "APROBADO",
        "fecha_gasto": "2025-11-15"
      }
    ]
  },
  {
    "id": 2,
    "fecha": "2025-11-16",
    "exento": false,
    "revisado": true,
    "gastos": [
      {
        "id": 51,
        "concepto": "Comida rápida",
        "monto": "15.50",
        "estado": "RECHAZADO",
        "fecha_gasto": "2025-11-16"
      }
    ]
  }
]
```

---

#### `PATCH /viajes/{id}/reabrir/`
Reabre un viaje previamente revisado para solicitar información adicional.

**Permisos:**
- ✅ MASTER: Puede reabrir cualquier viaje
- ✅ EMPRESA (con permisos=true): Puede reabrir viajes de su empresa
- ❌ EMPLEADO: No autorizado

**Respuesta:**
```json
{
  "message": "Viaje reabierto. Los días y gastos deberán revisarse nuevamente."
}
```

**Efectos secundarios:**
- El viaje vuelve a estado `EN_REVISION`
- Todos los días se marcan con `revisado=false`
- Los gastos asociados se restablecen a estado `PENDIENTE`


---

#### `PUT /dias/{dia_id}/review/`
Revisa un día de viaje (marca como exento o no exento) usando únicamente el identificador del día.

**Permisos:**
- ✅ EMPRESA (con permisos=true): Puede revisar días de sus viajes en revisión
- ✅ MASTER: Puede revisar cualquier día
- ❌ EMPLEADO: No autorizado

**Body:**
```json
{
  "exento": false
}
```

**Efecto:**
- Actualiza el estado del día (`revisado=true` automáticamente)
- Cambia el estado de los gastos asociados (`APROBADO` si `exento=true`, `RECHAZADO` en caso contrario)
- Si todos los días del viaje quedan revisados, el viaje pasa a `REVISADO`

---

### Estadísticas

#### `GET /viajes/empleados/ciudades/`
Obtiene estadísticas de ciudades visitadas por el empleado autenticado.

**Permisos:**
- ✅ EMPLEADO: Sus propias estadísticas
- ✅ EMPRESA: Estadísticas de sus empleados (TODO: implementar filtro)
- ✅ MASTER: Estadísticas de cualquier empleado (TODO: implementar filtro)

**Respuesta:**
```json
[
  {
    "city": "Madrid",
    "trips": 5,
    "days": 15,
    "nonExemptDays": 2,
    "exemptDays": 13
  },
  {
    "city": "Barcelona",
    "trips": 3,
    "days": 9,
    "nonExemptDays": 1,
    "exemptDays": 8
  }
]
```

**Uso en Dashboard:**
- Mostrar destinos más visitados
- Calcular total de días exentos/no exentos por empleado

---

#### `GET /viajes/empleados/viaje-en-curso/`
Verifica si el empleado tiene un viaje en curso.

**Permisos:**
- ✅ EMPLEADO: Verifica su propio viaje

**Respuesta:**
```json
{
  "tiene_viaje_en_curso": true,
  "viaje_id": 123
}
```

O:
```json
{
  "tiene_viaje_en_curso": false
}
```

---

## Ejemplos de Uso

### Flujo Completo: Empleado crea y completa un viaje

```bash
# 1. Empleado crea viaje
POST /api/users/viajes/new/
Authorization: Token {empleado_token}
{
  "destino": "Madrid, España",
  "fecha_inicio": "2025-11-15",
  "fecha_fin": "2025-11-17",
  "motivo": "Reunión trimestral",
  "empresa_visitada": "Acme Corp"
}
# → Respuesta: viaje con estado "PENDIENTE"

# 2. Día del viaje: empleado inicia el viaje
POST /api/users/viajes/123/iniciar/
Authorization: Token {empleado_token}
# → Crea 3 DiaViaje (15, 16, 17 de noviembre)
# → Cambia estado a "EN_CURSO"

# 3. Durante el viaje: empleado registra gastos
POST /api/users/gastos/new/
Authorization: Token {empleado_token}
{
  "viaje_id": 123,
  "concepto": "Hotel",
  "monto": 120.00,
  "fecha_gasto": "2025-11-15"
}
# → Gasto asociado automáticamente al DiaViaje del 15/11

# 4. Al terminar: empleado finaliza el viaje
PUT /api/users/viajes/123/end/
Authorization: Token {empleado_token}
# → Cambia estado a "EN_REVISION"
# → Queda listo para revisión de empresa

# 5. Empresa revisa el viaje
POST /api/users/viajes/123/finalizar_revision/
Authorization: Token {empresa_token}
{
  "dias_data": [
    {"id": 1, "exento": true},
    {"id": 2, "exento": true},
    {"id": 3, "exento": false}
  ],
  "motivo": "Día 3 sin justificantes"
}
# → Marca días como revisados
# → Aprueba/rechaza gastos según día
# → Cambia estado a "FINALIZADO"
```

---

### Dashboard React: Consultar viajes con estadísticas

```javascript
// 1. Ver empleado con todos sus viajes
const response = await fetch(
  '/api/users/empleados/10/?include=viajes',
  {
    headers: { 'Authorization': `Token ${token}` }
  }
)

const empleado = await response.json()
console.log(empleado.viajes)  // Todos los viajes del empleado
console.log(empleado.viajes_count)  // Total de viajes

// 2. Obtener estadísticas de ciudades
const stats = await fetch(
  '/api/users/viajes/empleados/ciudades/',
  {
    headers: { 'Authorization': `Token ${token}` }
  }
)

const ciudades = await stats.json()
// Calcular total de días exentos/no exentos
const totalExentos = ciudades.reduce((sum, c) => sum + c.exemptDays, 0)
const totalNoExentos = ciudades.reduce((sum, c) => sum + c.nonExemptDays, 0)
```

---

### Empresa: Revisar viajes pendientes

```bash
# 1. Listar viajes pendientes de revisión
GET /api/users/viajes/pending/
Authorization: Token {empresa_token}

# 2. Ver detalles de un viaje específico con días y gastos
GET /api/users/viajes/123/dias/
Authorization: Token {empresa_token}

# 3. Procesar revisión
POST /api/users/viajes/123/finalizar_revision/
Authorization: Token {empresa_token}
{
  "dias_data": [
    {"id": 1, "exento": true},
    {"id": 2, "exento": false}
  ],
  "motivo": "Falta justificante día 2"
}
```

---

## Scripts de Datos

### Cargar Datos de Prueba

```bash
# 1. Crear empresas y empleados
python manage.py load_sample_data
# → 2 empresas
# → 10 empleados por empresa

# 2. Crear viajes con destinos reales
python manage.py create_sample_trips --trips-per-employee 5
# → 5 viajes por empleado
# → Destinos nacionales e internacionales
# → Mayoría FINALIZADOS, algunos EN_REVISION
# → DiaViaje creados automáticamente

# 3. Crear gastos realistas
python manage.py create_sample_expenses
# → Gastos distribuidos en días
# → Categorías: alojamiento, transporte, comida, otros
# → Montos realistas
# → 10 viajes con gastos + 5 viajes EN_REVISION

# 4. Limpiar y recargar todo
python manage.py load_sample_data --clear
python manage.py create_sample_trips --clear --trips-per-employee 10
python manage.py create_sample_expenses --clear-gastos
```

---

## Tests Disponibles

### Tests de Servicios (16 tests)

```bash
# Ejecutar tests de lógica de negocio
python manage.py test users.viajes.tests.test_viajes_services -v 2
```

**Cobertura:**
- ✅ Creación de DiaViaje
- ✅ Iniciar viaje (crea días automáticamente)
- ✅ Finalizar viaje (con validaciones)
- ✅ Inicializar días para viajes históricos
- ✅ Procesar revisión (con validaciones de completitud)
- ✅ Flujo completo de integración

---

## Matriz de Permisos

### Operaciones por Rol

| Endpoint | MASTER | EMPRESA | EMPLEADO |
|----------|--------|---------|----------|
| Crear viaje | ✅ Todos | ✅ Sus empleados | ✅ Propio |
| Listar viajes | ✅ Todos | ✅ Sus empleados | ✅ Propios |
| Ver viaje en curso | ✅ | ✅ | ✅ Propio |
| Iniciar viaje | ✅ Todos | ✅ Sus empleados | ✅ Propio |
| Finalizar viaje | ✅ Todos | ✅ Sus empleados | ✅ Propio |
| Cancelar viaje | ✅ Todos | ✅ Sus empleados | ✅ Propio |
| Ver pendientes | ✅ Todos | ✅ Con permisos | ❌ |
| Revisar viaje | ✅ Todos | ✅ Con permisos | ❌ |
| Ver días | ✅ Todos | ✅ Sus empleados | ✅ Propios |
| Actualizar día | ✅ Todos | ✅ Con permisos | ❌ |
| Estadísticas | ✅ Todos | ✅ Sus empleados | ✅ Propias |

---

## Validaciones de Negocio

### Al Crear Viaje
- ✅ Fecha fin >= fecha inicio
- ✅ No hay conflicto con otros viajes del empleado
- ✅ El empleado pertenece a la empresa (si lo crea EMPRESA)

### Al Iniciar Viaje
- ✅ El viaje debe estar PENDIENTE
- ✅ La fecha de inicio debe ser hoy o pasada
- ✅ Crea todos los DiaViaje (uno por cada día)

### Al Finalizar Viaje
- ✅ El viaje debe estar EN_CURSO
- ✅ Verifica que existan todos los DiaViaje esperados

### Al Revisar Viaje
- ✅ El viaje debe estar EN_REVISION
- ✅ Todos los DiaViaje deben existir
- ✅ Todos los días enviados deben pertenecer al viaje
- ✅ La empresa debe tener permisos de revisión

---

## Solución de Problemas

### Error: "Faltan días por crear"
**Causa:** El viaje no tiene todos los DiaViaje creados.

**Solución:**
```python
from users.viajes.services import crear_dias_viaje
crear_dias_viaje(viaje)
```

### Error: "Aún no puedes iniciar este viaje"
**Causa:** La fecha de inicio es futura.

**Solución:** Espera a que llegue la fecha o cambia la fecha del viaje.

### Error: "Solo puedes finalizar un viaje en curso"
**Causa:** El viaje no está EN_CURSO.

**Solución:** Primero inicia el viaje con `POST /viajes/{id}/iniciar/`

### Días exentos/no exentos = 0
**Causa:** Los viajes se crearon sin DiaViaje (antes de la corrección de lógica).

**Solución:**
```python
from users.viajes.services import inicializar_dias_viaje_finalizado
from users.models import Viaje

for viaje in Viaje.objects.filter(estado='FINALIZADO'):
    if viaje.dias.count() == 0:
        inicializar_dias_viaje_finalizado(viaje)
```

---

## Changelog

- **v2.1** - Corrección de lógica: DiaViaje se crean al iniciar viaje
- **v2.0** - Añadido método `inicializar_dias_viaje_finalizado()` para scripts
- **v1.5** - Añadidas validaciones de completitud en revisión
- **v1.0** - Versión inicial del módulo de viajes

---

## Referencias

- [Análisis de Lógica de Viajes](../../ANALISIS_LOGICA_VIAJES.md)
- [Tests de Servicios](./tests/test_viajes_services.py)
- [Servicios de Lógica de Negocio](./services.py)
