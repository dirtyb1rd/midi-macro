#!/bin/bash
# get_weather.sh - Display current weather
# Uses wttr.in - Open source, trusted, no API key required

set -e

# Default location (can be overridden with argument)
LOCATION="${1:-Portland}"  # Change this to your city

# Get weather data with timeout
WEATHER=$(curl -s --max-time 10 "wttr.in/${LOCATION}?format=%l:+%c+%t+%w+%m" 2>/dev/null || echo "Weather unavailable")

if [ -z "$WEATHER" ] || [ "$WEATHER" = "Weather unavailable" ]; then
    echo "Failed to retrieve weather"
    notify-send "❌ Weather Error" "Could not fetch weather for $LOCATION" --urgency=normal --icon=dialog-error
    exit 1
fi

# Send notification
notify-send "🌤️ Weather: $LOCATION" "$WEATHER" --urgency=normal --icon=weather-clear

echo "$WEATHER"
