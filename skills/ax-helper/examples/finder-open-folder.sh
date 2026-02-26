#!/bin/bash
# Automate Finder to open a folder using AX Helper
# Usage: ./finder-open-folder.sh <folder_path>
# Example: ./finder-open-folder.sh "$HOME/Documents"

FOLDER="${1:-$HOME/Documents}"
AXHELPER="$HOME/clawd/skills/ax-helper/ax-helper.py"

# Check if Finder is running
if ! $AXHELPER list-apps | grep -q "Finder"; then
    echo "Opening Finder..."
    open -a Finder
    sleep 1
fi

# Focus Finder
osascript -e 'tell application "Finder" to activate'

echo "Finding folder in Finder window..."

# Query for table rows (file list)
RESULT=$($AXHELPER query Finder --filter role=AXTable 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$RESULT" ]; then
    echo "Could not find file list. Trying to open folder via open command as fallback..."
    open "$FOLDER"
    echo "Opened $FOLDER via Finder"
    exit 0
fi

# Alternative: Use open command which is more reliable for opening folders
echo "Opening folder via Finder: $FOLDER"
open "$FOLDER"

echo "Done! Finder should now be showing $FOLDER"
