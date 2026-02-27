#!/bin/bash
# Export IPA from Xcode archive
#
# Usage: ./xcode-export.sh <archive_path> [output_dir] [method]
# Example: ./xcode-export.sh ~/Desktop/MyKavaBar-20260220.xcarchive ~/Desktop app-store

# Bash strict mode
set -euo pipefail

# Script name for logging
SCRIPT_NAME="export"

# Source common.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Check for valid Pro license
check_license

# Initialize logging
init_logging

# Trap errors
trap 'cleanup_on_error $LINENO' ERR

# Usage function
usage() {
    cat << USAGE
Usage: $(basename "$0") <archive_path> [output_dir] [method]

Export IPA from Xcode archive

Arguments:
    archive_path    Path to .xcarchive file (required)
    output_dir      Output directory (optional, default: ~/Desktop/export-<timestamp>)
    method          Export method (optional, default: app-store)
                   Options: app-store, ad-hoc, enterprise, development

Examples:
    # Export for App Store
    ./xcode-export.sh ~/Desktop/MyApp.xcarchive

    # Export to specific directory with ad-hoc method
    ./xcode-export.sh ~/Desktop/MyApp.xcarchive ~/Desktop/MyBuilds ad-hoc

    # Export for development testing
    ./xcode-export.sh ~/Desktop/MyApp.xcarchive ~/Desktop development

USAGE
    exit 1
}

# Validate arguments
validate_archive() {
    local archive_path="$1"
    
    # Check archive path provided
    if [[ -z "$archive_path" ]]; then
        log "ERROR" "Archive path is required"
        usage
    fi
    
    # Check archive exists
    if [[ ! -e "$archive_path" ]]; then
        log "ERROR" "Archive not found: $archive_path"
        log "INFO" "Please provide a valid path to a .xcarchive file"
        exit 1
    fi
    
    # Check it's a directory (xcarchive is a bundle/directory)
    if [[ ! -d "$archive_path" ]]; then
        log "ERROR" "Archive is not a directory: $archive_path"
        log "INFO" "A .xcarchive is a bundle, not a file"
        exit 1
    fi
    
    # Validate archive structure
    local info_plist="$archive_path/Info.plist"
    local products_dir="$archive_path/Products"
    
    if [[ ! -f "$info_plist" ]]; then
        log "ERROR" "Invalid archive structure: Info.plist not found"
        log "INFO" "Expected: $info_plist"
        exit 1
    fi
    
    if [[ ! -d "$products_dir" ]]; then
        log "ERROR" "Invalid archive structure: Products directory not found"
        log "INFO" "Expected: $products_dir"
        exit 1
    fi
    
    # Find .app inside Products
    local app_path
    app_path=$(find "$products_dir" -name "*.app" -type d 2>/dev/null | head -n1)
    
    if [[ -z "$app_path" ]]; then
        log "ERROR" "No .app bundle found in archive Products directory"
        exit 1
    fi
    
    log "SUCCESS" "Archive validated: $archive_path"
    echo "$app_path"
}

# Extract app info from archive
get_app_info() {
    local archive_path="$1"
    local app_info_plist
    app_info_plist=$(find "$archive_path/Products" -name "Info.plist" -path "*.app/Info.plist" -type f 2>/dev/null | head -n1)
    
    if [[ -n "$app_info_plist" ]] && [[ -f "$app_info_plist" ]]; then
        local bundle_id
        local app_name
        
        bundle_id=$(/usr/bin/defaults read "${app_info_plist%/Info.plist}/Info" CFBundleIdentifier 2>/dev/null || echo "")
        app_name=$(/usr/bin/defaults read "${app_info_plist%/Info.plist}/Info" CFBundleName 2>/dev/null || echo "")
        
        if [[ -z "$app_name" ]]; then
            app_name=$(/usr/bin/defaults read "${app_info_plist%/Info.plist}/Info" CFBundleDisplayName 2>/dev/null || echo "")
        fi
        
        if [[ -z "$app_name" ]]; then
            app_name=$(basename "$archive_path" .xcarchive)
        fi
        
        echo "$app_name|$bundle_id"
    else
        local app_name
        app_name=$(basename "$archive_path" .xcarchive)
        echo "$app_name|"
    fi
}

# Create ExportOptions.plist
create_export_options() {
    local method="$1"
    local output_file="$2"
    
    local method_value=""
    local thinning=""
    local upload_symbols="false"
    
    case "$method" in
        app-store|app-store-connect)
            method_value="app-store-connect"
            upload_symbols="true"
            ;;
        ad-hoc)
            method_value="ad-hoc"
            thinning="<thin-for-all-variants>"
            ;;
        enterprise)
            method_value="enterprise"
            ;;
        development)
            method_value="development"
            ;;
        *)
            log "WARN" "Unknown export method: $method, using 'development'"
            method_value="development"
            ;;
    esac
    
    cat > "$output_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>$method_value</string>
    <key>uploadSymbols</key>
    <$upload_symbols/>
EOF

    if [[ -n "$thinning" ]]; then
        cat >> "$output_file" << EOF
    <key>thinning</key>
    <string>$thinning</string>
EOF
    fi

    cat >> "$output_file" << EOF
    <key>signingStyle</key>
    <string>automatic</string>
    <key>stripSwiftSymbols</key>
    <true/>
</dict>
</plist>
EOF

    log "INFO" "Created ExportOptions.plist for method: $method_value"
}

# Find IPA in output directory
find_ipa() {
    local output_dir="$1"
    local ipa_path
    
    ipa_path=$(find "$output_dir" -name "*.ipa" -type f 2>/dev/null | head -n1)
    
    if [[ -n "$ipa_path" ]]; then
        echo "$ipa_path"
        return 0
    fi
    return 1
}

# Main function
main() {
    local archive_path="${1:-}"
    local output_dir="${2:-}"
    local method="${3:-app-store}"
    
    local start_time
    start_time=$(date +%s)
    
    # Step 1: Validate arguments
    log "INFO" "Starting IPA export..."
    log "INFO" "Archive: ${archive_path:-<not specified>}"
    log "INFO" "Method: $method"
    
    # Step 2: Validate archive
    local app_path
    app_path=$(validate_archive "$archive_path")
    
    # Step 3: Detect Xcode
    log "INFO" "Detecting Xcode..."
    detect_xcode
    
    local xcodebuild
    xcodebuild=$(get_xcodebuild_path)
    
    # Step 4: Set output directory
    if [[ -z "$output_dir" ]]; then
        local timestamp
        timestamp=$(date '+%Y%m%d-%H%M%S')
        output_dir="$HOME/Desktop/export-${timestamp}"
    fi
    
    # Create output directory
    mkdir -p "$output_dir"
    log "INFO" "Output directory: $output_dir"
    
    # Step 5: Set export method (already done via parameter)
    log "INFO" "Export method: $method"
    
    # Step 6: Get app info
    local app_info
    app_info=$(get_app_info "$archive_path")
    local app_name
    local bundle_id
    app_name=$(echo "$app_info" | cut -d'|' -f1)
    bundle_id=$(echo "$app_info" | cut -d'|' -f2)
    
    log "INFO" "App name: ${app_name:-unknown}"
    log "INFO" "Bundle ID: ${bundle_id:-unknown}"
    
    # Step 7: Create ExportOptions.plist
    local export_options_file
    export_options_file=$(mktemp "${TMPDIR:-/tmp}/export_options_XXXXXX.plist")
    TEMP_FILES="${TEMP_FILES:-} $export_options_file"
    
    create_export_options "$method" "$export_options_file"
    
    log "INFO" "Export options: $export_options_file"
    
    # Step 8: Run xcodebuild -exportArchive
    log "INFO" "Running xcodebuild -exportArchive..."
    log "INFO" "This may take a few minutes..."
    
    if "$xcodebuild" -exportArchive \
        -archivePath "$archive_path" \
        -exportPath "$output_dir" \
        -exportOptionsPlist "$export_options_file" \
        -allowProvisioningUpdates \
        2>&1 | tee -a "$LOG_FILE"; then
        log "SUCCESS" "Export completed successfully"
    else
        log "ERROR" "Export failed"
        log "INFO" "Common fixes:"
        log "INFO" "  1. Ensure you have a valid signing identity (run: security find-identity -v -p codesigning)"
        log "INFO" "  2. Check your provisioning profiles are valid (open Xcode → Preferences → Accounts)"
        log "INFO" "  3. For App Store: ensure you have a valid App Store distribution certificate"
        log "INFO" "  4. Try adding -skipPackageUpdates if network issues occur"
        exit 1
    fi
    
    # Step 9: Verify IPA created
    log "INFO" "Verifying IPA..."
    
    local ipa_path
    if ! ipa_path=$(find_ipa "$output_dir"); then
        log "ERROR" "No IPA file found in output directory: $output_dir"
        log "INFO" "Contents of output directory:"
        ls -la "$output_dir" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    # Get IPA size
    local ipa_size
    ipa_size=$(du -h "$ipa_path" | cut -f1)
    
    # Calculate duration
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_formatted
    if [[ $duration -lt 60 ]]; then
        duration_formatted="${duration}s"
    else
        duration_formatted="$((duration / 60))m $((duration % 60))s"
    fi
    
    # Step 10: Log success
    log "SUCCESS" "========================================"
    log "SUCCESS" "IPA Export Complete!"
    log "SUCCESS" "========================================"
    log "SUCCESS" "IPA: $ipa_path"
    log "SUCCESS" "Size: $ipa_size"
    log "SUCCESS" "Duration: $duration_formatted"
    log "INFO" "Log file: $LOG_FILE"
}

# Run main
main "$@"
