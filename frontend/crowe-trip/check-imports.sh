# Script para verificar imports de config/api
echo "🔍 Verificando imports de config/api..."

# Buscar todos los archivos que importan config/api
echo "📁 Archivos que importan config/api:"
grep -r "from.*config/api" src/ --include="*.ts" --include="*.tsx" 2>/dev/null || echo "No se encontraron imports de config/api"

echo ""
echo "🔧 Verificando si existen rutas relativas incorrectas:"
grep -r "from.*\.\..*config" src/ --include="*.ts" --include="*.tsx" 2>/dev/null || echo "No se encontraron rutas relativas a config"

echo ""
echo "✅ Estado de archivos de configuración:"
if [ -f "src/config/api.ts" ]; then
    echo "   ✓ src/config/api.ts existe"
else
    echo "   ❌ src/config/api.ts NO existe"
fi

if [ -f ".env.local" ]; then
    echo "   ✓ .env.local existe"
else
    echo "   ❌ .env.local NO existe"
fi

if [ -f ".env.production" ]; then
    echo "   ✓ .env.production existe"
else
    echo "   ❌ .env.production NO existe"
fi

echo ""
echo "🚀 Comandos para probar:"
echo "   npm run dev          # Iniciar servidor de desarrollo"
echo "   npm run check-config # Verificar variables de entorno"
echo "   npm run typecheck    # Verificar tipos TypeScript"
