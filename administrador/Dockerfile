# Usa una imagen de Python
FROM python:3.10

# Configurar el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos del backend
COPY . /app/

# Instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exponer el puerto 8000 para Django
EXPOSE 8000

# Comando por defecto para ejecutar migraciones y luego el servidor
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]