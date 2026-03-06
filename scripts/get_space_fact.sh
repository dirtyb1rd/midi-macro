#!/bin/bash
# get_space_fact.sh - Display NASA Astronomy Picture of the Day info
# Uses NASA APOD API with DEMO_KEY - Official NASA API, educational use

set -e

# Get today's APOD data using DEMO_KEY (limited to 30 requests per hour per IP)
RESPONSE=$(curl -s --max-time 10 "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY" 2>/dev/null)

if [ -z "$RESPONSE" ] || echo "$RESPONSE" | grep -q "error"; then
    echo "Failed to retrieve space data"
    notify-send "❌ Space Data Error" "Could not fetch astronomy data" --urgency=normal --icon=dialog-error
    exit 1
fi

# Extract title and explanation (truncated)
TITLE=$(echo "$RESPONSE" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
EXPLANATION=$(echo "$RESPONSE" | grep -o '"explanation":"[^"]*"' | head -1 | cut -d'"' -f4 | cut -c1-200)

if [ -z "$TITLE" ]; then
    TITLE="Space Fact"
fi

if [ -z "$EXPLANATION" ]; then
    EXPLANATION="Check out today's astronomy picture!"
fi

# Add ellipsis if truncated
if [ ${#EXPLANATION} -ge 200 ]; then
    EXPLANATION="${EXPLANATION}..."
fi

# Send notification
notify-send "🚀 NASA: $TITLE" "$EXPLANATION" --urgency=normal --icon=applications-science

echo "Title: $TITLE"
echo "Explanation: $EXPLANATION"
