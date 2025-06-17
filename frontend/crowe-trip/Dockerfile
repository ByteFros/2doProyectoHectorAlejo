# Build stage
FROM node:20-slim AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:20-slim
WORKDIR /app

# Copiar archivos de configuración e instalar dependencias de producción
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# Copiar archivos construidos
COPY --from=builder /app/build ./build
COPY --from=builder /app/public ./public

EXPOSE 5173
ENV NODE_ENV=production
ENV PORT=5173
ENV HOST=0.0.0.0

# Usar el script definido en package.json
CMD ["npm", "start"]
