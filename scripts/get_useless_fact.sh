#!/bin/bash
# get_useless_fact.sh - Display a random useless but true fact
# Uses uselessfacts.jsph.pl - No auth required, educational/fun

set -e

# Get a random useless fact
FACT_DATA=$(curl -s --max-time 10 'https://uselessfacts.jsph.pl/random.json?language=en' 2>/dev/null)

if [ -z "$FACT_DATA" ] || echo "$FACT_DATA" | grep -q "error"; then
    notify-send "❌ Fact Error" "Could not fetch useless fact" --urgency=normal --icon=dialog-error
    exit 1
fi

# Parse the fact text
FACT=$(echo "$FACT_DATA" | grep -o '"text":"[^"]*"' | cut -d'"' -f4)

if [ -z "$FACT" ]; then
    notify-send "❌ Fact Error" "Failed to parse fact data" --urgency=normal --icon=dialog-error
    exit 1
fi

# Clean up HTML entities (basic)
FACT=$(echo "$FACT" | sed 's/&quot;/"/g; s/&#039;/'"'"'/g; s/&amp;/\&/g')

# Send notification
notify-send "🧠 Useless Fact" "$FACT" --urgency=normal --icon=dialog-information

echo "$FACT"
