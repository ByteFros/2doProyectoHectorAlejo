#!/bin/bash

# ====================================
# SCRIPTS DE DESARROLLO Y PRODUCCIÓN
# ====================================

echo "🚀 Crowe Trip - Docker Management Scripts"
echo "========================================="

case "$1" in
  "dev")
    echo "🔧 Iniciando entorno de desarrollo..."
    docker-compose down
    docker-compose up --build -d
    echo "✅ Entorno de desarrollo iniciado:"
    echo "   Frontend: http://localhost:5173"
    echo "   Backend:  http://localhost:8000"
    echo "   Database: localhost:5432"
    ;;
  
  "prod")
    echo "🏭 Iniciando entorno de producción..."
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up --build -d
    echo "✅ Entorno de producción iniciado:"
    echo "   Frontend: http://localhost"
    echo "   Backend:  (interno)"
    ;;
  
  "stop")
    echo "🛑 Deteniendo todos los contenedores..."
    docker-compose down
    docker-compose -f docker-compose.prod.yml down
    echo "✅ Contenedores detenidos"
    ;;
  
  "logs")
    echo "📋 Mostrando logs..."
    if [ "$2" == "prod" ]; then
      docker-compose -f docker-compose.prod.yml logs -f
    else
      docker-compose logs -f
    fi
    ;;
  
  "clean")
    echo "🧹 Limpiando contenedores y volúmenes..."
    docker-compose down -v
    docker-compose -f docker-compose.prod.yml down -v
    docker system prune -f
    echo "✅ Limpieza completada"
    ;;
  
  "test")
    echo "🧪 Ejecutando tests..."
    docker-compose exec backend python manage.py test
    docker-compose exec frontend npm test
    ;;
  
  *)
    echo "Uso: $0 {dev|prod|stop|logs|clean|test}"
    echo ""
    echo "Comandos disponibles:"
    echo "  dev    - Iniciar entorno de desarrollo"
    echo "  prod   - Iniciar entorno de producción"
    echo "  stop   - Detener todos los contenedores"
    echo "  logs   - Ver logs (agregar 'prod' para producción)"
    echo "  clean  - Limpiar contenedores y volúmenes"
    echo "  test   - Ejecutar tests"
    exit 1
    ;;
esac
