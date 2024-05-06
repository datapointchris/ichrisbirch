#!/bin/bash

read -rp "Enter the PostgreSQL version you want to use (e.g., 14, 13): " PG_VERSION


read -rp "Enter the port you want to map to the PostgreSQL container (e.g., 5433): " PG_PORT

CONTAINER_NAME="postgres-$PG_VERSION-$PG_PORT-$(date +%H-%M)"

docker run --name "$CONTAINER_NAME" \
-e POSTGRES_PASSWORD=thepassword \
-d \
-p "$PG_PORT":5432 \
-v "${CONTAINER_NAME}_data:/var/lib/postgresql/data" \
postgres:"$PG_VERSION"

echo "PostgreSQL version $PG_VERSION running on port ""$PG_PORT"
