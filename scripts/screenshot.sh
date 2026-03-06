#!/bin/bash
# screenshot.sh - Take a screenshot with timestamp
# Uses maim (modern screenshot tool) or scrot as fallback

set -e

# Create screenshots directory if it doesn't exist
SCREENSHOT_DIR="$HOME/Pictures/Screenshots"
mkdir -p "$SCREENSHOT_DIR"

# Generate filename with timestamp
FILENAME="screenshot_$(date +%Y%m%d_%H%M%S).png"
FILEPATH="$SCREENSHOT_DIR/$FILENAME"

# Try different screenshot tools
if command -v maim &> /dev/null; then
    # maim is available (modern, better quality)
    maim "$FILEPATH"
elif command -v scrot &> /dev/null; then
    # scrot is available (classic)
    scrot "$FILEPATH"
elif command -v gnome-screenshot &> /dev/null; then
    # GNOME screenshot tool
    gnome-screenshot -f "$FILEPATH"
else
    notify-send "❌ Screenshot Error" "No screenshot tool found. Install maim, scrot, or gnome-screenshot." --urgency=critical --icon=dialog-error
    exit 1
fi

# Verify screenshot was taken
if [ -f "$FILEPATH" ]; then
    notify-send "📸 Screenshot Saved" "Saved to: $FILENAME" --urgency=normal --icon=camera-photo
    echo "Screenshot saved: $FILEPATH"
else
    notify-send "❌ Screenshot Failed" "Could not save screenshot" --urgency=critical --icon=dialog-error
    exit 1
fi
