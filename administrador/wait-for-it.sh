#!/usr/bin/env bash

set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
  >&2 echo "🔄 Esperando a que PostgreSQL esté listo en $host:5432..."
  sleep 2
done

>&2 echo "✅ PostgreSQL está listo. Ejecutando comando: $cmd"
exec $cmd
