# AXCTL Installation Guide

## Prerequisites

- macOS 12+ (Monterey or later)
- Xcode 14+ (for iOS automation features)
- Node.js 18+ (for npm installation)
- Python 3.9+ (for CLI tools)

## Quick Start (Free Tier)

### 1. Install via npm

```bash
npm install -g @axctl/core
```

### 2. Grant Accessibility Permissions

System Settings → Privacy & Security → Accessibility → Add Terminal/iTerm

### 3. Test Desktop Automation

```bash
# List running apps
ax-helper list-apps

# Query Safari UI
ax-helper query Safari

# Click a button
ax-helper click "Button:OK"
```

## Pro Tier Setup (iOS Automation)

### 1. Purchase License

Visit https://axctl.dev and choose Annual ($69/year) or Lifetime ($179).

You'll receive your license key via email.

### 2. Activate License

```bash
axctl activate YOUR-LICENSE-KEY
```

### 3. Configure App Store Connect API

Generate an API key at: https://appstoreconnect.apple.com/access/api

```bash
# Set up ASC credentials
export ASC_KEY_ID="YOUR_KEY_ID"
export ASC_ISSUER_ID="YOUR_ISSUER_ID"
export ASC_KEY_PATH="/path/to/AuthKey_KEYID.p8"
```

### 4. Test Xcode Automation

```bash
# Archive your app
xcode-archive \
  --project MyApp.xcodeproj \
  --scheme MyApp \
  --configuration Release

# Export IPA
xcode-export \
  --archive MyApp.xcarchive \
  --method app-store

# Upload to TestFlight
xcode-upload \
  --ipa MyApp.ipa \
  --asc-key-id $ASC_KEY_ID
```

## Manual Installation (from GitHub)

### Clone Repository

```bash
git clone https://github.com/damediacoadmin/axctl.git
cd axctl
```

### Install Dependencies

```bash
# API server (optional, for self-hosting)
cd api
npm install

# Desktop automation
cd ../skills/ax-helper
pip3 install -r requirements.txt

# iOS automation (Pro only)
cd ../xcodebuild
chmod +x *.sh

cd ../asc-api-helper
pip3 install -r requirements.txt
```

### Add to PATH

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$PATH:/path/to/axctl/skills/ax-helper"
export PATH="$PATH:/path/to/axctl/skills/xcodebuild"
export PATH="$PATH:/path/to/axctl/skills/asc-api-helper"
```

## Verification

### Check Installation

```bash
# Free tier
ax-helper --version

# Pro tier (after activation)
xcode-archive --help
asc-api --version
```

### Test Commands

```bash
# Desktop automation (free)
ax-helper query Finder

# iOS automation (pro)
xcode-archive --project Demo.xcodeproj --scheme Demo --dry-run
```

## Configuration

### Environment Variables

Create `~/.axctl/config` or set in your shell:

```bash
# App Store Connect (Pro)
export ASC_KEY_ID="YOUR_KEY_ID"
export ASC_ISSUER_ID="YOUR_ISSUER_ID"
export ASC_KEY_PATH="~/.axctl/keys/AuthKey.p8"

# Xcode (Pro)
export XCODE_DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"

# Desktop Automation (Free)
export AX_TIMEOUT=30
export AX_MAX_DEPTH=10
```

### License Storage

License keys are stored in: `~/.axctl/license.json`

Machine ID is generated from hardware UUID.

## Troubleshooting

### Accessibility Permission Denied

```bash
# Check current permissions
tccutil reset Accessibility com.apple.Terminal

# Then manually grant in System Settings
```

### Xcode Command Not Found

```bash
# Verify Xcode installation
xcode-select -p

# Set developer directory
sudo xcode-select --switch /Applications/Xcode.app
```

### License Activation Failed

```bash
# Check internet connection
curl -I https://api.axctl.dev/health

# Verify license key format
# Should be: AXCTL-PRO-{CUSTOMER_ID}-{HASH}

# Re-activate
axctl activate YOUR-LICENSE-KEY --force
```

### Python Package Issues

```bash
# Use venv for isolation
python3 -m venv ~/.axctl/venv
source ~/.axctl/venv/bin/activate
pip3 install -r requirements.txt
```

## Updating

### npm (Recommended)

```bash
npm update -g @axctl/core
```

### Manual

```bash
cd /path/to/axctl
git pull origin main
pip3 install -r requirements.txt --upgrade
```

## Uninstalling

```bash
# npm
npm uninstall -g @axctl/core

# Manual
rm -rf /path/to/axctl
rm -rf ~/.axctl
```

## Support

- **Documentation:** https://github.com/damediacoadmin/axctl
- **Email:** hello@axctl.dev
- **Issues:** https://github.com/damediacoadmin/axctl/issues

## Next Steps

- [Examples](./examples/) - See real-world automation scripts
- [API Reference](./docs/API.md) - Full command documentation
- [Contributing](./CONTRIBUTING.md) - Help improve AXCTL

