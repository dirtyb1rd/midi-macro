#!/bin/bash
# system_info.sh - Display system resource usage
# No external API - pure system info

set -e

# Get CPU usage (average over 1 second)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if [ -z "$CPU_USAGE" ]; then
    CPU_USAGE="N/A"
fi

# Get memory usage
MEM_INFO=$(free -h | grep "^Mem:")
MEM_USED=$(echo "$MEM_INFO" | awk '{print $3}')
MEM_TOTAL=$(echo "$MEM_INFO" | awk '{print $2}')
MEM_PERCENT=$(echo "$MEM_INFO" | awk '{printf "%.1f", $3/$2 * 100.0}')

# Get disk usage for root
DISK_INFO=$(df -h / | tail -1)
DISK_USED=$(echo "$DISK_INFO" | awk '{print $3}')
DISK_TOTAL=$(echo "$DISK_INFO" | awk '{print $2}')
DISK_PERCENT=$(echo "$DISK_INFO" | awk '{print $5}')

# Get uptime
UPTIME=$(uptime -p | sed 's/up //')

# Format message
MESSAGE="CPU: ${CPU_USAGE}% | RAM: ${MEM_USED}/${MEM_TOTAL} (${MEM_PERCENT}%) | Disk: ${DISK_USED}/${DISK_TOTAL} (${DISK_PERCENT}) | Uptime: ${UPTIME}"

# Send notification
notify-send "💻 System Status" "$MESSAGE" --urgency=normal --icon=computer

echo "$MESSAGE"
