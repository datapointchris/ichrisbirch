#!/bin/bash

PG_VERSION=16
PG_PORT=5455
CONTAINER_NAME="postgres-$PG_VERSION-$PG_PORT-$(date +%H-%M)"

echo ""
echo "Stopping and removing all running docker containers"
# shellcheck disable=SC2046
docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)
sleep 2

echo ""
echo "Starting PostgreSQL version $PG_VERSION on port $PG_PORT"
docker run --name "$CONTAINER_NAME" \
    -e POSTGRES_PASSWORD=postgres \
    -d \
    -p "$PG_PORT":5432 \
    -v "${CONTAINER_NAME}_data:/var/lib/postgresql/data" \
    postgres:"$PG_VERSION"
sleep 2

echo ""
echo "Running Postgres Backup and Restore Test"
python ../ichrisbirch/scheduler/postgres_backup_restore.py
