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
REDIS_HOME="$OS_PREFIX/var/lib/redis"
REDIS_LOG="$OS_PREFIX/var/log/redis"

make_directories() {
    sudo mkdir -vp $REDIS_HOME
    sudo mkdir -vp $REDIS_LOG
}

copy_configuration_files() {
    sudo cp -v "$REDIS_SOURCE/redis.conf" "$REDIS_HOME/redis.conf"

}

set_macos_permissions() {
    echo "Updating MacOS owner permissions to: $USER"
    sudo chown redis:redis $REDIS_HOME
    sudo chown redis:redis $REDIS_LOG
    sudo chmod 750 $REDIS_HOME
    sudo chown redis:redis $REDIS_LOG
    echo
}

dry_run() {
    if [[ $MACOS ]]; then
        echo "=====> MacOS Detected: /usr/local/ prefix will be used <====="
        echo
    fi
    echo "::::: Script Actions :::::"
    echo

    echo "::::: Create Directories :::::"
    echo "$REDIS_HOME"
    echo "$REDIS_LOG"

    echo "::::: Copy Configuration Files :::::"
    echo "$PROJECT_NAME/deploy/$REDIS_SOURCE/nginx.conf => $REDIS_HOME/nginx.conf"

    if [[ $MACOS ]]; then
        echo "Update MacOS owner permissions for: $REDIS_HOME to: $USER"
    fi
    echo
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
    set_macos_permissions
fi
