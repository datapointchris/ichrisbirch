#!/usr/bin/env bash
set -e # fail script on command fail

######################################################################
# Postgres Snapshot Backup to S3
######################################################################
# TODO: [2023/01/02] - Run this thing with airflow
# TODO: [2023/01/02] - Move the loading of the Environment to an environment helper script

# -------------------- Instructions -------------------- #
# TODO: [2023/01/02] - These instructions are outdated!!
# Make sure to:
# 1) Name this file `backup.sh` and place it in /home/ubuntu
# 2) Run sudo apt install awscli to install the AWSCLI
# -> aws-cli should get permissions from EC2 instance
# 3) Create S3 bucket for the backups and fill it in below (set a lifecycle rule to expire files older than X days in the bucket)
# 4) Run chmod +x backup.sh
# 5) Set up a daily backup at midnight via `crontab -e`:
#    0 0 * * * /home/ubuntu/backup.sh > /home/ubuntu/backup.log

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")

# ---------- Imports ---------- #
source "$SCRIPT_DIR/environment"

source "$SCRIPT_DIR/bash-helpers"
# bash-helpers.filename_to_title
# bash-helpers.print_title
# bash-helpers.print_section
# bash-helpers.color_blue
# bash-helpers.color_green
# bash-helpers.color_yellow
# bash-helpers.color_red


SCRIPT_TITLE="$(filename_to_title "$SCRIPT_NAME")"


usage() {
    local message
    message=$(
        cat <<-EOF

$(color_green "$(print_section "Usage:")")
$(color_blue "Script runs without arguments:")
./$SCRIPT_NAME

$(color_blue "Help:")
./$SCRIPT_NAME --help

$(color_blue "Dry Run:")
./$SCRIPT_NAME --dry-run
EOF
    )
    echo "$message"
}

help() {
    local message
    message=$(
        cat <<-EOF

$(print_title "$SCRIPT_TITLE")

$(color_green "$(print_section "Description")")
This script creates a snapshot of an RDS Postgres instance
and exports it to an S3 bucket, then deletes the snapshot from RDS.

$(usage)

$(color_green "$(print_section "Requirements:")")
1. $(color_blue "awscli") installed
2. Script executor to have the following permissions:
  1. RDS create-db-snapshot
  2. RDS start-export-task
  3. RDS delete-db-snapshot
Locally: user or IAM ccolor_redentials must have these permissions
EC2: the instance *should* have the necessary permissions through a security group
Airflow... ¯\_(ツ)_/¯
EOF
    )
    echo "$message"
}

# if [[ -z "$1" ]]; then
#     usage
#     exit 0

# else
if [[ -n "$1" ]]; then
    case "$1" in
    "--help")
        help
        exit 0
        ;;
    "--dry-run")
        DRY_RUN=true
        echo
        print_title "$(color_blue "Executing Dry Run of $SCRIPT_TITLE")"
        ;;
    *)
        color_red "Unrecognized argument: $1"

        usage
        exit 1
        ;;
    esac
fi

elapsed_time() { echo "$((SECONDS / 60)) minutes $((SECONDS % 60)) seconds"; }

logger () {
    local level="$1"
    local message="$2"
    echo "[${level^^}] $message"
}

# ----- Constants ----- #
SECONDS=0
BUCKET_PREFIX="postgres"
TIMESTAMP="$(date -u +%Y-%m-%dT%HH%MM)"
SNAPSHOT_NAME="$POSTGRES_DBNAME-$TIMESTAMP-snapshot"
FULL_BUCKET_PATH="s3://$S3_BACKUPS_BUCKET/$BUCKET_PREFIX/$SNAPSHOT_NAME"
LOG_FILE="$SCRIPT_NAME.log"

if [[ -n $DEBUG ]]; then
    logger debug "Env File Loaded: $ENV_PATH"
    logger debug "OS Prefix: $OS_PREFIX"
    logger debug "Database: postgresql://$POSTGRES_URI/$POSTGRES_DBNAME"
    logger debug "Bucket: $FULL_BUCKET_PATH"
    logger debug "Log Location: $LOG_FILE"
fi

# ----- Main Functions ----- #

create_rds_snapshot() {
    aws rds create-db-snapshot \
        --db-instance-identifier "$POSTGRES_DBNAME" \
        --db-snapshot-identifier "$SNAPSHOT_NAME" \
        --output text >>"$LOG_FILE" 2>&1

    aws rds wait db-snapshot-completed \
        --db-instance-identifier "$POSTGRES_DBNAME" \
        --db-snapshot-identifier "$SNAPSHOT_NAME" \
        --output text >>"$LOG_FILE" 2>&1
}

export_rds_snapshot_to_s3() {
    aws rds start-export-task \
        --export-task-identifier "$SNAPSHOT_NAME" \
        --source-arn arn:aws:rds:us-east-1:215933706506:snapshot:"$SNAPSHOT_NAME" \
        --s3-bucket-name "$S3_BACKUPS_BUCKET" \
        --s3-prefix "$BUCKET_PREFIX" \
        --iam-role-arn arn:aws:iam::215933706506:role/S3DatabaseBackups \
        --kms-key-id arn:aws:kms:us-east-1:215933706506:key/65e31888-e584-48df-84d1-5f0cc2f1f28b \
        --output text >>"$LOG_FILE" 2>&1

    export_status=""
    while [ "$export_status" != "COMPLETE" ]; do
        sleep 15
        export_status=$(aws rds describe-export-tasks \
            --source-arn arn:aws:rds:us-east-1:215933706506:snapshot:"$SNAPSHOT_NAME" \
            --query "ExportTasks[*].[Status]" \
            --output text)
    done
}

delete_rds_snapshot() {
    aws rds delete-db-snapshot \
        --db-snapshot-identifier "$SNAPSHOT_NAME" \
        --output text >>"$LOG_FILE" 2>&1

    aws rds wait db-snapshot-deleted \
        --db-instance-identifier "$POSTGRES_DBNAME" \
        --db-snapshot-identifier "$SNAPSHOT_NAME" \
        --output text >>"$LOG_FILE" 2>&1
}

# ----- Main Script ----- #
logger info "$(color_green "Running:") $(color_blue "$SCRIPT_TITLE")"

logger info "$(color_yellow "Creating $SNAPSHOT_NAME")"
if [[ -z $DRY_RUN ]]; then create_rds_snapshot; fi
logger info "$(color_green "Created $SNAPSHOT_NAME")"

logger info "$(color_yellow "Exporting $SNAPSHOT_NAME")"
if [[ -z $DRY_RUN ]]; then export_rds_snapshot_to_s3; fi
logger info "$(color_green "Exported $SNAPSHOT_NAME")"

logger info "$(color_yellow "Deleting $SNAPSHOT_NAME")"
if [[ -z $DRY_RUN ]]; then delete_rds_snapshot; fi
logger info "$(color_red "Deleted $SNAPSHOT_NAME")"

logger info "$(color_green "Completed:") $(color_blue "$SCRIPT_TITLE-- $(elapsed_time)")"