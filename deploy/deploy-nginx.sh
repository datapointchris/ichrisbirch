#!/usr/bin/env bash

# Deploy nginx Config Files to [environment]

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
NGINX_SOURCE="$ENVIRONMENT/nginx"

# Config Locations
ETC_DIR="$OS_PREFIX/etc"

NGINX_HOME="$ETC_DIR/nginx"
NGINX_SITES_AVAILABLE="$NGINX_HOME/sites-available"
NGINX_SITES_ENABLED="$NGINX_HOME/sites-enabled"

dry_run() {
    if [[ $MACOS ]]; then
        echo "macos detected: /usr/local prefix will be used"
    fi
    echo script actions:
    {
    echo "copy: ./$NGINX_SOURCE/nginx.conf => $NGINX_HOME/nginx.conf"
    echo "copy: ./$NGINX_SOURCE/api.conf => $NGINX_SITES_AVAILABLE/$PROJECT_NAME-api.conf"
    echo "copy: ./$NGINX_SOURCE/app.conf => $NGINX_SITES_AVAILABLE/$PROJECT_NAME-app.conf"
    echo "symlink: $NGINX_SITES_AVAILABLE/$PROJECT_NAME-api.conf => $NGINX_SITES_ENABLED/$PROJECT_NAME-api.conf"
    echo "symlink: $NGINX_SITES_AVAILABLE/$PROJECT_NAME-app.conf => $NGINX_SITES_ENABLED/$PROJECT_NAME-app.conf"
    } | column -t

}

# -- Check for arguments -- #
# NOTE: No exit codes inside the functions so they can be more generic

if [[ "$1" = "--dry-run" ]]; then
    dry_run
    exit 0;
fi

echo "Deploying NGINX Config Files to $ENVIRONMENT"

# Directories
sudo mkdir -vp $NGINX_SITES_AVAILABLE
sudo mkdir -vp $NGINX_SITES_ENABLED

# Configuration
sudo cp -v "$NGINX_SOURCE/nginx.conf" "$NGINX_HOME/nginx.conf"
sudo cp -v "$NGINX_SOURCE/api.conf" "$NGINX_SITES_AVAILABLE/$PROJECT_NAME-api.conf"
sudo cp -v "$NGINX_SOURCE/app.conf" "$NGINX_SITES_AVAILABLE/$PROJECT_NAME-app.conf"

# Symlink from sites-available to sites-enabled
sudo ln -sfv "$NGINX_SITES_AVAILABLE/$PROJECT_NAME-api.conf" "$NGINX_SITES_ENABLED/$PROJECT_NAME-api.conf"
sudo ln -sfv "$NGINX_SITES_AVAILABLE/$PROJECT_NAME-app.conf" "$NGINX_SITES_ENABLED/$PROJECT_NAME-app.conf"
echo


# ---------- Set owner on MacOS in dev ---------- #
if [[ $MACOS ]]; then
    echo "Updating MacOS owner permissions to: $USER"
    sudo chown -vR "$USER" $NGINX_HOME
    echo
fi

echo restarting nginx
sudo nginx -s reload
