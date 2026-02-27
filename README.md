# AXCTL - macOS Automation CLI

Command-line automation for macOS that saves **$3,000/year** in time and **98%** on AI token costs.

## 🚀 Features

- **Xcode Build Automation** - Build, archive, export, and upload iOS apps from the command line
- **App Store Connect API** - Manage apps, TestFlight, and submissions programmatically  
- **Accessibility Helper** - Control any macOS app via native Accessibility APIs (no screenshots needed)
- **Token Efficient** - Uses 150 tokens/action vs 7,800 for Vision AI (98% reduction)

## 📦 Installation

### Recommended: Local Install (no permissions needed)
```bash
cd ~
npm install @axctl/core

# Then use commands with full path:
~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py query "Safari"

# Or create aliases for convenience:
alias ax-helper="~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py"
alias asc-api="~/node_modules/@axctl/core/skills/asc-api-helper/asc-api-helper.py"
```

### Alternative: Global Install (requires sudo)
```bash
sudo npm install -g @axctl/core

# Then use commands directly:
ax-helper query "Safari"
axctl help
```

## ⚡ Quickstart

### Desktop Automation (Free - No License Required)

```bash
# Query any Mac app's UI
~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py query "Safari"

# Click a button
~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py click "button:Submit"

# Type into a field
~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py type "textfield:Email" "user@example.com"

# Press a key
~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py press "Enter"
```

**Tip:** Create an alias for easier use:
```bash
alias ax-helper="~/node_modules/@axctl/core/skills/ax-helper/ax-helper.py"
```

### iOS Automation (Pro - License Required)

```bash
# Get your license from https://axctl.dev
# Note: License validation will be added in a future update
# For now, tools work without activation for testing

# Build & archive your app
~/node_modules/@axctl/core/skills/xcodebuild/xcode-archive.sh \
  --project MyApp.xcodeproj \
  --scheme MyApp \
  --configuration Release

# Export for App Store
~/node_modules/@axctl/core/skills/xcodebuild/xcode-export.sh \
  --archive MyApp.xcarchive \
  --method app-store

# Upload to TestFlight
~/node_modules/@axctl/core/skills/xcodebuild/xcode-upload.sh \
  --ipa MyApp.ipa \
  --asc-key-id YOUR_KEY_ID
```

## 📚 Usage Examples

### Example 1: Automated iOS Build Pipeline

```bash
#!/bin/bash
# Full iOS build + TestFlight upload in one command

# 1. Archive
xcode-archive \
  --project MyApp.xcodeproj \
  --scheme "MyApp" \
  --configuration Release \
  --output build/MyApp.xcarchive

# 2. Export IPA
xcode-export \
  --archive build/MyApp.xcarchive \
  --method app-store \
  --output build/MyApp.ipa

# 3. Upload to TestFlight
xcode-upload \
  --ipa build/MyApp.ipa \
  --asc-key-id ABC123DEF456 \
  --asc-issuer-id 12345678-1234-1234-1234-123456789012

echo "✅ Build uploaded to TestFlight!"
```

### Example 2: Browser Automation (Token-Efficient)

```bash
# Fill a web form (150 tokens instead of 7,800 with Vision AI)
ax-helper query "Google Chrome"
ax-helper type "textfield:Email" "user@example.com"
ax-helper type "textfield:Password" "secure-password"
ax-helper click "button:Sign in"
```

### Example 3: Check TestFlight Status

```bash
# List all TestFlight builds
asc-api list-builds --app-id 1234567890

# Get specific build info
asc-api build-info --build-id abc123def456
```

## 🆓 Pricing

| Feature | Free | Monthly | Annual | Lifetime |
|---------|------|---------|--------|----------|
| **Price** | $0 | $9/mo | $69/year | $179 once |
| **Desktop automation** | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| **Xcode build automation** | ❌ | ✅ | ✅ | ✅ |
| **App Store Connect API** | ❌ | ✅ | ✅ | ✅ |
| **Machine limit** | N/A | 1 machine | 3 machines | 5 machines |
| **Updates** | N/A | ✅ | ✅ | ✅ Forever |

**Best Value:** Lifetime ($179) = 2.6 years of annual, then free forever 🚀

## 💡 Why AXCTL?

**Token Savings Example:**  
At 20M tokens/month ($2 per 1M):

- Vision AI: **$480/year** 💸  
- AXCTL: **$9/year** ✨  
- **Savings: $471/year**

**Time Savings:**  
30 hours/year automation × $100/hr = **$3,000/year**

**Total Annual Value: $3,471**  
**Cost: $69/year**  
**ROI: 50x** 🚀

## 📖 Documentation

- [Xcode Build Skill](./skills/xcodebuild/SKILL.md)
- [App Store Connect API](./skills/asc-api-helper/SKILL.md)
- [AX Helper (Desktop Automation)](./skills/ax-helper/SKILL.md)

## 🔗 Links

- **Website:** https://axctl.dev
- **License API:** https://github.com/damediacoadmin/axctl/tree/main/api
- **Landing Page:** https://github.com/damediacoadmin/axctl/tree/main/landing

## 📄 License

Proprietary - Free tier is unlimited for personal use. Pro features require a license.

---

Built by [David Miller](https://github.com/damediacoadmin) | [DAMedia Co](https://damedia.co)
