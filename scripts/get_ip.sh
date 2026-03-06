#!/bin/bash
# get_ip.sh - Display your public IP address
# Uses ipify.org - Trusted, open-source, no API key, no logging

set -e

# Get public IP with timeout and retry logic
IP=$(curl -s --max-time 5 'https://api.ipify.org?format=json' | grep -o '"ip":"[^"]*"' | cut -d'"' -f4)

if [ -z "$IP" ]; then
    echo "Failed to retrieve IP address"
    exit 1
fi

# Send notification
notify-send "🌐 Public IP Address" "$IP" --urgency=normal --icon=network-wired

echo "IP: $IP"
