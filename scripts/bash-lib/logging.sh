#!/usr/bin/env bash
# Structured JSON logging for bash scripts
#
# Usage:
#   source "$(dirname "$0")/lib/logging.sh"
#   log_info "deployment_started" "commit" "$SHA" "branch" "main"
#   log_error "deployment_failed" "step" "docker_build" "exit_code" "1"
#
# Output:
#   {"timestamp":"2026-01-20T21:40:10Z","level":"info","event":"deployment_started","commit":"abc123","branch":"main"}

# Escape special JSON characters in a string
_json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

# Core JSON logging function
# Args: level event [key value ...]
log_json() {
    local level="$1"
    local event="$2"
    shift 2
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Build JSON with optional key-value pairs
    local json="{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"event\":\"$(_json_escape "$event")\""

    while [[ $# -ge 2 ]]; do
        local key="$1"
        local value="$2"
        json+=",\"$(_json_escape "$key")\":\"$(_json_escape "$value")\""
        shift 2
    done
    json+="}"

    echo "$json"
}

# Convenience functions for each log level
log_debug() { log_json "debug" "$@"; }
log_info()  { log_json "info"  "$@"; }
log_warn()  { log_json "warn"  "$@"; }
log_error() { log_json "error" "$@"; }

# Send Slack notification with rich formatting
# Args: status message [context]
# status: "success" or "failure"
# message: Main message content (supports Slack mrkdwn)
# context: Optional additional context (supports Slack mrkdwn)
notify_slack() {
    local status="$1"
    local message="$2"
    local context="${3:-}"

    # SLACK_WEBHOOK_URL should be set by the calling script (from AWS SSM)
    if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
        return 0
    fi

    local color icon title
    if [[ "$status" == "success" ]]; then
        color="good"
        icon="✅"
        title="ichrisbirch deployment succeeded"
    else
        color="danger"
        icon="🔴"
        title="ichrisbirch deployment failed"
    fi

    # Escape special characters for JSON
    message="${message//\\/\\\\}"
    message="${message//\"/\\\"}"
    context="${context//\\/\\\\}"
    context="${context//\"/\\\"}"

    # Build payload - use attachments for colored sidebar
    local payload
    payload="{\"attachments\":[{\"color\":\"$color\",\"blocks\":["
    payload+="{\"type\":\"header\",\"text\":{\"type\":\"plain_text\",\"text\":\"$icon $title\",\"emoji\":true}},"
    payload+="{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"$message\"}}"

    # Add context block if provided
    if [[ -n "$context" ]]; then
        payload+=",{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"$context\"}}"
    fi

    payload+="]}]}"

    curl -s -X POST "$SLACK_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1 || true
}

# Fetch Slack webhook URL from AWS SSM Parameter Store
# Returns 0 on success, 1 on failure
fetch_slack_webhook_from_ssm() {
    local param_name="${1:-/ichrisbirch/production/slack/webhook_url}"

    if ! command -v aws &>/dev/null; then
        log_warn "aws_cli_not_found" "message" "Cannot fetch Slack webhook URL"
        return 1
    fi

    local webhook_url
    webhook_url=$(aws ssm get-parameter \
        --name "$param_name" \
        --with-decryption \
        --query 'Parameter.Value' \
        --output text \
        --region us-east-2 2>/dev/null) || return 1

    if [[ -n "$webhook_url" && "$webhook_url" != "None" ]]; then
        export SLACK_WEBHOOK_URL="$webhook_url"
        return 0
    fi
    return 1
}
