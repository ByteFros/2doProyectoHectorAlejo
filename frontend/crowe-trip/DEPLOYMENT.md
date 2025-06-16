# 🚀 Instrucciones de Despliegue para Producción

## ✅ Estado Actual
- ✅ Variables de entorno configuradas (.env.local, .env.production)
- ✅ Configuración de API centralizada (src/config/api.ts)
- ✅ vite.config.ts actualizado con allowedHosts
- ✅ use-auth.ts refactorizado
- ✅ useTrips.ts refactorizado  
- ✅ useEmployees.ts refactorizado
- ✅ Scripts de package.json actualizados

## 🔧 Próximos Pasos Obligatorios

### 1. Refactorizar Hooks Restantes
Ejecuta este comando para encontrar todos los archivos que aún necesitan refactorización:

```bash
npm run find-hardcoded-urls
```

Los hooks más importantes que probablemente necesiten refactorización:
- `useCompanies.ts`
- `useTripNotes.ts` 
- `useSpends.ts`
- Hooks en `src/components/hooks/trips/`
- Hooks en `src/components/common/messages/hooks/`

### 2. Patrón de Refactorización

Para cada hook que use fetch, seguir este patrón:

**ANTES:**
```typescript
const response = await fetch("http://127.0.0.1:8000/api/endpoint", {
    method: "GET",
    headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${token}`,
    },
    credentials: "include",
});
```

**DESPUÉS:**
```typescript
import { apiRequest } from "../../config/api";

const response = await apiRequest("/endpoint", {
    method: "GET", 
    headers: {
        Authorization: `Token ${token}`,
    },
});
```

### 3. Probar en Desarrollo

```bash
# Verificar configuración
npm run check-config

# Ejecutar en desarrollo
npm run dev

# Verificar que no hay URLs hardcodeadas
npm run find-hardcoded-urls
```

### 4. Build para Producción

```bash
# Build de producción
npm run build:production

# Previsualizar build
npm run preview
```

### 5. Configuración del Backend Django

Asegúrate de que tu backend Django tenga configurado CORS para permitir requests desde `crowe.bronixia.es`:

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://crowe.bronixia.es",
    "http://localhost:5173",  # para desarrollo
    "http://127.0.0.1:5173",  # para desarrollo
]

ALLOWED_HOSTS = [
    "crowe.bronixia.es",
    "localhost",
    "127.0.0.1",
]
```

### 6. Variables de Entorno en Producción

En tu servidor de producción, asegúrate de configurar:

```bash
export VITE_API_BASE_URL=https://crowe.bronixia.es
export VITE_ENVIRONMENT=production
export NODE_ENV=production
```

## 🐛 Solución de Problemas Comunes

### Error: "This host is not allowed"
- ✅ Ya solucionado con allowedHosts en vite.config.ts

### Error de CORS
- Configurar CORS_ALLOWED_ORIGINS en Django
- Verificar que estés usando HTTPS en producción

### URLs no resuelven correctamente
- Verificar que VITE_API_BASE_URL esté configurado
- Ejecutar `npm run check-config` para verificar

### Network requests fallan
- Verificar en DevTools Network tab la URL que se está usando
- Verificar que el backend esté corriendo en la URL esperada

## 📋 Checklist Final

- [ ] Refactorizar todos los hooks restantes
- [ ] Probar `npm run dev` funciona correctamente
- [ ] Probar `npm run build:production` sin errores
- [ ] Verificar `npm run find-hardcoded-urls` no encuentra nada
- [ ] Configurar CORS en backend Django
- [ ] Configurar variables de entorno en servidor de producción
- [ ] Desplegar y probar en https://crowe.bronixia.es
- [ ] Verificar login/logout funciona
- [ ] Verificar todas las funcionalidades principales

## 🚨 Antes de Desplegar

1. **Backup**: Haz backup del código actual que funciona
2. **Testing**: Prueba localmente con las nuevas configuraciones
3. **Gradual**: Despliega primero en un entorno de staging si es posible

¿Necesitas ayuda con algún paso específico?
