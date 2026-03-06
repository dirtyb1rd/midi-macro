#!/bin/bash
# copy_quote.sh - Copy an inspirational quote to clipboard
# Uses quotable.io - Free, no auth, educational

set -e

# Get a random quote
QUOTE_DATA=$(curl -s --max-time 10 'https://api.quotable.io/random' 2>/dev/null)

if [ -z "$QUOTE_DATA" ] || echo "$QUOTE_DATA" | grep -q "error"; then
    notify-send "❌ Quote Error" "Could not fetch quote" --urgency=normal --icon=dialog-error
    exit 1
fi

# Parse quote and author
QUOTE=$(echo "$QUOTE_DATA" | grep -o '"content":"[^"]*"' | cut -d'"' -f4)
AUTHOR=$(echo "$QUOTE_DATA" | grep -o '"author":"[^"]*"' | cut -d'"' -f4)

if [ -z "$QUOTE" ] || [ -z "$AUTHOR" ]; then
    notify-send "❌ Quote Error" "Failed to parse quote data" --urgency=normal --icon=dialog-error
    exit 1
fi

# Format for clipboard
FULL_QUOTE="\"$QUOTE\" - $AUTHOR"

# Copy to clipboard using available tool
if command -v wl-copy &> /dev/null; then
    # Wayland
    echo "$FULL_QUOTE" | wl-copy
elif command -v xclip &> /dev/null; then
    # X11 with xclip
    echo "$FULL_QUOTE" | xclip -selection clipboard
elif command -v xsel &> /dev/null; then
    # X11 with xsel
    echo "$FULL_QUOTE" | xsel --clipboard --input
else
    notify-send "❌ Clipboard Error" "No clipboard tool found. Install wl-copy, xclip, or xsel." --urgency=critical --icon=dialog-error
    exit 1
fi

# Send notification
notify-send "📋 Quote Copied" "\"$QUOTE\" - $AUTHOR" --urgency=normal --icon=edit-copy

echo "Copied to clipboard: $FULL_QUOTE"
