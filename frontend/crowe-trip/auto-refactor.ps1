# PowerShell script para refactorización masiva de URLs
# Ejecutar desde PowerShell en la raíz del proyecto

Write-Host "🔧 Iniciando refactorización automática de URLs..." -ForegroundColor Green

# Lista de archivos que necesitan ser refactorizados
$files = @(
    "src\components\common\messages\ExpenseSelector.tsx",
    "src\components\common\messages\hooks\useConversationMessages.ts",
    "src\components\common\messages\hooks\useConversations.ts",
    "src\components\common\messages\hooks\useEmployeeSearch.ts",
    "src\components\employee\travel\current-trip\expenses-table\expenses-table.tsx",
    "src\components\hooks\files\useFilePreview.ts",
    "src\components\hooks\trips\useComanyTripsChart.ts",
    "src\components\hooks\trips\useCompanyTripsSummary.ts",
    "src\components\hooks\trips\useEmployeTripsTable.ts",
    "src\components\hooks\trips\useExemptDays.ts",
    "src\components\hooks\trips\useGeneralInfo.ts",
    "src\components\hooks\trips\useMasterEmployeesByCompany.ts",
    "src\components\hooks\trips\useRegisterEmployees.ts",
    "src\components\hooks\trips\useTripsChartGrouped.ts",
    "src\components\hooks\trips\useTripsPerMonth.ts",
    "src\components\hooks\trips\useTripsType.ts",
    "src\components\hooks\use-company-messages.ts",
    "src\components\hooks\use-employee-messages.ts",
    "src\components\hooks\use-master-messages.ts",
    "src\components\hooks\useCitiesReport.ts",
    "src\components\hooks\useEmployeeCityStats.ts",
    "src\components\hooks\useEmployeeTravelSummary.ts",
    "src\components\hooks\useFinishedTrips.ts",
    "src\components\hooks\useSpends.ts",
    "src\components\hooks\useTripNotes.ts",
    "src\components\hooks\useTripsChart.ts",
    "src\components\hooks\useUser.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\useEmployeesByCompany.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\useFinalizeTripReview.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\useMasterCSVExport.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\usePendingCompanies.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\usePendingTripsByEmployee.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\usePendingTripscount.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\usePendingTripsDetail.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\useTripDays.ts",
    "src\components\master\dashboard\pending-trips-table\hooks\useUpdateTripDay.ts",
    "src\components\master\manage-companies\add-company\add-company.tsx"
)

Write-Host "📁 Procesando $($files.Count) archivos..." -ForegroundColor Yellow

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  📝 Procesando: $file" -ForegroundColor Cyan
        
        $content = Get-Content $file -Raw
        
        # Agregar import si no existe
        if ($content -notmatch "import.*apiRequest.*from.*config/api") {
            # Determinar la ruta relativa correcta para el import
            $depth = ($file -split "\\").Count - 2  # Restar 2 por src y el archivo
            $relativePath = "../" * $depth + "config/api"
            
            $importLine = "import { apiRequest } from `"$relativePath`";"
            
            # Agregar después de los imports existentes
            if ($content -match "^import") {
                $lines = $content -split "`n"
                $lastImportIndex = -1
                for ($i = 0; $i -lt $lines.Count; $i++) {
                    if ($lines[$i] -match "^import") {
                        $lastImportIndex = $i
                    }
                }
                if ($lastImportIndex -ge 0) {
                    $lines = $lines[0..$lastImportIndex] + $importLine + $lines[($lastImportIndex + 1)..($lines.Count - 1)]
                    $content = $lines -join "`n"
                }
            } else {
                $content = $importLine + "`n" + $content
            }
        }
        
        # Reemplazar URLs hardcodeadas
        $content = $content -replace 'fetch\(`?"?http://127\.0\.0\.1:8000/api([^`"]*)`?"?\)', 'apiRequest("$1")'
        $content = $content -replace "'http://127\.0\.0\.1:8000/api", "'/api"
        $content = $content -replace '"http://127\.0\.0\.1:8000/api', '"/api'
        
        # Limpiar headers redundantes
        $content = $content -replace '\s*"Content-Type":\s*"application/json",?\s*', ''
        $content = $content -replace '\s*credentials:\s*"include",?\s*', ''
        
        # Escribir archivo modificado
        Set-Content $file $content -NoNewline
        
        Write-Host "    ✅ Refactorizado" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Archivo no encontrado: $file" -ForegroundColor Red
    }
}

Write-Host "`n🔍 Verificando resultados..." -ForegroundColor Green
npm run find-hardcoded-urls

Write-Host "`n✅ Refactorización completada!" -ForegroundColor Green
Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Probar con: npm run dev" -ForegroundColor White
Write-Host "  2. Verificar imports en archivos que den error" -ForegroundColor White
Write-Host "  3. Build de producción: npm run build:production" -ForegroundColor White
