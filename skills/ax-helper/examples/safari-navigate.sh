#!/bin/bash
# Navigate Safari to a URL using AX Helper
# Usage: ./safari-navigate.sh <url>
# Example: ./safari-navigate.sh "https://example.com"

URL="${1:-https://example.com}"
AXHELPER="$HOME/clawd/skills/ax-helper/ax-helper.py"

# Check if Safari is running
if ! $AXHELPER list-apps | grep -q "Safari"; then
    echo "Opening Safari..."
    open -a Safari
    sleep 1
fi

# Find Safari's address bar (AXTextField in toolbar)
echo "Finding address bar..."
ADDRESSBAR=$($AXHELPER query Safari --filter role=AXTextField 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['elements'][0]['path'])" 2>/dev/null)

if [ -z "$ADDRESSBAR" ]; then
    echo "Could not find address bar, trying alternate method..."
    ADDRESSBAR="window[0].toolbar[0].textfield[0]"
fi

echo "Clicking address bar: $ADDRESSBAR"
$AXHELPER click Safari "$ADDRESSBAR"

echo "Typing URL: $URL"
$AXHELPER type Safari "$ADDRESSBAR" "$URL"

echo "Pressing Return..."
$AXHELPER press Safari Return

echo "Done! Safari should now be navigating to $URL"
