#!/bin/bash
# Common functions for xcodebuild skill

# Bash strict mode
set -euo pipefail

# Check for valid license (Pro feature)
check_license() {
    # Find the check-license.js script
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local check_license="$script_dir/../../bin/check-license.js"
    
    if [[ ! -f "$check_license" ]]; then
        # Try alternative path (when installed via npm)
        check_license="$(dirname $(dirname "$script_dir"))/bin/check-license.js"
    fi
    
    if [[ -f "$check_license" ]]; then
        node "$check_license" || exit 1
    else
        echo "❌ License checker not found. Please reinstall AXCTL."
        exit 1
    fi
}

# Color codes
readonly COLORS_RESET='\033[0m'
readonly COLORS_RED='\033[0;31m'
readonly COLORS_GREEN='\033[0;32m'
readonly COLORS_YELLOW='\033[0;33m'
readonly COLORS_BLUE='\033[0;34m'

# Log directory
readonly LOG_DIR="$HOME/MacAutomator/logs/xcodebuild"

# Function: log(level, message)
# Log with color output and file logging
log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    local color=""
    local level_prefix=""
    
    case "$level" in
        INFO)
            color="$COLORS_BLUE"
            level_prefix="ℹ️"
            ;;
        WARN)
            color="$COLORS_YELLOW"
            level_prefix="⚠️"
            ;;
        ERROR)
            color="$COLORS_RED"
            level_prefix="❌"
            ;;
        SUCCESS)
            color="$COLORS_GREEN"
            level_prefix="✅"
            ;;
        *)
            color="$COLORS_RESET"
            level_prefix="•"
            ;;
    esac
    
    # Format log line
    local log_line="[$timestamp] [$level] $message"
    
    # Write to log file
    if [[ -n "${LOG_FILE:-}" ]]; then
        echo "$log_line" >> "$LOG_FILE"
    fi
    
    # Output to stdout with color
    echo -e "${color}${log_line}${COLORS_RESET}"
}

# Function: detect_xcode()
# Auto-detect latest stable Xcode path, support XCODE_VERSION override
detect_xcode() {
    local xcode_path=""
    local xcode_version=""

    # Check for XCODE_VERSION override
    if [[ -n "${XCODE_VERSION:-}" ]]; then
        log "INFO" "XCODE_VERSION override specified: ${XCODE_VERSION}"
        
        # Try specific version path
        xcode_path="/Applications/Xcode-${XCODE_VERSION}.app"
        
        if [[ ! -d "$xcode_path" ]]; then
            log "ERROR" "Xcode ${XCODE_VERSION} not found at ${xcode_path}"
            log "ERROR" "Available Xcode versions:"
            ls -la /Applications/ | grep -i xcode || true
            exit 1
        fi
        
        xcode_version="$XCODE_VERSION"
    else
        # Auto-detect latest stable Xcode
        # Check Xcode 16.x first (latest stable as of early 2026)
        for major in 17 16; do
            for minor in 4 3 2 1 0; do
                local candidate="/Applications/Xcode-${major}.${minor}.app"
                if [[ -d "$candidate" ]]; then
                    xcode_path="$candidate"
                    xcode_version="${major}.${minor}"
                    break 2
                fi
            done
        done
        
        # Fallback to default Xcode location
        if [[ -z "$xcode_path" ]] && [[ -d "/Applications/Xcode.app" ]]; then
            xcode_path="/Applications/Xcode.app"
            xcode_version=$(/usr/bin/defaults read "$xcode_path/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "unknown")
        fi
    fi
    
    # Check if Xcode found
    if [[ -z "$xcode_path" ]] || [[ ! -d "$xcode_path" ]]; then
        log "ERROR" "No Xcode installation found"
        log "ERROR" "Please install Xcode from Mac App Store or specify XCODE_VERSION"
        exit 1
    fi
    
    # Export DEVELOPER_DIR
    export DEVELOPER_DIR="$xcode_path/Contents/Developer"
    export PATH="$xcode_path/Contents/Developer/usr/bin:$PATH"
    
    log "INFO" "Using Xcode: $xcode_path (version $xcode_version)"
    log "INFO" "DEVELOPER_DIR set to: $DEVELOPER_DIR"
    
    # Warn if using Xcode 16.x (deprecation warning)
    if [[ "$xcode_version" =~ ^16\.[0-9]+$ ]]; then
        log "WARN" "Xcode 16.x is approaching end-of-life. Consider upgrading to Xcode 17.x+"
    fi
    
    return 0
}

# Function: check_signing_identity(identity_name)
# Check if signing identity exists
check_signing_identity() {
    local identity_name="${1:-}"
    
    # Get available signing identities
    local identities
    identities=$(security find-identity -v -p codesigning 2>/dev/null) || true
    
    if [[ -z "$identities" ]]; then
        log "WARN" "No code signing identities found"
        log "INFO" "You may need to:"
        log "INFO" "  1. Add your Apple Developer account in Xcode"
        log "INFO" "  2. Create a signing certificate in Xcode → Preferences → Accounts"
        return 1
    fi
    
    # If identity name provided, check for it
    if [[ -n "$identity_name" ]]; then
        if echo "$identities" | grep -qF "$identity_name"; then
            log "SUCCESS" "Found signing identity: $identity_name"
            return 0
        else
            log "WARN" "Signing identity '$identity_name' not found"
            log "INFO" "Available identities:"
            echo "$identities" | while read -r line; do
                log "INFO" "  $line"
            done
            return 1
        fi
    fi
    
    # No identity name provided, just log available
    log "INFO" "Available code signing identities:"
    echo "$identities" | while read -r line; do
        log "INFO" "  $line"
    done
    
    return 0
}

# Function: cleanup_on_error()
# Trap ERR signal for cleanup
cleanup_on_error() {
    local exit_code=$?
    local line_number=${1:-0}
    
    if [[ $exit_code -ne 0 ]]; then
        log "ERROR" "Script failed at line $line_number with exit code $exit_code"
        
        # Clean up any temporary files
        if [[ -n "${TEMP_FILES:-}" ]]; then
            for temp_file in $TEMP_FILES; do
                if [[ -f "$temp_file" ]]; then
                    rm -f "$temp_file"
                    log "INFO" "Cleaned up temp file: $temp_file"
                fi
            done
        fi
        
        # Kill any background build processes
        if [[ -n "${BUILD_PID:-}" ]]; then
            kill "$BUILD_PID" 2>/dev/null || true
        fi
    fi
    
    return $exit_code
}

# Initialize logging
init_logging() {
    local script_name="${SCRIPT_NAME:-xcodebuild}"
    local timestamp
    timestamp=$(date '+%Y-%m-%d-%H-%M-%S')
    
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Set log file path
    LOG_FILE="${LOG_DIR}/${script_name}-${timestamp}.log"
    
    log "INFO" "Logging to: $LOG_FILE"
}

# Function: check_command_exists(command)
# Check if a command exists
check_command_exists() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log "ERROR" "Required command '$cmd' not found"
        log "INFO" "Install with: brew install $cmd"
        return 1
    fi
    return 0
}

# Function: get_xcodebuild_path()
# Get xcodebuild path
get_xcodebuild_path() {
    if [[ -n "${DEVELOPER_DIR:-}" ]]; then
        echo "${DEVELOPER_DIR}/usr/bin/xcodebuild"
    elif command -v xcodebuild &>/dev/null; then
        echo "$(command -v xcodebuild)"
    else
        log "ERROR" "xcodebuild not found. Run detect_xcode first."
        return 1
    fi
}
