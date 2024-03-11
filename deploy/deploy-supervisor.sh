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

dry_run() {
    if [[ $MACOS ]]; then
        echo "MacOS detected: /usr/local prefix will be used"
    fi
    echo Script Actions:
    {
    echo "copy: ./$SUPERVISOR_SOURCE/supervisord.conf => $ETC_DIR/supervisord.conf"
    echo "copy: ./$SUPERVISOR_SOURCE/api.conf => $SUPERVISOR_CONFIG_TARGET/$PROJECT_NAME-api.conf"
    echo "copy: ./$SUPERVISOR_SOURCE/app.conf => $SUPERVISOR_CONFIG_TARGET/$PROJECT_NAME-app.conf"
    echo "copy: ./$SUPERVISOR_SOURCE/scheduler.conf => $SUPERVISOR_CONFIG_TARGET/$PROJECT_NAME-scheduler.conf"
    } | column -t
    echo "create: $SUPERVISOR_LOG_TARGET/supervisord.log"
    echo "create: $SUPERVISOR_LOG_TARGET/$PROJECT_NAME-api.log"
    echo "create: $SUPERVISOR_LOG_TARGET/$PROJECT_NAME-app.log"
    echo "create: $SUPERVISOR_LOG_TARGET/$PROJECT_NAME-scheduler.log"
}

# -- Check for arguments -- #
# NOTE: No exit codes inside usage or help so they can be called without exiting

if [[ "$1" = "--dry-run" ]]; then
    dry_run
    exit 0;
fi

echo "Deploying Supervisor Config Files to $ENVIRONMENT"
# Note: Make sure log direcitories match entries in `supervisord.conf`

sudo mkdir -vp $SUPERVISOR_HOME
sudo mkdir -vp $SUPERVISOR_CONFIG_TARGET
sudo mkdir -vp $SUPERVISOR_LOG_TARGET

if [[ ! -f "$ETC_DIR/supervisord.conf" ]] || ! diff -q "$SUPERVISOR_SOURCE/supervisord.conf" "$ETC_DIR/supervisord.conf" &>/dev/null; then
    sudo cp -v "$SUPERVISOR_SOURCE/supervisord.conf" "$ETC_DIR/supervisord.conf"
    SUPERVISORD_UPDATED=1
fi

CONFIG_FILES=("app.conf" "api.conf" "scheduler.conf")
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
    SOURCE="$SUPERVISOR_SOURCE/$CONFIG_FILE"
    TARGET="$SUPERVISOR_CONFIG_TARGET/$PROJECT_NAME-$CONFIG_FILE"
    if [[ ! -f "$TARGET" ]] || ! diff -q "$SOURCE" "$TARGET" &>/dev/null; then
        sudo cp -v "$SOURCE" "$TARGET"
    fi
done
echo

LOG_FILES=("supervisord.log" "$PROJECT_NAME-app.log" "$PROJECT_NAME-api.log" "$PROJECT_NAME-scheduler.log")
for LOG_FILE in "${LOG_FILES[@]}"; do
    TARGET="$SUPERVISOR_LOG_TARGET/$LOG_FILE"
    if [[ -f "$TARGET" ]]; then
        echo "log file exists: $TARGET"
    else
        sudo touch "$TARGET"
        echo created log file: "$TARGET"
    fi
done
echo

# Set owner on MacOS in dev
if [[ $MACOS ]]; then
    echo "Updating MacOS owner permissions to: $USER"
    sudo chown -vR "$USER" $SUPERVISOR_HOME
    sudo chown -vR "$USER" $SUPERVISOR_LOG_TARGET
    echo
fi

if [[ $SUPERVISORD_UPDATED ]]; then
    echo restarting supervisor
    sudo supervisorctl reload
else
    echo restarting supervisor processes
    sudo supervisorctl reread
    sudo supervisorctl update
fi

echo Supervisor Status:
sudo supervisorctl status
