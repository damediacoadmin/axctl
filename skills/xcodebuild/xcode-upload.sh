#!/bin/bash
#
# xcode-upload.sh - Upload IPA to App Store Connect
# Validates and uploads .ipa files using altool or notarytool
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# =============================================================================
# USAGE
# =============================================================================

usage() {
    cat <<EOF
Usage: $(basename "$0") <ipa_path>

Upload an IPA file to App Store Connect for distribution.

Arguments:
  ipa_path      Path to .ipa file

Options:
  -h, --help    Show this help message
  --validate    Only validate the IPA (don't upload)
  --notary      Use notarytool instead of altool

Examples:
  $(basename "$0") ~/Desktop/MyApp.ipa
  $(basename "$0") ~/Desktop/MyApp.ipa --validate
  $(basename "$0") ~/Desktop/MyApp.ipa --notary

Environment Variables:
  APP_STORE_CONNECT_API_KEY    API Key for App Store Connect authentication
  APP_STORE_CONNECT_KEY_ID     Key ID for API Key authentication
  APP_STORE_CONNECT_ISSUER_ID  Issuer ID for API Key authentication
  APPLE_ID                     Apple ID email (for notarization)
  APPLE_ID_PASSWORD            App-specific password

Notes:
  - For altool: Requires API Key or Apple ID with app-specific password
  - For notarytool: Used for notarization (macOS apps)

EOF
    exit "${1:-0}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    local validate_only=0
    local use_notary=0
    local ipa_path=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage 0
                ;;
            --validate)
                validate_only=1
                shift
                ;;
            --notary)
                use_notary=1
                shift
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                exit 1
                ;;
            *)
                if [[ -z "$ipa_path" ]]; then
                    ipa_path="$1"
                else
                    log "ERROR" "Unexpected argument: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    if [[ -z "$ipa_path" ]]; then
        usage 1
    fi

    # Initialize logging
    if [[ $validate_only -eq 1 ]]; then
        init_logging "validate"
    else
        init_logging "upload"
    fi

    # Expand tilde
    ipa_path="${ipa_path/#\~/$HOME}"

    log "INFO" "=== Starting App Store Connect Upload ==="
    log "INFO" "IPA path: $ipa_path"
    log "INFO" "Validate only: $validate_only"
    log "INFO" "Use notarytool: $use_notary"

    # Validate IPA path
    if [[ ! -f "$ipa_path" ]]; then
        log "ERROR" "IPA file does not exist: $ipa_path"
        exit 1
    fi

    if [[ ! "$ipa_path" == *.ipa ]]; then
        log "ERROR" "Invalid file format. Expected .ipa file"
        exit 1
    fi

    # Get app name from IPA filename
    local app_name
    app_name=$(basename "$ipa_path" .ipa)

    log "INFO" "App name: $app_name"

    # Detect and configure Xcode
    detect_xcode "${XCODE_VERSION:-}"

    # Check for altool or notarytool
    if [[ $use_notary -eq 1 ]]; then
        if ! xcrun notarytool --version &>/dev/null; then
            log "ERROR" "notarytool not found. Install Xcode Command Line Tools."
            exit 1
        fi
        TOOL_NAME="notarytool"
    else
        if ! xcrun altool --version &>/dev/null; then
            log "ERROR" "altool not found. Install Xcode Command Line Tools."
            exit 1
        fi
        TOOL_NAME="altool"
    fi

    log "INFO" "Using tool: $TOOL_NAME"

    # Check authentication - use bash array
    local -a AUTH_ARGS=()
    if [[ -n "${APP_STORE_CONNECT_API_KEY:-}" ]]; then
        log "INFO" "Using API Key authentication"
        AUTH_ARGS=("--apiKey" "$APP_STORE_CONNECT_API_KEY" "--apiIssuer" "$APP_STORE_CONNECT_ISSUER_ID")
    elif [[ -n "${APPLE_ID:-}" ]]; then
        log "INFO" "Using Apple ID authentication"
        AUTH_ARGS=("--apple-id" "$APPLE_ID" "--password" "$APPLE_ID_PASSWORD")
    else
        log "WARNING" "No authentication credentials found"
        log "INFO" "Will attempt with keychain credentials"
    fi

    # Validation and upload logic
    if [[ $use_notary -eq 1 ]]; then
        # notarytool: single step for validate+upload (or just validate)
        if [[ $validate_only -eq 1 ]]; then
            log "INFO" "Validating IPA with notarytool..."
        else
            log "INFO" "Submitting IPA to notarytool (validates + uploads)..."
        fi

        local notary_output
        if notary_output=$(xcrun notarytool submit "$ipa_path" "${AUTH_ARGS[@]}" --wait 2>&1); then
            echo "$notary_output" | tee -a "$LOG_FILE"
            if [[ $validate_only -eq 1 ]]; then
                log "SUCCESS" "IPA validation passed"
            else
                log "SUCCESS" "IPA submitted successfully"
            fi
        else
            local exit_code=$?
            log "ERROR" "Notarytool failed with exit code: $exit_code"
            log "ERROR" "Output: $notary_output"
            exit 1
        fi

        if [[ $validate_only -eq 1 ]]; then
            log "INFO" "=== Validation Complete ==="
            log "SUCCESS" "IPA is ready for upload"
            exit 0
        fi
    else
        # altool: separate validate-app and upload-app steps
        if [[ $validate_only -eq 1 ]] || [[ $use_notary -eq 0 ]]; then
            log "INFO" "Validating IPA with App Store Connect..."

            local validate_output
            if validate_output=$(xcrun altool --validate-app -f "$ipa_path" "${AUTH_ARGS[@]}" 2>&1); then
                echo "$validate_output" | tee -a "$LOG_FILE"
                log "SUCCESS" "IPA validation passed"
            else
                local exit_code=$?
                log "ERROR" "IPA validation failed with exit code: $exit_code"
                log "ERROR" "Output: $validate_output"
                exit 1
            fi

            if [[ $validate_only -eq 1 ]]; then
                log "INFO" "=== Validation Complete ==="
                log "SUCCESS" "IPA is ready for upload"
                exit 0
            fi
        fi

        # Upload IPA with altool
        log "INFO" "Uploading IPA to App Store Connect..."

        local upload_output
        if upload_output=$(xcrun altool --upload-app -f "$ipa_path" "${AUTH_ARGS[@]}" 2>&1); then
            echo "$upload_output" | tee -a "$LOG_FILE"
            log "SUCCESS" "Upload completed successfully"
        else
            local exit_code=$?
            log "ERROR" "Upload failed with exit code: $exit_code"
            log "ERROR" "Output: $upload_output"
            exit 1
        fi
    fi

    # Show upload status
    log "INFO" "Upload summary:"
    log "INFO" "  App: $app_name"
    log "INFO" "  File: $ipa_path"
    log "INFO" "  Status: Uploaded to App Store Connect"

    # Provide next steps
    log "SUCCESS" "=== Upload Complete ==="
    log "INFO" "Next steps:"
    log "INFO" "  1. Log in to App Store Connect: https://appstoreconnect.apple.com"
    log "INFO" "  2. Navigate to My Apps > $app_name"
    log "INFO" "  3. Add build to your app version"
    log "INFO" "  4. Submit for review"
    log "INFO" ""
    log "INFO" "Log file: $LOG_FILE"
}

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

# Set up error trap
trap cleanup_on_error ERR

# Run main function
main "$@"
