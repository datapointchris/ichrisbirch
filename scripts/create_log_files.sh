#!/bin/bash

LOG_DIR="/var/log/ichrisbirch"
sudo mkdir "$LOG_DIR"
sudo chown ubuntu "$LOG_DIR"
touch "$LOG_DIR/ichrisbirch.log"
touch "$LOG_DIR/app.log"
touch "$LOG_DIR/api.log"
touch "$LOG_DIR/chat.log"
touch "$LOG_DIR/scheduler.log"
touch "$LOG_DIR/ichrisbirch.json"
