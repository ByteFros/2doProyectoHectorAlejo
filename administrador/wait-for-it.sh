#!/usr/bin/env bash

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 host [port] command..."
  exit 1
fi

host="$1"
shift

if [ $# -gt 0 ] && [[ "$1" =~ ^[0-9]+$ ]]; then
  port="$1"
  shift
else
  port="${DB_PORT:-5432}"
fi

cmd=("$@")

until pg_isready -h "$host" -p "$port" > /dev/null 2>&1; do
  >&2 echo "🔄 Esperando a que PostgreSQL esté listo en $host:$port..."
  sleep 2
done

>&2 echo "✅ PostgreSQL está listo. Ejecutando comando: ${cmd[*]}"
exec "${cmd[@]}"
