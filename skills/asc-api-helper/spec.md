# ASC API Helper - App Store Connect API CLI

## Purpose
Python CLI for interacting with Apple's App Store Connect API. Provides JWT authentication and commands for managing apps, builds, and TestFlight distribution.

## Requirements

### Dependencies
- Python 3.9+
- PyJWT (for JWT token generation)
- cryptography (for .p8 key handling)
- requests (for HTTP API calls)

### Authentication
Uses App Store Connect API Key (.p8 file) with:
- Key ID (from filename or config)
- Issuer ID (from App Store Connect)
- Private key (.p8 file path)

### Commands

#### 1. `auth-test` - Verify API credentials
```bash
./asc-api-helper.py auth-test --key-id ABC123 --issuer-id xyz-issuer --key-file ~/Keys/AuthKey_ABC123.p8
```

**Output:**
```json
{
  "success": true,
  "issuer_id": "xyz-issuer",
  "key_id": "ABC123",
  "token_expires": "2026-02-25T15:30:00Z"
}
```

#### 2. `list-apps` - List all apps in account
```bash
./asc-api-helper.py list-apps --key-id ABC123 --issuer-id xyz --key-file ~/Keys/AuthKey.p8
```

**Output:**
```json
{
  "apps": [
    {
      "id": "1234567890",
      "bundle_id": "com.example.app",
      "name": "My App",
      "sku": "MYAPP001",
      "platform": "IOS"
    }
  ],
  "count": 1
}
```

#### 3. `list-builds` - List builds for an app
```bash
./asc-api-helper.py list-builds --app-id 1234567890 --limit 10 [auth flags]
```

**Output:**
```json
{
  "builds": [
    {
      "id": "build-uuid",
      "version": "1.0.0",
      "build_number": "42",
      "upload_date": "2026-02-25T10:00:00Z",
      "processing_state": "VALID",
      "expired": false,
      "testflight_enabled": true
    }
  ],
  "count": 1
}
```

#### 4. `get-app` - Get detailed app info
```bash
./asc-api-helper.py get-app --app-id 1234567890 [auth flags]
```

**Output:**
```json
{
  "id": "1234567890",
  "bundle_id": "com.example.app",
  "name": "My App",
  "sku": "MYAPP001",
  "primary_locale": "en-US",
  "available_in_new_territories": true,
  "content_rights_declaration": "USES_THIRD_PARTY_CONTENT"
}
```

#### 5. `upload-build` - Upload build to TestFlight (via transporter)
```bash
./asc-api-helper.py upload-build --ipa-path ~/Desktop/app.ipa [auth flags]
```

**Note:** Uses `xcrun altool --upload-app` or Apple Transporter under the hood.

**Output:**
```json
{
  "success": true,
  "ipa_path": "/Users/dave/Desktop/app.ipa",
  "upload_id": "xyz-upload-123",
  "message": "Upload successful. Build will appear in App Store Connect shortly."
}
```

---

## Implementation Details

### JWT Token Generation
```python
import jwt
import time
from cryptography.hazmat.primitives import serialization

def generate_token(key_id: str, issuer_id: str, key_file: str) -> str:
    # Load private key
    with open(key_file, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    
    # Generate JWT (valid for 20 minutes)
    now = int(time.time())
    payload = {
        'iss': issuer_id,
        'exp': now + 1200,  # 20 minutes
        'aud': 'appstoreconnect-v1',
    }
    
    headers = {
        'alg': 'ES256',
        'kid': key_id,
        'typ': 'JWT',
    }
    
    return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
```

### API Base URL
```
https://api.appstoreconnect.apple.com/v1
```

### Common Headers
```python
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
}
```

### Error Handling
- Return JSON with `"error": "message"` on failure
- Exit codes: 0=success, 1=error, 2=auth failure

---

## File Structure

```
~/clawd/skills/asc-api-helper/
├── asc-api-helper.py      # Main CLI (argparse)
├── asc_auth.py            # JWT token generation
├── asc_api.py             # API client functions
├── requirements.txt       # PyJWT, cryptography, requests
├── SKILL.md               # Usage documentation
└── examples/
    └── upload-to-testflight.sh
```

---

## Testing Checklist

- [ ] `auth-test` generates valid JWT token
- [ ] `list-apps` returns apps from account
- [ ] `list-builds` returns builds for specific app
- [ ] `get-app` returns app details
- [ ] Error handling for invalid credentials
- [ ] Error handling for network failures
- [ ] JSON output valid and parseable

---

## Usage in OpenClaw

```python
# List apps in account
result = exec("~/clawd/skills/asc-api-helper/asc-api-helper.py list-apps --key-id ABC --issuer-id xyz --key-file ~/Keys/AuthKey.p8")
apps = json.loads(result)

# Get builds for MyKavaBar
result = exec("~/clawd/skills/asc-api-helper/asc-api-helper.py list-builds --app-id 6759386927 --limit 5 [auth]")
builds = json.loads(result)
```

---

## Success Criteria

1. All commands return valid JSON
2. JWT authentication works with real .p8 key
3. Can list apps and builds from real ASC account
4. Runs in <5 seconds for API calls
5. Clear error messages for common failures

---

**Output Location:** `~/clawd/skills/asc-api-helper/`
**Main Script:** `asc-api-helper.py` (executable, shebang `#!/usr/bin/env python3`)
