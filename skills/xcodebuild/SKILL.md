# Xcode Build Skill for OpenClaw

A complete, production-ready skill for building, archiving, exporting, and uploading iOS apps using Xcode's command-line tools.

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Scripts Overview](#scripts-overview)
- [Environment Variables](#environment-variables)
- [Example Workflows](#example-workflows)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Installation

### Prerequisites

1. **Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **CocoaPods** (if using pods)
   ```bash
   sudo gem install cocoapods
   ```

3. **OpenClaw Configuration**
   ```bash
   # Ensure the skill directory exists
   mkdir -p ~/clawd/skills

   # Scripts will be placed in ~/clawd/skills/xcodebuild/
   ```

### Make Scripts Executable

```bash
cd ~/clawd/skills/xcodebuild
chmod +x *.sh
```

---

## ⚡ Quick Start

### Build and Upload MyKavaBar to TestFlight

```bash
# 1. Increment build number
~/clawd/skills/xcodebuild/xcode-increment-build.sh ~/Projects/MyKavaBar --commit

# 2. Build archive
~/clawd/skills/xcodebuild/xcode-archive.sh ~/Projects/MyKavaBar

# 3. Export IPA (App Store)
~/clawd/skills/xcodebuild/xcode-export.sh ~/Desktop/MyKavaBar.xcarchive ~/Desktop app-store

# 4. Upload to TestFlight
~/clawd/skills/xcodebuild/xcode-upload.sh ~/Desktop/MyKavaBar.ipa
```

---

## 📜 Scripts Overview

### 1. xcode-archive.sh

Build an Xcode project and create an `.xcarchive` file.

```bash
./xcode-archive.sh <project_path> [scheme] [configuration]
```

**Arguments:**
- `project_path` - Path to `.xcodeproj`, `.xcworkspace`, or directory
- `scheme` (optional) - Build scheme name
- `configuration` (optional) - Debug or Release (default: Release)

**Example:**
```bash
# Build MyApp with Release configuration
./xcode-archive.sh ~/Projects/MyApp MyAppScheme Release

# Build with default settings
./xcode-archive.sh ~/Projects/MyApp
```

**Output:** `~/Desktop/<app>.xcarchive`

---

### 2. xcode-export.sh

Export an IPA file from an archive with signing.

```bash
./xcode-export.sh <archive_path> [output_dir] [export_type]
```

**Arguments:**
- `archive_path` - Path to `.xcarchive` file
- `output_dir` (optional) - Output directory (default: `~/Desktop`)
- `export_type` (optional) - `app-store`, `ad-hoc`, `enterprise` (default: `app-store`)

**Examples:**
```bash
# Export for App Store distribution
./xcode-export.sh ~/Desktop/MyApp.xcarchive ~/Desktop app-store

# Export for Ad Hoc testing
./xcode-export.sh ~/Desktop/MyApp.xcarchive ~/Downloads ad-hoc
```

**Output:** `<output_dir>/<app>.ipa`

---

### 3. xcode-upload.sh

Upload an IPA to App Store Connect for distribution.

```bash
./xcode-upload.sh <ipa_path> [options]
```

**Options:**
- `--validate` - Only validate, don't upload
- `--notary` - Use notarytool instead of altool

**Examples:**
```bash
# Upload to App Store Connect
./xcode-upload.sh ~/Desktop/MyApp.ipa

# Validate only
./xcode-upload.sh ~/Desktop/MyApp.ipa --validate

# Upload with notarization
./xcode-upload.sh ~/Desktop/MyApp.ipa --notary
```

---

### 4. xcode-increment-build.sh

Auto-increment the build number in Info.plist.

```bash
./xcode-increment-build.sh <project_path> [--commit]
```

**Arguments:**
- `project_path` - Path to project or workspace
- `--commit` - Optional: Commit the change to git

**Examples:**
```bash
# Increment build number
./xcode-increment-build.sh ~/Projects/MyApp

# Increment and commit to git
./xcode-increment-build.sh ~/Projects/MyApp --commit
```

---

## 🔧 Environment Variables

Configure the build behavior with these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `XCODE_VERSION` | Override Xcode version | `XCODE_VERSION=16.4` |
| `DEVELOPER_DIR` | Override developer directory | `/Applications/Xcode.app/Contents/Developer` |
| `PROVISIONING_PROFILE` | Specific profile name/UUID | `PROVISIONING_PROFILE="My App Profile"` |
| `APP_STORE_CONNECT_API_KEY` | API Key for authentication | `APP_STORE_CONNECT_API_KEY="KEY123"` |
| `APP_STORE_CONNECT_KEY_ID` | API Key ID | `APP_STORE_CONNECT_KEY_ID="ABC123"` |
| `APP_STORE_CONNECT_ISSUER_ID` | Issuer ID | `APP_STORE_CONNECT_ISSUER_ID="abc-123"` |
| `APPLE_ID` | Apple ID email | `APPLE_ID="dev@example.com"` |
| `APPLE_ID_PASSWORD` | App-specific password | `APPLE_ID_PASSWORD="xxxx-xxxx-xxxx"` |

### Setting Environment Variables

**Temporary (current session):**
```bash
export XCODE_VERSION=16.4
./xcode-archive.sh ~/Projects/MyApp
```

**Permanent (add to shell profile):**
```bash
# Add to ~/.zshrc or ~/.bash_profile
export XCODE_VERSION=16.4
export APP_STORE_CONNECT_API_KEY="your-api-key"
```

---

## 📝 Example Workflows

### Workflow 1: Build and Distribute Ad Hoc

```bash
#!/bin/bash
# Build and create Ad Hoc distribution

PROJECT_PATH=~/Projects/MyApp
ARCHIVE_PATH=~/Desktop/MyApp.xcarchive
IPA_PATH=~/Desktop/MyApp.ipa

# Step 1: Increment build number
echo "Incrementing build number..."
~/clawd/skills/xcodebuild/xcode-increment-build.sh "$PROJECT_PATH" --commit

# Step 2: Build archive
echo "Building archive..."
~/clawd/skills/xcodebuild/xcode-archive.sh "$PROJECT_PATH"

# Step 3: Export IPA
echo "Exporting IPA..."
~/clawd/skills/xcodebuild/xcode-export.sh "$ARCHIVE_PATH" ~/Desktop ad-hoc

# Step 4: Upload (optional)
echo "Uploading to TestFlight..."
~/clawd/skills/xcodebuild/xcode-upload.sh "$IPA_PATH"

echo "Done! IPA at: $IPA_PATH"
```

### Workflow 2: CI/CD Pipeline

```bash
#!/bin/bash
# CI/CD build pipeline

set -e

# Configure
export XCODE_VERSION=16.4
export APP_STORE_CONNECT_API_KEY="${API_KEY}"
export APP_STORE_CONNECT_KEY_ID="${KEY_ID}"
export APP_STORE_CONNECT_ISSUER_ID="${ISSUER_ID}"

# Build
echo "Building archive..."
~/clawd/skills/xcodebuild/xcode-archive.sh ~/Projects/MyApp

# Export
echo "Exporting IPA..."
~/clawd/skills/xcodebuild/xcode-export.sh ~/Desktop/MyApp.xcarchive "$ARTIFACTS_DIR" app-store

# Validate
echo "Validating IPA..."
~/clawd/skills/xcodebuild/xcode-upload.sh "$ARTIFACTS_DIR/MyApp.ipa" --validate

# Upload
echo "Uploading to App Store Connect..."
~/clawd/skills/xcodebuild/xcode-upload.sh "$ARTIFACTS_DIR/MyApp.ipa"

echo "Pipeline complete!"
```

### Workflow 3: Quick Build for Testing

```bash
#!/bin/bash
# Quick debug build for testing

# Build with Debug configuration
~/clawd/skills/xcodebuild/xcode-archive.sh ~/Projects/MyApp MyApp Debug

# Export for simulator or Ad Hoc
~/clawd/skills/xcodebuild/xcode-export.sh ~/Desktop/MyApp.xcarchive ~/Desktop ad-hoc

echo "Build complete!"
```

---

## 🔍 Troubleshooting

### Common Errors

#### 1. "Xcode not found"

**Error:**
```
ERROR: Xcode not found at /Applications/Xcode-16.4.app
```

**Solution:**
```bash
# Check available Xcode versions
ls /Applications/Xcode*.app

# Use default Xcode (without version override)
XCODE_VERSION= ./xcode-archive.sh ~/Projects/MyApp

# Or specify correct version
export XCODE_VERSION=16.4
```

---

#### 2. "No code signing identities found"

**Error:**
```
WARNING: No code signing identities found in keychain
```

**Solution:**
```bash
# Check available identities
security find-identity -v -p codesigning

# Import developer certificate (if you have one)
security import /path/to/certificate.p12 -P password

# Or download from Apple Developer portal:
# 1. Go to https://developer.apple.com/account
# 2. Certificates, IDs & Profiles
# 3. Download and double-click to install
```

---

#### 3. "No provisioning profiles found"

**Error:**
```
WARNING: Provisioning Profiles directory not found
```

**Solution:**
```bash
# Create directory if missing
mkdir -p ~/Library/MobileDevice/Provisioning\ Profiles

# Download provisioning profiles from Apple Developer portal
# 1. Go to https://developer.apple.com/account
# 2. Certificates, IDs & Profiles > Profiles
# 3. Download and double-click to install

# List installed profiles
ls ~/Library/MobileDevice/Provisioning\ Profiles/
```

---

#### 4. "IPA validation failed"

**Error:**
```
ERROR: IPA validation failed with exit code: 1
```

**Solutions:**

**A. Check authentication:**
```bash
# Verify API Key credentials
export APP_STORE_CONNECT_API_KEY="your-api-key"
export APP_STORE_CONNECT_KEY_ID="your-key-id"
export APP_STORE_CONNECT_ISSUER_ID="your-issuer-id"

# Or use Apple ID
export APPLE_ID="your-email@example.com"
export APPLE_ID_PASSWORD="app-specific-password"
```

**B. Verify app in App Store Connect:**
- Ensure the app exists in App Store Connect
- Check that bundle identifier matches
- Verify certificates are valid

---

#### 5. "Archive build failed"

**Error:**
```
ERROR: Archive build failed with exit code: 65
```

**Solutions:**

**A. Clean build folder:**
```bash
# Clean derived data
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Rebuild
./xcode-archive.sh ~/Projects/MyApp
```

**B. Check project configuration:**
```bash
# Verify scheme exists
xcodebuild -list -workspace ~/Projects/MyApp/MyApp.xcworkspace

# Verify target configuration
xcodebuild -scheme MyApp -showBuildSettings
```

---

#### 6. "CocoaPods not installed"

**Error:**
```
ERROR: CocoaPods is not installed. Run: sudo gem install cocoapods
```

**Solution:**
```bash
# Install CocoaPods
sudo gem install cocoapods

# Or via Homebrew
brew install cocoapods

# Initialize (if first time)
pod setup
```

---

#### 7. "Info.plist not found"

**Error:**
```
ERROR: Could not find Info.plist in project
```

**Solution:**
```bash
# Find Info.plist manually
find ~/Projects/MyApp -name "Info.plist" -type f

# Specify full path if needed
./xcode-increment-build.sh ~/Projects/MyApp/MyApp/App/Info.plist
```

---

### Log Files

All operations create detailed log files in `~/MacAutomator/logs/xcodebuild/`:

```
archive-2026-02-20-10-30-45.log    # Archive build logs
export-2026-02-20-10-35-12.log     # Export logs
upload-2026-02-20-10-40-00.log      # Upload logs
increment-build-2026-02-20-10-25-00.log  # Build number increment logs
```

**View logs:**
```bash
# List recent logs
ls -lt ~/MacAutomator/logs/xcodebuild/

# View specific log
cat ~/MacAutomator/logs/xcodebuild/archive-2026-02-20-10-30-45.log

# Follow log in real-time
tail -f ~/MacAutomator/logs/xcodebuild/archive-*.log
```

---

### Debug Mode

Enable verbose output for debugging:

```bash
# Set environment variable for verbose xcodebuild output
export XCODE_BUILD_LOG=1

# Run script
./xcode-archive.sh ~/Projects/MyApp
```

---

## 📚 Additional Resources

- [Xcode Command Line Tools Documentation](https://developer.apple.com/documentation/xcode/running-your-app-from-the-command-line)
- [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi)
- [CocoaPods Guides](https://guides.cocoapods.org/)
- [Code Signing Troubleshooting](https://developer.apple.com/support/code-signing/)

---

## 🤝 Support

For issues or questions:

1. Check the log files in `~/MacAutomator/logs/xcodebuild/`
2. Verify your Xcode and certificate configuration
3. Review the troubleshooting section above

**Common quick fixes:**
```bash
# Reset Xcode cache
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Reset signing certificates cache
security delete-certificate -c "iPhone Developer" 2>/dev/null || true

# Update CocoaPods
pod repo update
```
