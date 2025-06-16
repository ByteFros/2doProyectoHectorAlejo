#!/bin/bash

# Script para refactorizar URLs hardcodeadas en el proyecto Crowe Trip
# Ejecutar desde la raíz del proyecto frontend

echo "🔍 Buscando URLs hardcodeadas en el proyecto..."

# Buscar archivos con URLs hardcodeadas
echo "📁 Archivos que contienen URLs hardcodeadas:"
grep -r "127\.0\.0\.1:8000" src/ --include="*.ts" --include="*.tsx" || echo "No se encontraron referencias a 127.0.0.1:8000"
grep -r "localhost:8000" src/ --include="*.ts" --include="*.tsx" || echo "No se encontraron referencias a localhost:8000"

echo ""
echo "🔧 Lista de archivos que necesitan ser refactorizados:"
echo "   - src/components/hooks/useTrips.ts"
echo "   - src/components/hooks/useEmployees.ts"
echo "   - src/components/hooks/useCompanies.ts"
echo "   - src/components/hooks/useTripNotes.ts"
echo "   - src/components/hooks/useSpends.ts"
echo "   - Y todos los otros hooks que hagan fetch"

echo ""
echo "✅ PASOS COMPLETADOS:"
echo "   ✓ Archivos .env creados"
echo "   ✓ Configuración de API centralizada (src/config/api.ts)"
echo "   ✓ vite.config.ts actualizado"
echo "   ✓ use-auth.ts refactorizado"

echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo "   1. Refactorizar hooks restantes (ver lista arriba)"
echo "   2. Ejecutar 'npm run dev' para probar en desarrollo"
echo "   3. Ejecutar 'npm run build' para probar el build de producción"
echo "   4. Desplegar y probar en crowe.bronixia.es"

echo ""
echo "📝 COMANDO PARA ENCONTRAR MÁS ARCHIVOS:"
echo "   grep -r 'http://127.0.0.1:8000' src/ --include='*.ts' --include='*.tsx'"

echo ""
echo "⚠️  RECUERDA:"
echo "   - Verificar que el backend Django permita CORS desde crowe.bronixia.es"
echo "   - Usar HTTPS en producción"
echo "   - Probar tanto en desarrollo como en producción"
