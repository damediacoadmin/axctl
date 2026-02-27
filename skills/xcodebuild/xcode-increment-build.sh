#!/bin/bash
#
# xcode-increment-build.sh - Auto-increment build number in Info.plist
# Reads current CFBundleVersion, increments by 1, and optionally commits to git
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Check for valid Pro license
check_license

# =============================================================================
# USAGE
# =============================================================================

usage() {
    cat <<EOF
Usage: $(basename "$0") <project_path> [--commit]

Increment the build number (CFBundleVersion) in an Xcode project's Info.plist.

Arguments:
  project_path     Path to .xcodeproj, .xcworkspace, or directory

Options:
  --commit         Commit the change to git (if in a git repository)
  -h, --help       Show this help message

Examples:
  $(basename "$0") ~/Projects/MyApp
  $(basename "$0") ~/Projects/MyApp --commit

Notes:
  - Searches for Info.plist in common locations
  - Backs up Info.plist before modification
  - If --commit is specified and git repo exists, creates a commit

EOF
    exit "${1:-0}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    local do_commit=0
    local project_path=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage 0
                ;;
            --commit)
                do_commit=1
                shift
                ;;
            -*)
                error_exit "Unknown option: $1"
                ;;
            *)
                if [[ -z "$project_path" ]]; then
                    project_path="$1"
                else
                    error_exit "Unexpected argument: $1"
                fi
                shift
                ;;
        esac
    done

    if [[ -z "$project_path" ]]; then
        usage 1
    fi

    # Initialize logging
    SCRIPT_NAME="increment-build" init_logging

    log "INFO" "=== Starting Build Number Increment ==="
    log "INFO" "Project path: $project_path"
    log "INFO" "Commit change: $do_commit"

    # Expand ~ to $HOME if present (safer than eval)
    project_path="${project_path/#\~/$HOME}"

    if [[ ! -e "$project_path" ]]; then
        error_exit "Project path does not exist: $project_path"
    fi

    # Find Info.plist
    local info_plist=""

    # Common locations to search
    local search_paths=()

    if [[ -d "$project_path" ]]; then
        search_paths+=("$project_path")
    fi

    # Try to find via xcodebuild
    log "INFO" "Searching for Info.plist..."

    # Method 1: Use xcodebuild to find it
    if [[ -d "$project_path" ]]; then
        # Get the project name from the xcodeproj if available
        local xcodeproj
        xcodeproj=$(find "$project_path" -maxdepth 2 -name "*.xcodeproj" -type d 2>/dev/null | head -n1)
        if [[ -n "$xcodeproj" ]]; then
            PROJECT_NAME=$(basename "$xcodeproj" .xcodeproj)
        else
            PROJECT_NAME=$(basename "$project_path")
        fi

        local find_cmd="find "$project_path" -maxdepth 4 -name "Info.plist" -type f 2>/dev/null"
        local plist_candidates
        local plist_candidates
        plist_candidates=$($find_cmd 2>/dev/null | grep -v Pods | grep -v "Pods/" || echo "")

        if [[ -n "$plist_candidates" ]]; then
            local count
            count=$(echo "$plist_candidates" | wc -l | tr -d ' ')
            log "INFO" "Found $count Info.plist candidates"

            # Try to find the main app Info.plist (not in Pods, not in Tests)
            info_plist=$(echo "$plist_candidates" | grep -E "(Sources|App|Main)" | head -n1 || echo "$plist_candidates" | head -n1)
        fi
    fi

    # Fallback: common default locations
    if [[ -z "$info_plist" ]] || [[ ! -f "$info_plist" ]]; then
        local defaults=(
            "$project_path/$PROJECT_NAME/Info.plist"
            "$project_path/Info.plist"
            "$project_path/App/Info.plist"
            "$project_path/Sources/Info.plist"
        )

        for plist in "${defaults[@]}"; do
            if [[ -f "$plist" ]]; then
                info_plist="$plist"
                break
            fi
        done
    fi

    if [[ -z "$info_plist" ]] || [[ ! -f "$info_plist" ]]; then
        error_exit "Could not find Info.plist in project. Please specify the full path."
    fi

    log "INFO" "Found Info.plist: $info_plist"

    # Read current build number
    log "INFO" "Reading current build number..."

    local current_build
    current_build=$(/usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$info_plist" 2>/dev/null || echo "")

    if [[ -z "$current_build" ]]; then
        # Try alternate key
        current_build=$(/usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$info_plist" 2>/dev/null || echo "")
    fi

    if [[ -z "$current_build" ]]; then
        error_exit "CFBundleVersion not found in Info.plist"
    fi

    log "INFO" "Current build number: $current_build"

    # Validate it's a number
    if ! [[ "$current_build" =~ ^[0-9]+$ ]]; then
        log "WARN" "Current build number is not a pure number: $current_build"
        log "INFO" "Attempting to extract numeric portion..."
        current_build=$(echo "$current_build" | grep -oE '^[0-9]+' || echo "1")
    fi

    # Increment build number
    local new_build=$((current_build + 1))

    log "INFO" "Incrementing to: $new_build"

    # Backup Info.plist
    local backup_path="${info_plist}.backup.$(date +%Y%m%d-%H%M%S)"
    cp "$info_plist" "$backup_path"
    log "INFO" "Backed up Info.plist to: $backup_path"

    # Update build number
    if /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $new_build" "$info_plist" 2>/dev/null; then
        log "SUCCESS" "Updated CFBundleVersion: $current_build → $new_build"
    else
        # Try alternate key
        if /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $new_build" "$info_plist" 2>/dev/null; then
            log "SUCCESS" "Updated CFBundleVersion: $current_build → $new_build"
        else
            # Restore backup
            cp "$backup_path" "$info_plist"
            error_exit "Failed to update build number. Restored backup."
        fi
    fi

    # Optionally commit to git
    if [[ $do_commit -eq 1 ]]; then
        log "INFO" "Checking for git repository..."

        # Find git root
        local git_root
        git_root=$(git -C "$project_path" rev-parse --show-toplevel 2>/dev/null || echo "")

        if [[ -z "$git_root" ]]; then
            git_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
        fi

        if [[ -n "$git_root" ]]; then
            log "INFO" "Git repository found: $git_root"

            # Stage changes
            log "INFO" "Staging Info.plist changes..."
            git -C "$git_root" add "$info_plist"

            # Check if there are changes to commit
            local status
            status=$(git -C "$git_root" status --porcelain || echo "")

            if [[ -n "$status" ]]; then
                log "INFO" "Committing changes..."

                # Create commit message
                local commit_msg="Build: Increment build number to $new_build"
                if [[ -n "${GIT_AUTHOR_NAME:-}" ]]; then
                    GIT_AUTHOR_NAME="$GIT_AUTHOR_NAME" GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-}" \
                    git -C "$git_root" commit -m "$commit_msg"
                else
                    git -C "$git_root" commit -m "$commit_msg"
                fi

                log "SUCCESS" "Committed changes: $commit_msg"

                # Show commit
                log "INFO" "Commit details:"
                git -C "$git_root" log -1 --oneline | while read -r line; do
                    log "INFO" "  $line"
                done
            else
                log "WARNING" "No changes to commit"
            fi
        else
            log "WARNING" "Not in a git repository, skipping commit"
        fi
    fi

    # Summary
    log "SUCCESS" "=== Build Number Update Complete ==="
    log "INFO" "Info.plist: $info_plist"
    log "INFO" "Old build: $current_build"
    log "INFO" "New build: $new_build"
    log "INFO" ""

    # Output for scripting
    echo ""
    echo "CURRENT_BUILD=$current_build"
    echo "NEW_BUILD=$new_build"

    if [[ $do_commit -eq 1 ]]; then
        echo "GIT_COMMITTED=1"
    fi
}

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

# =============================================================================
# CLEANUP
# =============================================================================

cleanup() {
    local exit_code=$?
    # Call common cleanup if available
    if declare -f cleanup_on_error &>/dev/null; then
        cleanup_on_error "$exit_code" "${BASH_LINENO[0]}"
    fi
    exit $exit_code
}

# Set up error trap
trap 'cleanup' EXIT
trap 'cleanup_on_error $?' ERR

# Run main function
main "$@"
