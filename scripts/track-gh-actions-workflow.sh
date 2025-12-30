#!/bin/bash

# Track the most recent "Validate Project" workflow run
# Usage: ./scripts/track-workflow.sh [watch]

set -e

WORKFLOW_NAME="Validate Project"

# Function to get the most recent workflow run
get_latest_run() {
    gh run list --workflow="$WORKFLOW_NAME" --limit=1 --json databaseId,status,conclusion,url,headBranch,createdAt --jq '.[0]'
}

# Function to display run info
display_run_info() {
    local run_info="$1"
    local run_id=$(echo "$run_info" | jq -r '.databaseId')
    local status=$(echo "$run_info" | jq -r '.status')
    local conclusion=$(echo "$run_info" | jq -r '.conclusion // "pending"')
    local branch=$(echo "$run_info" | jq -r '.headBranch')
    local created_at=$(echo "$run_info" | jq -r '.createdAt')
    local url=$(echo "$run_info" | jq -r '.url')

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Latest Validate Project Run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Run ID: $run_id"
    echo "Branch: $branch"
    echo "Created: $created_at"
    echo "Status: $status"
    echo "Conclusion: $conclusion"
    echo "URL: $url"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to show logs
show_logs() {
    local run_id="$1"
    echo ""
    echo "Fetching failed job logs for run $run_id..."
    echo ""

    # Get only failed job logs
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Failed Job Logs Only"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Disable pager for gh CLI output
    env PAGER=cat gh run view "$run_id" --log-failed

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "For all logs use: PAGER=cat gh run view $run_id --log"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to watch run status
watch_run() {
    local run_id="$1"
    echo ""
    echo "Watching run $run_id (press Ctrl+C to stop)..."
    echo ""

    while true; do
        local current_info=$(gh run list --workflow="$WORKFLOW_NAME" --limit=1 --json databaseId,status,conclusion --jq '.[0]')
        local current_id=$(echo "$current_info" | jq -r '.databaseId')
        local current_status=$(echo "$current_info" | jq -r '.status')
        local current_conclusion=$(echo "$current_info" | jq -r '.conclusion // "pending"')

        # Check if we're still watching the same run
        if [ "$current_id" != "$run_id" ]; then
            echo "New run detected: $current_id"
            run_id="$current_id"
        fi

        printf "\rStatus: %-15s | Conclusion: %-15s | Run: %s" "$current_status" "$current_conclusion" "$run_id"

        # If run is complete, break
        if [ "$current_status" = "completed" ]; then
            echo ""
            echo ""
            if [ "$current_conclusion" = "success" ]; then
                echo "Run completed successfully!"
            else
                echo "Run failed with conclusion: $current_conclusion"
                echo ""
                echo "Showing failure logs..."
                show_logs "$run_id"
            fi
            break
        fi

        sleep 5
    done
}

# Main execution
main() {
    echo "Fetching latest 'Validate Project' workflow run..."
    echo ""

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        echo "GitHub CLI (gh) is not installed. Please install it first:"
        echo "   brew install gh"
        exit 1
    fi

    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        echo "Not authenticated with GitHub CLI. Please run:"
        echo "   gh auth login"
        exit 1
    fi

    local run_info=$(get_latest_run)

    if [ "$run_info" = "null" ] || [ -z "$run_info" ]; then
        echo "No workflow runs found for '$WORKFLOW_NAME'"
        exit 1
    fi

    # Extract run ID from the run info
    local run_id=$(echo "$run_info" | jq -r '.databaseId')

    # Handle different command options
    case "${1:-}" in
        "watch")
            display_run_info "$run_info"
            watch_run "$run_id"
            ;;
        "logs")
            # Check if a specific run ID was provided as second argument
            if [ -n "${2:-}" ]; then
                echo "Using specified run ID: $2"
                show_logs "$2"
            else
                display_run_info "$run_info"
                show_logs "$run_id"
            fi
            ;;
        "url")
            echo "$run_info" | jq -r '.url'
            ;;
        *)
            display_run_info "$run_info"
            echo ""
            echo "Available commands:"
            echo "   ./scripts/track-workflow.sh watch         # Watch run status in real-time"
            echo "   ./scripts/track-workflow.sh logs [run_id] # Show failed logs (optionally for specific run)"
            echo "   ./scripts/track-workflow.sh url           # Get URL of latest run"
            echo ""
            echo "Quick access: gh run view $run_id --log-failed"
            ;;
    esac
}

main "$@"
