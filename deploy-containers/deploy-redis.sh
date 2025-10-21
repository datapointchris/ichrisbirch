#!/usr/bin/env bash

# Deploy redis Config Files to [environment]

# Fail script on command fail
set -e

PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel)")

if [[ $(uname) == "Darwin" ]]; then
    MACOS=1
    OS_PREFIX="/usr/local"
    ENVIRONMENT="dev"
else
    OS_PREFIX=""
    ENVIRONMENT="prod"
fi

# Project File Locations
REDIS_SOURCE="$ENVIRONMENT/redis"

# Config Locations
REDIS_HOME="$OS_PREFIX/etc/redis"
REDIS_DATA="$OS_PREFIX/var/lib/redis"
REDIS_LOG="$OS_PREFIX/var/log/redis"

make_directories() {
    sudo mkdir -vp $REDIS_DATA
    sudo mkdir -vp $REDIS_LOG
    sudo touch $REDIS_LOG/redis.log
    sudo chown -vR "$USER" $REDIS_LOG
    sudo chmod -v 755 $REDIS_LOG
}

copy_configuration_files() {
    if [[ $MACOS ]]; then
        sudo cp -v "$REDIS_SOURCE/redis.conf" "$OS_PREFIX/etc/redis.conf"
    else
        sudo cp -v "$REDIS_SOURCE/redis.conf" "$REDIS_HOME/redis.conf"
        sudo cp -v "$REDIS_SOURCE/redis_init_script" "/etc/init.d/redis"
    fi

}

dry_run() {
    if [[ $MACOS ]]; then
        echo "=====> MacOS Detected: **Conditions Apply** <====="
        echo
        echo "::::: Copy Configuration Files :::::"
        echo "$PROJECT_NAME/deploy/$REDIS_SOURCE/redis.conf => $REDIS_HOME/redis.conf"
    else
        echo "::::: Script Actions :::::"
        echo

        echo "::::: Create Directories :::::"
        echo "$REDIS_HOME"
        echo "$REDIS_DATA"
        echo "$REDIS_LOG"

        echo "::::: Copy Configuration Files :::::"
        echo "$PROJECT_NAME/deploy/$REDIS_SOURCE/redis.conf => $REDIS_HOME/redis.conf"
        echo "$REDIS_SOURCE/redis_init_script ==> /etc/init.d/redis (Linux Only)"
    fi
}

if [[ "$1" = "--dry-run" ]]; then
    dry_run
    exit 0
fi

echo "Deploying Redis Configuration Files to $ENVIRONMENT"


make_directories
echo
copy_configuration_files
echo
if [[ $MACOS ]]; then
    echo "Starting or Restarting Redis Service"
    brew services restart redis
else
    echo "Starting or Restarting Redis Service"
    sudo /etc/init.d/redis stop
    sudo /etc/init.d/redis start
fi
