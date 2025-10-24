# Análisis de Lógica: Viajes, Días y Gastos

## Estado Actual de la Implementación

### Modelos y Relaciones

```
Viaje (1) ----< DiaViaje (N) ----< Gasto (N)
  │
  └─> estado: PENDIENTE → EN_CURSO → EN_REVISION → FINALIZADO
```

**Viaje**:
- `fecha_inicio`, `fecha_fin`, `dias_viajados`
- `estado`: PENDIENTE, EN_CURSO, EN_REVISION, FINALIZADO, CANCELADO

**DiaViaje**:
- `viaje` (FK)
- `fecha` (date)
- `exento` (boolean, default=True)
- `revisado` (boolean, default=False)

**Gasto**:
- `viaje` (FK)
- `dia` (FK a DiaViaje)
- `fecha_gasto`, `concepto`, `monto`
- `estado`: PENDIENTE, APROBADO, RECHAZADO, JUSTIFICAR

---

## Flujo Actual

### 1. Creación de Viaje
```python
# services.py: crear_viaje()
viaje = Viaje.objects.create(...)
# ❌ NO se crean DiaViaje aquí
```

### 2. Inicio de Viaje
```python
# services.py: iniciar_viaje()
viaje.estado = "EN_CURSO"
# ❌ NO se crean DiaViaje aquí
```

### 3. Carga de Gastos (durante EN_CURSO)
```python
# serializers.py: GastoSerializer.create()
dia, _ = DiaViaje.objects.get_or_create(viaje=viaje, fecha=fecha)
gasto = Gasto.objects.create(dia=dia, ...)
# ✅ DiaViaje se crea ON-DEMAND al crear gasto
```

### 4. Finalizar Viaje
```python
# services.py: finalizar_viaje()
viaje.estado = 'EN_REVISION'
crear_dias_viaje(viaje)  # ✅ Crea TODOS los DiaViaje aquí
```

### 5. Procesar Revisión
```python
# services.py: procesar_revision_viaje()
for dia in viaje.dias.all():
    dia.exento = True/False
    dia.revisado = True
    dia.gastos.update(estado="APROBADO" o "RECHAZADO")
viaje.estado = "FINALIZADO"
```

---

## Problemas Identificados

### 🔴 Problema 1: Viajes FINALIZADOS sin DiaViaje

**Situación**: El script `create_sample_trips.py` crea viajes directamente en estado FINALIZADO.

```python
# En create_sample_trips.py
viaje = Viaje.objects.create(
    estado="FINALIZADO",  # ← Directamente FINALIZADO
    ...
)
# No llama a crear_dias_viaje() ❌
```

**Consecuencia**:
- Viajes FINALIZADOS sin registros DiaViaje
- Contador de días exentos/no exentos = 0
- No se puede revisar el viaje retroactivamente

---

### 🔴 Problema 2: Creación Lazy de DiaViaje

**Situación**: Los DiaViaje se crean de 2 formas diferentes:

1. **On-demand al crear gasto** (línea 75, serializers.py)
2. **Batch al finalizar viaje** (línea 213, services.py)

**Consecuencia**:
- Si cargas gastos solo en 3 de 5 días, solo existen 3 DiaViaje
- Al finalizar, se crean los 2 días faltantes
- Inconsistencia antes/después de finalizar

---

### 🟡 Problema 3: No se valida completitud

**Situación**: `procesar_revision_viaje` no verifica que todos los días tengan gastos.

```python
# No hay validación de:
# - ¿Todos los días tienen al menos 1 gasto?
# - ¿Hay días del viaje sin gastos?
```

**Consecuencia**:
- Se puede finalizar un viaje sin gastos completos
- Días sin gastos quedan como exento=True por defecto

---

### 🟡 Problema 4: Redundancia en modelo Gasto

**Situación**: Gasto tiene ambos:
```python
viaje = models.ForeignKey(Viaje, ...)
dia = models.ForeignKey(DiaViaje, ...)
```

**Consecuencia**:
- Redundancia: `dia.viaje` ya da acceso al viaje
- Riesgo de inconsistencia: ¿Qué pasa si `gasto.viaje != gasto.dia.viaje`?

---

## Soluciones Propuestas

### ✅ Solución 1: Crear DiaViaje al iniciar viaje (RECOMENDADA)

**Cambio**:
```python
def iniciar_viaje(viaje: Viaje) -> Viaje:
    """Inicia un viaje y crea todos los DiaViaje"""
    if date.today() < viaje.fecha_inicio:
        raise ValueError("Aún no puedes iniciar este viaje")

    viaje.estado = "EN_CURSO"
    viaje.save()

    # ✅ Crear todos los días aquí
    crear_dias_viaje(viaje)

    return viaje
```

**Ventajas**:
- ✅ Todos los viajes EN_CURSO tienen DiaViaje completos
- ✅ Se puede validar qué días faltan por cargar gastos
- ✅ Contador funciona desde el inicio
- ✅ No hay creación on-demand confusa

**Desventajas**:
- ⚠️ Viajes PENDIENTES no tienen DiaViaje (pero está bien, no han iniciado)

---

### ✅ Solución 2: Método auxiliar para scripts

**Nuevo método**:
```python
def inicializar_dias_viaje_finalizado(viaje: Viaje) -> List[DiaViaje]:
    """
    Crea DiaViaje para viajes ya finalizados (uso en scripts).

    Args:
        viaje: Viaje en estado FINALIZADO sin DiaViaje

    Returns:
        Lista de DiaViaje creados
    """
    if viaje.estado != "FINALIZADO":
        raise ValueError("Este método es solo para viajes FINALIZADOS")

    dias = crear_dias_viaje(viaje)

    # Marcar todos como exentos y revisados por defecto
    for dia in dias:
        dia.exento = True
        dia.revisado = True
        dia.save()

    return dias
```

**Uso en script**:
```python
# En create_sample_trips.py
viaje = Viaje.objects.create(estado="FINALIZADO", ...)
inicializar_dias_viaje_finalizado(viaje)  # ✅ Crear días
```

---

### ✅ Solución 3: Validar completitud en revisión

**Cambio en `procesar_revision_viaje`**:
```python
@transaction.atomic
def procesar_revision_viaje(viaje: Viaje, dias_data: List[Dict], ...):
    dias_viaje = viaje.dias.all()

    # ✅ Validar que existen todos los días
    dias_esperados = (viaje.fecha_fin - viaje.fecha_inicio).days + 1
    if dias_viaje.count() != dias_esperados:
        raise ValueError(
            f"Faltan días por crear. Esperados: {dias_esperados}, "
            f"Encontrados: {dias_viaje.count()}"
        )

    # ✅ Validar que todos los días tienen gastos (opcional)
    dias_sin_gastos = [d for d in dias_viaje if not d.gastos.exists()]
    if dias_sin_gastos:
        raise ValueError(
            f"Los siguientes días no tienen gastos: "
            f"{[d.fecha for d in dias_sin_gastos]}"
        )

    # ... resto del código
```

---

### ✅ Solución 4: Eliminar redundancia en Gasto (opcional)

**Cambio en modelo Gasto**:
```python
class Gasto(models.Model):
    # ❌ Eliminar este campo
    # viaje = models.ForeignKey(Viaje, ...)

    # ✅ Mantener solo este
    dia = models.ForeignKey(DiaViaje, ...)

    # Acceso al viaje: gasto.dia.viaje
```

**Migración necesaria**: Sí, requiere migración de BD.

**Ventaja**:
- ✅ No hay redundancia
- ✅ No hay riesgo de inconsistencia

**Desventaja**:
- ⚠️ Queries más complejas: `Gasto.objects.filter(dia__viaje=viaje)`
- ⚠️ Requiere refactorización de código existente

---

## Propuesta de Implementación

### Fase 1: Arreglos Inmediatos (Sin breaking changes)

1. **Modificar `iniciar_viaje`** para crear DiaViaje
2. **Crear método auxiliar** `inicializar_dias_viaje_finalizado`
3. **Actualizar script** `create_sample_trips.py` para usar el nuevo método
4. **Añadir validaciones** en `procesar_revision_viaje`

### Fase 2: Crear script de gastos

1. **Nuevo comando** `create_sample_expenses.py`:
   - Genera gastos realistas por tipo (transporte, alojamiento, comida)
   - Distribuye gastos en todos los días del viaje
   - Marca algunos días como exentos/no exentos aleatoriamente
   - Crea más viajes EN_REVISION

### Fase 3: Refactorización (Opcional, futuro)

1. Eliminar campo `viaje` de modelo Gasto
2. Migración de base de datos
3. Actualizar queries y serializers

---

## Recomendación Final

**Para continuar ahora:**

1. ✅ **Implementar Solución 1 y 2** (crear DiaViaje al iniciar + método auxiliar)
2. ✅ **Crear comando de gastos** que use la lógica correcta
3. ⏸️ **Posponer Solución 4** (eliminar redundancia) para no romper código existente

**Código que modificar:**

1. `users/viajes/services.py`:
   - Modificar `iniciar_viaje()`
   - Añadir `inicializar_dias_viaje_finalizado()`
   - Añadir validaciones en `procesar_revision_viaje()`

2. `users/management/commands/create_sample_trips.py`:
   - Llamar a `inicializar_dias_viaje_finalizado()` después de crear viajes FINALIZADOS

3. Crear `users/management/commands/create_sample_expenses.py`:
   - Generar gastos realistas
   - Crear viajes EN_REVISION
   - Usar lógica correcta de DiaViaje

---

## Pregunta para ti

¿Quieres que implemente estas soluciones en este orden?

1. Primero arreglamos la lógica de DiaViaje
2. Luego creamos el comando de gastos con la lógica correcta
3. Probamos todo junto

O prefieres solo crear el comando de gastos con la lógica actual (sin modificar services.py)?
