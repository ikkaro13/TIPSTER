FROM node:20-alpine AS builder

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm install

# Copiar el código y compilar (build)
COPY . .
RUN npm run build

# Imagen de producción ligera
FROM node:20-alpine AS runner

WORKDIR /app

# Copiar los assets de NextJS y módulos node
COPY --from=builder /app/package.json .
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Exponer el puerto de frontend
EXPOSE 3000

# Arrancar la aplicación
CMD ["npm", "start"]
