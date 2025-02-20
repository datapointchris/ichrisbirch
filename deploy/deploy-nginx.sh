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
SITES_AVAILABLE="$NGINX_HOME/sites-available"
SITES_ENABLED="$NGINX_HOME/sites-enabled"

CONFIG_FILES=("api.conf" "app.conf" "chat.conf")

make_directories() {
    sudo mkdir -vp $SITES_AVAILABLE
    sudo mkdir -vp $SITES_ENABLED
}

copy_configuration_files() {
    sudo cp -v "$NGINX_SOURCE/nginx.conf" "$NGINX_HOME/nginx.conf"
    for config_file in "${CONFIG_FILES[@]}"; do
        sudo cp -v "$NGINX_SOURCE/$config_file" "$SITES_AVAILABLE/$PROJECT_NAME-$config_file"
    done
}

symlink_from_sites_available_to_sites_enabled() {
    for config_file in "${CONFIG_FILES[@]}"; do
        sudo ln -sfv "$SITES_AVAILABLE/$PROJECT_NAME-$config_file" "$SITES_ENABLED/$PROJECT_NAME-$config_file"
    done
}

set_macos_permissions() {
    echo "Updating MacOS owner permissions to: $USER"
    sudo chown -vR "$USER" $NGINX_HOME
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
    echo "$SITES_AVAILABLE"
    echo "$SITES_ENABLED"

    echo "::::: Copy Config Files :::::"
    {
        echo "$PROJECT_NAME/deploy/$NGINX_SOURCE/nginx.conf => $NGINX_HOME/nginx.conf"
        for config_file in "${CONFIG_FILES[@]}"; do
            echo "$PROJECT_NAME/deploy/$NGINX_SOURCE/$config_file => $SITES_AVAILABLE/$PROJECT_NAME-$config_file"
        done
    } | column -t
    echo

    echo "::::: Symlink Config Files :::::"
    {
        for config_file in "${CONFIG_FILES[@]}"; do
            echo "symlink: $SITES_AVAILABLE/$PROJECT_NAME-$config_file => $SITES_ENABLED/$PROJECT_NAME-$config_file"
        done
    } | column -t

    if [[ $MACOS ]]; then
        echo "Update MacOS owner permissions for: $REDIS_HOME to: $USER"
    fi
    echo
}

# -- Check for arguments -- #
# NOTE: No exit codes inside the functions so they can be more generic

if [[ "$1" = "--dry-run" ]]; then
    dry_run
    exit 0
fi

echo "Deploying NGINX Config Files to $ENVIRONMENT"
make_directories
echo
copy_configuration_files
echo
symlink_from_sites_available_to_sites_enabled
echo

if [[ $MACOS ]]; then
    set_macos_permissions
fi

echo restarting nginx
sudo nginx -s reload
