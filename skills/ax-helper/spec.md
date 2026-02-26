# AX Helper - macOS Accessibility Automation Tool

## Purpose
Lightweight Python CLI for automating macOS apps using Accessibility APIs (PyObjC). Returns structured JSON without screenshots - way more token-efficient than VLM-based automation.

## Requirements

### Dependencies
- Python 3.9+
- PyObjC (Cocoa, AppKit, ApplicationServices)
- No external screenshot/OCR libraries

### Commands

#### 1. `query` - Find UI elements
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

#### 2. `click` - Click an element
```bash
./ax-helper.py click <app_name> <element_path>
```

**Example:**
```bash
./ax-helper.py click Safari "window[0].toolbar[0].button[3]"
```

**Output:**
```json
{
  "success": true,
  "element": "window[0].toolbar[0].button[3]",
  "action": "click",
  "timestamp": "2026-02-24T13:30:00Z"
}
```

#### 3. `type` - Type text into focused element
```bash
./ax-helper.py type <app_name> <element_path> <text>
```

**Example:**
```bash
./ax-helper.py type Safari "window[0].textfield[0]" "https://example.com"
```

**Output:**
```json
{
  "success": true,
  "element": "window[0].textfield[0]",
  "action": "type",
  "text": "https://example.com",
  "timestamp": "2026-02-24T13:30:00Z"
}
```

#### 4. `get-value` - Read element value/text
```bash
./ax-helper.py get-value <app_name> <element_path>
```

**Output:**
```json
{
  "element": "window[0].textfield[0]",
  "value": "https://example.com",
  "role": "AXTextField",
  "enabled": true
}
```

#### 5. `list-apps` - Show running apps
```bash
./ax-helper.py list-apps
```

**Output:**
```json
{
  "apps": [
    {"name": "Safari", "pid": 12345, "bundle": "com.apple.Safari"},
    {"name": "Finder", "pid": 234, "bundle": "com.apple.finder"}
  ]
}
```

#### 6. `tree` - Dump full accessibility tree (debugging)
```bash
./ax-helper.py tree <app_name> [--max-depth 3]
```

**Output:** JSON tree of all AX elements

---

## Implementation Details

### Core Functions

1. **get_app_by_name(app_name)** - Find running app, return AXUIElement
2. **query_elements(app_element, filters)** - Search tree, return matching elements
3. **parse_element_path(path)** - Convert "window[0].button[3]" to element
4. **perform_action(element, action, params)** - AXPress, AXSetValue, etc.
5. **serialize_element(element)** - Convert AXUIElement to JSON dict

### Error Handling
- Return JSON with `"error": "message"` on failure
- Exit codes: 0=success, 1=error, 2=not found

### Performance
- Use AXUIElementCopyAttributeValue for attribute reads
- Cache app references within single command execution
- No tree walking unless necessary (use filters)

---

## File Structure

```
~/clawd/skills/ax-helper/
├── ax-helper.py          # Main CLI (argparse)
├── ax_core.py            # PyObjC AX wrapper functions
├── ax_search.py          # Element search/filtering
├── ax_actions.py         # Click, type, focus actions
├── requirements.txt      # pyobjc-framework-Cocoa
├── SKILL.md              # Usage documentation
└── examples/
    ├── safari-navigate.sh
    └── finder-open-folder.sh
```

---

## Testing Checklist

- [ ] `list-apps` shows running apps
- [ ] `query Safari` returns window elements
- [ ] `query Safari --filter role=AXButton` filters correctly
- [ ] `click` triggers button press
- [ ] `type` inserts text into text fields
- [ ] `get-value` reads text field content
- [ ] `tree` dumps full accessibility hierarchy
- [ ] Error handling for invalid app names
- [ ] Error handling for invalid element paths
- [ ] JSON output valid and parseable

---

## Usage in OpenClaw

```python
# Find and click Safari's address bar
result = exec("~/clawd/skills/ax-helper/ax-helper.py query Safari --filter role=AXTextField")
elements = json.loads(result)
address_bar = elements['elements'][0]['path']

# Click it
exec(f"~/clawd/skills/ax-helper/ax-helper.py click Safari {address_bar}")

# Type URL
exec(f"~/clawd/skills/ax-helper/ax-helper.py type Safari {address_bar} 'https://mykavabar.com'")

# Press Enter
exec(f"~/clawd/skills/ax-helper/ax-helper.py press Safari Return")
```

---

## Success Criteria

1. All commands return valid JSON
2. Can automate Safari (navigate to URL, click buttons)
3. Can automate Finder (open folders, select files)
4. Runs in <1 second for simple queries
5. No dependencies on screenshot/VLM tools
6. Works on macOS 13+ (Ventura, Sonoma, Sequoia)

---

**Output Location:** `~/clawd/skills/ax-helper/`
**Main Script:** `ax-helper.py` (executable, shebang `#!/usr/bin/env python3`)
