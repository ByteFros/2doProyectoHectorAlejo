#!/bin/bash

# Script para refactorización automática de URLs hardcodeadas
# Ejecutar desde la raíz del proyecto

echo "🔧 Iniciando refactorización automática de URLs..."

# Lista de archivos que necesitan el import de apiRequest
FILES_NEED_IMPORT=(
    "src/components/common/messages/ExpenseSelector.tsx"
    "src/components/common/messages/hooks/useConversationMessages.ts"
    "src/components/common/messages/hooks/useConversations.ts"
    "src/components/common/messages/hooks/useEmployeeSearch.ts"
    "src/components/employee/travel/current-trip/expenses-table/expenses-table.tsx"
    "src/components/hooks/files/useFilePreview.ts"
    "src/components/hooks/trips/useComanyTripsChart.ts"
    "src/components/hooks/trips/useCompanyTripsSummary.ts"
    "src/components/hooks/trips/useEmployeTripsTable.ts"
    "src/components/hooks/trips/useExemptDays.ts"
    "src/components/hooks/trips/useGeneralInfo.ts"
    "src/components/hooks/trips/useMasterEmployeesByCompany.ts"
    "src/components/hooks/trips/useRegisterEmployees.ts"
    "src/components/hooks/trips/useTripsChartGrouped.ts"
    "src/components/hooks/trips/useTripsPerMonth.ts"
    "src/components/hooks/trips/useTripsType.ts"
    "src/components/hooks/use-company-messages.ts"
    "src/components/hooks/use-employee-messages.ts"
    "src/components/hooks/use-master-messages.ts"
    "src/components/hooks/useCitiesReport.ts"
    "src/components/hooks/useCompanies.ts"
    "src/components/hooks/useEmployeeCityStats.ts"
    "src/components/hooks/useEmployeeTravelSummary.ts"
    "src/components/hooks/useFinishedTrips.ts"
    "src/components/hooks/useSpends.ts"
    "src/components/hooks/useTripNotes.ts"
    "src/components/hooks/useTripsChart.ts"
    "src/components/hooks/useUser.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/useEmployeesByCompany.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/useFinalizeTripReview.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/useMasterCSVExport.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/usePendingCompanies.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/usePendingTripsByEmployee.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/usePendingTripscount.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/usePendingTripsDetail.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/useTripDays.ts"
    "src/components/master/dashboard/pending-trips-table/hooks/useUpdateTripDay.ts"
    "src/components/master/manage-companies/add-company/add-company.tsx"
)

echo "📁 Procesando ${#FILES_NEED_IMPORT[@]} archivos..."

# Función para agregar import si no existe
add_import_if_needed() {
    local file="$1"
    
    if [ -f "$file" ]; then
        # Verificar si ya tiene el import
        if ! grep -q "import.*apiRequest.*from.*config/api" "$file"; then
            echo "  ➕ Agregando import a $file"
            
            # Encontrar la línea después de los imports existentes
            if grep -q "^import" "$file"; then
                # Agregar después del último import
                sed -i '/^import.*$/a import { apiRequest } from "../../config/api";' "$file"
            else
                # Agregar al inicio si no hay imports
                sed -i '1i import { apiRequest } from "../../config/api";' "$file"
            fi
        fi
    fi
}

# Procesar cada archivo
for file in "${FILES_NEED_IMPORT[@]}"; do
    add_import_if_needed "$file"
done

echo ""
echo "🔄 Realizando reemplazos de URLs..."

# Reemplazos de patrones comunes
echo "  🔗 Reemplazando fetch calls..."

# Buscar y reemplazar en todos los archivos .ts y .tsx
find src/ -name "*.ts" -o -name "*.tsx" | while read file; do
    if grep -q "http://127.0.0.1:8000" "$file"; then
        echo "  📝 Procesando: $file"
        
        # Reemplazar fetch con apiRequest
        sed -i 's|fetch(`\?'\''http://127\.0\.0\.1:8000/api\([^'\''`]*\)'\''`\?|apiRequest("\1"|g' "$file"
        sed -i 's|fetch("http://127\.0\.0\.1:8000/api\([^"]*\)"|apiRequest("\1"|g' "$file"
        
        # Reemplazar URLs en constantes
        sed -i "s|'http://127\.0\.0\.1:8000/api|'/api|g" "$file"
        sed -i 's|"http://127\.0\.0\.1:8000/api|"/api|g' "$file"
        
        # Casos especiales de template strings
        sed -i 's|`http://127\.0\.0\.1:8000/api\([^`]*\)`|apiRequest(`\1`)|g' "$file"
    fi
done

echo ""
echo "🧹 Limpiando headers redundantes..."

# Limpiar headers redundantes en archivos que usan apiRequest
find src/ -name "*.ts" -o -name "*.tsx" | while read file; do
    if grep -q "apiRequest" "$file"; then
        # Remover Content-Type redundante cuando se usa apiRequest
        sed -i '/Content-Type.*application\/json/d' "$file"
        sed -i '/credentials.*include/d' "$file"
    fi
done

echo ""
echo "✅ Refactorización automática completada!"
echo ""
echo "🔍 Verificando resultados..."
npm run find-hardcoded-urls

echo ""
echo "📋 Próximos pasos manuales:"
echo "  1. Revisar archivos que aún tienen URLs hardcodeadas"
echo "  2. Ajustar imports si hay errores de ruta"
echo "  3. Probar con: npm run dev"
echo "  4. Build de producción: npm run build:production"
