# ====================================
# DOCKERFILE FRONTEND - MULTI-STAGE
# ====================================

# Etapa 1: Build de desarrollo
FROM node:20-slim as development

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración
COPY package.json package-lock.json* ./

# Instalar dependencias
RUN npm ci

# Copiar el resto del código
COPY . .

# Exponer puerto 5173 para desarrollo
EXPOSE 5173

# Comando para desarrollo
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ====================================
# Etapa 2: Build de producción
FROM node:20-slim as builder

WORKDIR /app

# Copiar archivos de configuración
COPY package.json package-lock.json* ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar código fuente
COPY . .

# Variables de entorno para build
ARG VITE_API_BASE_URL=http://127.0.0.1:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV NODE_ENV=production

# Build de la aplicación
RUN npm run build

# ====================================
# Etapa 3: Servidor de producción
FROM nginx:alpine as production

# Copiar archivos compilados
COPY --from=builder /app/build /usr/share/nginx/html

# Configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# ====================================
# Por defecto usa development
FROM development
