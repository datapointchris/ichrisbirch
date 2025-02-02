#!/usr/bin/env bash

# Deploy Supervisor Config Files to [environment]

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
SUPERVISOR_SOURCE="$ENVIRONMENT/supervisor"

# Config Locations
ETC_DIR="$OS_PREFIX/etc"

SUPERVISOR_HOME="$ETC_DIR/supervisor"
SUPERVISOR_CONFIG_TARGET="$SUPERVISOR_HOME/conf.d"
SUPERVISOR_LOG_TARGET="$OS_PREFIX/var/log/supervisor"

CONFIG_FILES=("api.conf" "app.conf" "chat.conf" "scheduler.conf")
LOG_FILES=("supervisord.log" "$PROJECT_NAME-api.log" "$PROJECT_NAME-app.log" "$PROJECT_NAME-chat.log" "$PROJECT_NAME-scheduler.log")

make_directories() {
    sudo mkdir -vp $SUPERVISOR_HOME
    sudo mkdir -vp $SUPERVISOR_CONFIG_TARGET
    sudo mkdir -vp $SUPERVISOR_LOG_TARGET
}

check_supervisor_updated() {
    if [[ ! -f "$ETC_DIR/supervisord.conf" ]] || ! diff -q "$SUPERVISOR_SOURCE/supervisord.conf" "$ETC_DIR/supervisord.conf" &>/dev/null; then
        sudo cp -v "$SUPERVISOR_SOURCE/supervisord.conf" "$ETC_DIR/supervisord.conf"
        SUPERVISORD_UPDATED=1
    fi
}

copy_config_files() {
    for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
        SOURCE="$SUPERVISOR_SOURCE/$CONFIG_FILE"
        TARGET="$SUPERVISOR_CONFIG_TARGET/$PROJECT_NAME-$CONFIG_FILE"
        if [[ ! -f "$TARGET" ]] || ! diff -q "$SOURCE" "$TARGET" &>/dev/null; then
            sudo cp -v "$SOURCE" "$TARGET"
        fi
    done
}

create_log_files() {
    for LOG_FILE in "${LOG_FILES[@]}"; do
        TARGET="$SUPERVISOR_LOG_TARGET/$LOG_FILE"
        if [[ -f "$TARGET" ]]; then
            echo "log file exists: $TARGET"
        else
            sudo touch "$TARGET"
            echo created log file: "$TARGET"
        fi
    done
}

set_macos_permissions() {
    echo "updating macos owner permissions to: $USER"
    sudo chown -vR "$USER" $SUPERVISOR_HOME
    sudo chown -vR "$USER" $SUPERVISOR_LOG_TARGET
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
    echo "$SUPERVISOR_HOME"
    echo "$SUPERVISOR_CONFIG_TARGET"
    echo "$SUPERVISOR_LOG_TARGET"
    echo

    echo "::::: Copy Config Files :::::"
    {
        echo "$PROJECT_NAME/deploy/$SUPERVISOR_SOURCE/supervisord.conf => $ETC_DIR/supervisord.conf"

        for config_file in "${CONFIG_FILES[@]}"; do
            echo "$PROJECT_NAME/deploy/$SUPERVISOR_SOURCE/$config_file => $SUPERVISOR_CONFIG_TARGET/$PROJECT_NAME-$config_file"
        done
    } | column -t
    echo

    echo "::::: Create Log Files :::::"
    for log_file in "${LOG_FILES[@]}"; do
        echo "$SUPERVISOR_LOG_TARGET/$log_file"
    done
}

# -- Check for arguments -- #
# NOTE: No exit codes inside usage or help so they can be called without exiting

if [[ "$1" = "--dry-run" ]]; then
    dry_run
    exit 0
fi

if [[ $MACOS ]]; then
    echo "=====> MacOS Detected: /usr/local/ prefix will be used <====="
    echo
fi

# Note: Make sure log direcitories match entries in `supervisord.conf`
echo "deploying supervisor config files to $ENVIRONMENT"
make_directories
echo
check_supervisor_updated
echo
copy_config_files
echo
create_log_files
echo

if [[ $MACOS ]]; then
    set_macos_permissions
fi

if [[ $SUPERVISORD_UPDATED ]]; then
    echo restarting supervisor
    sudo supervisorctl reload
else
    echo restarting supervisor processes
    sudo supervisorctl reread
    sudo supervisorctl update
fi

echo supervisor status:
sudo supervisorctl status
