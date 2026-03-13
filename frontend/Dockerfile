# Build stage
# Build context must be repo root (shared SCSS lives in ichrisbirch/app/static/sass/)
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Copy shared SCSS files that Vite loadPaths references
COPY ichrisbirch/app/static/sass/ /ichrisbirch/app/static/sass/
COPY ichrisbirch/app/static/css/ /ichrisbirch/app/static/css/

# Build arg for API URL (set in docker-compose per environment)
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Production stage — Caddy serves static files with SPA routing
FROM caddy:2-alpine

COPY --from=builder /app/dist /srv
COPY frontend/Caddyfile /etc/caddy/Caddyfile

EXPOSE 80
