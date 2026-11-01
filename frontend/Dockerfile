# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Build arg for API URL (set in docker-compose per environment)
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Production stage — Caddy serves static files with SPA routing
FROM caddy:2-alpine

# The app image's account, so neither image runs as root or as a person. The
# image's caddy binary carries cap_net_bind_service, so it still binds :80.
RUN addgroup -S -g 10300 ichrisbirch \
 && adduser -S -D -H -u 10300 -G ichrisbirch -s /sbin/nologin ichrisbirch \
 && chown -R ichrisbirch:ichrisbirch /data /config

COPY --from=builder /app/dist /srv
COPY frontend/Caddyfile /etc/caddy/Caddyfile

USER 10300:10300
EXPOSE 80
