#!/bin/bash
# get_joke.sh - Display a random joke
# Uses official-joke-api.appspot.com - No auth required, HTTPS, CORS enabled

set -e

# Get a random joke
JOKE_DATA=$(curl -s --max-time 10 'https://official-joke-api.appspot.com/random_joke' 2>/dev/null)

if [ -z "$JOKE_DATA" ] || echo "$JOKE_DATA" | grep -q "error"; then
    notify-send "❌ Joke Error" "Could not fetch joke" --urgency=normal --icon=dialog-error
    exit 1
fi

# Parse setup and punchline (simple JSON parsing)
SETUP=$(echo "$JOKE_DATA" | grep -o '"setup":"[^"]*"' | cut -d'"' -f4)
PUNCHLINE=$(echo "$JOKE_DATA" | grep -o '"punchline":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SETUP" ] || [ -z "$PUNCHLINE" ]; then
    notify-send "❌ Joke Error" "Failed to parse joke data" --urgency=normal --icon=dialog-error
    exit 1
fi

# Show setup immediately
notify-send "😄 Joke" "$SETUP" --urgency=normal --icon=face-laugh

# Wait then show combined setup + punchline
(sleep 4 && notify-send "🎭 Punchline" "${SETUP}nn→ ${PUNCHLINE}" --urgency=normal --icon=face-laugh-beam) &

echo "$SETUP"
echo "$PUNCHLINE"
