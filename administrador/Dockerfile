# Usa una imagen ligera de Python
FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Configura el directorio de trabajo en el contenedor
WORKDIR /app

# Paquetes del sistema necesarios para compilar dependencias como psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        libpq-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependencias
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia el resto del código al contenedor
COPY . .

# Normaliza finales de línea y permisos de scripts
RUN sed -i 's/\r$//' /app/wait-for-it.sh /app/entrypoint.sh \
    && chmod +x /app/wait-for-it.sh /app/entrypoint.sh

ENV DJANGO_ENV=production \
    PORT=8000

# Expone el puerto 8000
EXPOSE 8000

# Punto de entrada
ENTRYPOINT ["./entrypoint.sh"]
