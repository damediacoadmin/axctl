# AX Helper - macOS Accessibility Automation Tool

Lightweight Python CLI for automating macOS apps using Accessibility APIs (PyObjC). Returns structured JSON without screenshots — way more token-efficient than VLM-based automation.

## Installation

```bash
cd ~/clawd/skills/ax-helper
pip install -r requirements.txt
```

**Requirements:**
- Python 3.9+
- macOS 13+ (Ventura, Sonoma, Sequoia)
- Accessibility permissions enabled (System Settings → Privacy & Security → Accessibility)

## Commands

### query - Find UI elements
```bash
./ax-helper.py query <app_name> [--filter role=button] [--filter title=Submit]
```

**Output:**
```json
{
  "app": "Safari",
  "pid": 12345,
  "elements": [
    {
      "role": "AXButton",
      "title": "Submit",
      "description": "Submit form",
      "enabled": true,
      "focused": false,
      "position": {"x": 100, "y": 200},
      "size": {"width": 80, "height": 30},
      "path": "window[0].toolbar[0].button[3]"
    }
  ]
}
```

### click - Click an element
```bash
./ax-helper.py click <app_name> <element_path>
```

**Example:**
```bash
./ax-helper.py click Safari "window[0].toolbar[0].button[3]"
```

### type - Type text into focused element
```bash
./ax-helper.py type <app_name> <element_path> <text>
```

**Example:**
```bash
./ax-helper.py type Safari "window[0].textfield[0]" "https://example.com"
```

### get-value - Read element value/text
```bash
./ax-helper.py get-value <app_name> <element_path>
```

### list-apps - Show running apps
```bash
./ax-helper.py list-apps
```

### tree - Dump full accessibility tree (debugging)
```bash
./ax-helper.py tree <app_name> [--max-depth 3]
```

### press - Press a key
```bash
./ax-helper.py press <app_name> <key>
```
Keys: Return, Enter, Tab, Escape, ArrowLeft, ArrowRight, etc.

## Usage in OpenClaw

Agents can call ax-helper directly via exec:

```python
# Find and click Safari's address bar
result = exec("~/clawd/skills/ax-helper/ax-helper.py query Safari --filter role=AXTextField")
elements = json.loads(result)
address_bar = elements['elements'][0]['path']

# Click it
exec(f"~/clawd/skills/ax-helper/ax-helper.py click Safari {address_bar}")

# Type URL
exec(f"~/clawd/skills/ax-helper/ax-helper.py type Safari {address_bar} 'https://mykavahar.com'")

# Press Enter
exec(f"~/clawd/skills/ax-helper/ax-helper.py press Safari Return")
```

## Common Patterns

### Navigate Safari to a URL
```bash
# 1. Find address bar
./ax-helper.py query Safari --filter role=AXTextField | jq '.elements[0].path'

# 2. Click address bar
./ax-helper.py click Safari "window[0].toolbar[0].textfield[0]"

# 3. Type URL
./ax-helper.py type Safari "window[0].toolbar[0].textfield[0]" "https://example.com"

# 4. Press Return
./ax-helper.py press Safari Return
```

See `examples/safari-navigate.sh` for the full script.

### Automate Finder
```bash
# List running Finder windows
./ax-helper.py query Finder --filter role=AXWindow

# Open a folder (double-click)
./ax-helper.py click Finder "window[0].scrollArea[0].table[0].row[5]"
```

See `examples/finder-open-folder.sh` for automation patterns.

## Troubleshooting

### "Application not found"
- Make sure the app is running
- Use `./ax-helper.py list-apps` to verify

### "Element not found"
- Check the element path is correct
- Run `./ax-helper.py tree <app_name>` to see the full hierarchy
- App may need to be in foreground

### "Permission denied" / "Cannot access accessibility"
- Grant Accessibility permissions:
  - System Settings → Privacy & Security → Accessibility
  - Add Terminal (or your Python interpreter)
  - Toggle enable

### No elements returned
- App may use custom UI elements
- Try removing filters to see all elements
- Use `tree` command to debug

### Performance slow
- Use specific filters (role, title) instead of querying everything
- Avoid deep tree queries when possible
