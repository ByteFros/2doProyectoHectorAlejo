# Usa una imagen de Python
FROM python:3.10

# Configura el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de requerimientos
COPY requirements.txt requirements.txt

# Instala dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia todo el código (incluido el script de espera)
COPY . .

# Da permisos de ejecución al script
RUN chmod +x /app/wait-for-it.sh

# Expone el puerto 8000
EXPOSE 8000

# Usa wait-for-it para esperar que el contenedor de PostgreSQL esté listo
CMD ["sh", "-c", "./wait-for-it.sh db python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
