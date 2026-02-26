#!/bin/bash
# Build archive from Xcode workspace or project
#
# Usage: ./xcode-archive.sh <project_path> [scheme] [configuration]
# Example: ./xcode-archive.sh ~/clawd/mykavabar-mobile MyKavaBar Release

# Bash strict mode
set -euo pipefail

# Script name for logging
SCRIPT_NAME="archive"

# Source common.sh for functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Initialize logging
init_logging

# Trap errors
trap 'cleanup_on_error $LINENO' ERR

# Usage function
usage() {
    cat <<EOF
Usage: $(basename "$0") <project_path> [scheme] [configuration]

Build an Xcode archive from a workspace or project.

Arguments:
    project_path     Path to the project directory containing .xcworkspace or .xcodeproj
    scheme           Scheme name (auto-detected if not provided)
    configuration    Build configuration (default: Release)

Examples:
    $(basename "$0") ~/clawd/mykavabar-mobile
    $(basename "$0") ~/clawd/mykavabar-mobile MyKavaBar
    $(basename "$0") ~/clawd/mykavabar-mobile MyKavaBar Release
    XCODE_VERSION=26 $(basename "$0") ~/path/to/project

EOF
    exit 1
}

# Start timing
START_TIME=$(date +%s)

# =============================================================================
# Step 1: Validate arguments
# =============================================================================
log "INFO" "Starting Xcode archive build..."

if [[ $# -lt 1 ]]; then
    log "ERROR" "Missing required argument: project_path"
    usage
fi

PROJECT_PATH="$1"
SCHEME="${2:-}"
CONFIGURATION="${3:-Release}"

# Resolve absolute path - check existence first
if [[ ! -d "$PROJECT_PATH" ]]; then
    log "ERROR" "Project path does not exist: $PROJECT_PATH"
    exit 1
fi
PROJECT_PATH=$(cd "$PROJECT_PATH" && pwd)

log "INFO" "Project path: $PROJECT_PATH"

# =============================================================================
# Step 2: Detect Xcode
# =============================================================================
log "INFO" "Detecting Xcode..."
detect_xcode

# Verify xcodebuild is available
XCODEBUILD=$(get_xcodebuild_path)
log "INFO" "xcodebuild path: $XCODEBUILD"

# =============================================================================
# Step 3: Auto-detect workspace or project file
# =============================================================================
log "INFO" "Detecting workspace or project..."

WORKSPACE=""
PROJECT_FILE=""

# Check for workspace first (CocoaPods/SPM)
WORKSPACE=$(find "$PROJECT_PATH" -maxdepth 1 -name "*.xcworkspace" -type d 2>/dev/null | head -n1)

if [[ -n "$WORKSPACE" ]]; then
    log "INFO" "Found workspace: $WORKSPACE"
    
    # Check if Podfile exists
    if [[ -f "$PROJECT_PATH/Podfile" ]]; then
        log "INFO" "Podfile detected - checking if Pods are installed..."
        if [[ ! -d "$PROJECT_PATH/Pods" ]]; then
            log "WARN" "Pods not installed. Running pod install..."
            (
                cd "$PROJECT_PATH"
                pod install
            )
        else
            log "INFO" "Pods already installed"
        fi
    fi
else
    # Fall back to project file
    PROJECT_FILE=$(find "$PROJECT_PATH" -maxdepth 1 -name "*.xcodeproj" -type d 2>/dev/null | head -n1)
    
    if [[ -n "$PROJECT_FILE" ]]; then
        log "INFO" "Found project: $PROJECT_FILE"
    else
        log "ERROR" "No .xcworkspace or .xcodeproj found in $PROJECT_PATH"
        log "ERROR" "Please ensure your project file is in the correct location"
        exit 1
    fi
fi

# =============================================================================
# Step 4: Auto-detect scheme if not provided
# =============================================================================
if [[ -z "$SCHEME" ]]; then
    log "INFO" "Auto-detecting scheme..."
    
    # Get list of available schemes
    if [[ -n "$WORKSPACE" ]]; then
        scheme_list=$("$XCODEBUILD" -workspace "$WORKSPACE" -list 2>/dev/null) || true
    else
        scheme_list=$("$XCODEBUILD" -project "$PROJECT_FILE" -list 2>/dev/null) || true
    fi
    
    if [[ -z "$scheme_list" ]]; then
        log "ERROR" "Failed to retrieve scheme list"
        log "ERROR" "Ensure your project is properly configured"
        exit 1
    fi
    
    # Parse schemes (skip header lines)
    SCHEME=$(echo "$scheme_list" | grep -A 100 "Schemes:" | tail -n +2 | head -1 | xargs)
    
    if [[ -z "$SCHEME" ]]; then
        log "ERROR" "Could not auto-detect scheme"
        log "INFO" "Please provide scheme name as second argument"
        exit 1
    fi
    
    log "INFO" "Auto-detected scheme: $SCHEME"
    
    # Log all available schemes
    log "INFO" "Available schemes:"
    echo "$scheme_list" | grep -A 100 "Schemes:" | tail -n +2 | while read -r scheme; do
        [[ -n "$scheme" ]] && log "INFO" "  - $scheme"
    done
else
    log "INFO" "Using provided scheme: $SCHEME"
fi

# =============================================================================
# Step 5: Set configuration
# =============================================================================
log "INFO" "Build configuration: $CONFIGURATION"

# =============================================================================
# Step 6: Check code signing (optional, warn only)
# =============================================================================
log "INFO" "Checking code signing identities..."
check_signing_identity 2>/dev/null || log "WARN" "Code signing issues may prevent successful archive"

# =============================================================================
# Step 7: Clean build folder
# =============================================================================
log "INFO" "Cleaning build folder..."

BUILD_CLEAN_LOG="${LOG_DIR}/clean-${START_TIME}.log"

if [[ -n "$WORKSPACE" ]]; then
    "$XCODEBUILD" -workspace "$WORKSPACE" \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -destination 'generic/platform=iOS' \
        clean 2>&1 | tee "$BUILD_CLEAN_LOG"
else
    "$XCODEBUILD" -project "$PROJECT_FILE" \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -destination 'generic/platform=iOS' \
        clean 2>&1 | tee "$BUILD_CLEAN_LOG"
fi

if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    log "ERROR" "Clean failed"
    exit 1
fi

log "SUCCESS" "Clean completed"

# =============================================================================
# Step 8: Build archive
# =============================================================================
log "INFO" "Building archive..."

# Generate output path
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
APP_NAME="${SCHEME}"
ARCHIVE_PATH="${HOME}/Desktop/${APP_NAME}-${TIMESTAMP}.xcarchive"

log "INFO" "Archive output: $ARCHIVE_PATH"

# Build the archive
BUILD_LOG="${LOG_DIR}/build-${TIMESTAMP}.log"

if [[ -n "$WORKSPACE" ]]; then
    "$XCODEBUILD" -workspace "$WORKSPACE" \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -destination 'generic/platform=iOS' \
        -archivePath "$ARCHIVE_PATH" \
        archive 2>&1 | tee "$BUILD_LOG"
else
    "$XCODEBUILD" -project "$PROJECT_FILE" \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -destination 'generic/platform=iOS' \
        -archivePath "$ARCHIVE_PATH" \
        archive 2>&1 | tee "$BUILD_LOG"
fi

BUILD_STATUS=${PIPESTATUS[0]}

# Show build log location
log "INFO" "Full build log: $BUILD_LOG"

# =============================================================================
# Step 9: Verify archive created
# =============================================================================
if [[ $BUILD_STATUS -ne 0 ]]; then
    log "ERROR" "Build failed with exit code $BUILD_STATUS"
    
    # Show common fixes
    log "INFO" "Common fixes:"
    log "INFO" "  1. Check code signing: Ensure you have valid certificates"
    log "INFO" "  2. Update dependencies: cd $PROJECT_PATH && pod install"
    log "INFO" "  3. Check Xcode preferences: Xcode → Settings → Accounts"
    log "INFO" "  4. Clean derived data: rm -rf ~/Library/Developer/Xcode/DerivedData"
    log "INFO" "  5. Check for scheme errors in the log above"
    
    # Show last few lines of build log for debugging
    log "ERROR" "Last 20 lines of build log:"
    tail -20 "$BUILD_LOG" | while read -r line; do
        log "ERROR" "  $line"
    done
    
    exit $BUILD_STATUS
fi

# Verify archive exists and has correct structure
if [[ ! -d "$ARCHIVE_PATH" ]]; then
    log "ERROR" "Archive was not created at expected path: $ARCHIVE_PATH"
    exit 1
fi

# Check for required archive contents
if [[ ! -f "$ARCHIVE_PATH/Info.plist" ]] || [[ ! -d "$ARCHIVE_PATH/Products" ]]; then
    log "ERROR" "Archive verification failed: missing required contents"
    exit 1
fi

log "SUCCESS" "Archive verified: $ARCHIVE_PATH"

# =============================================================================
# Step 10: Log success with details
# =============================================================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECS=$((DURATION % 60))

# Get archive size
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_PATH" | cut -f1)

log "SUCCESS" "=========================================="
log "SUCCESS" "Archive build completed successfully!"
log "SUCCESS" "=========================================="
log "INFO" "Archive path: $ARCHIVE_PATH"
log "INFO" "Archive size: $ARCHIVE_SIZE"
log "INFO" "Scheme: $SCHEME"
log "INFO" "Configuration: $CONFIGURATION"
log "INFO" "Duration: ${MINUTES}m ${SECS}s"
log "INFO" "Log file: $LOG_FILE"

# Summary
echo ""
echo "=========================================="
echo "✅ Archive created successfully!"
echo "=========================================="
echo "📦 Archive: $ARCHIVE_PATH"
echo "📊 Size: $ARCHIVE_SIZE"
echo "⏱️  Duration: ${MINUTES}m ${SECS}s"
echo "=========================================="

exit 0
