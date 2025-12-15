#!/bin/bash
# Update agenda image for ESPHome display
# Place in /config/scripts/ in Home Assistant

# Load secrets from file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.ha_secrets" ]; then
    source "$SCRIPT_DIR/.ha_secrets"
elif [ -f "/config/scripts/.ha_secrets" ]; then
    source "/config/scripts/.ha_secrets"
else
    echo "Error: .ha_secrets file not found" >&2
    echo "Please copy .ha_secrets.example to .ha_secrets and fill in your credentials" >&2
    exit 1
fi

# Verify required variables are set
if [ -z "$HA_TOKEN" ] || [ -z "$HA_URL" ]; then
    echo "Error: HA_TOKEN or HA_URL not set in .ha_secrets" >&2
    exit 1
fi

CALENDAR_ENTITY="calendar.gezamenlijke_agenda"

# Ensure tmpfs directory exists
mkdir -p /config/www/esphomefiles

# Get calendar events for next 2 days using Python (BusyBox date doesn't support -d)
read START_DATE END_DATE <<< $(python3 -c "
from datetime import datetime, timedelta
now = datetime.now()
end = now + timedelta(days=2)
print(now.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
")

# Debug: show dates
echo "START_DATE: $START_DATE" >&2
echo "END_DATE: $END_DATE" >&2

# Use calendar list events API instead of service call
# Format: /api/calendars/<entity_id>?start=<start>&end=<end>
RESPONSE=$(curl -s -X GET \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  "$HA_URL/api/calendars/$CALENDAR_ENTITY?start=$START_DATE&end=$END_DATE")

# Debug: show raw response
echo "Raw API response:" >&2
echo "$RESPONSE" | head -20 >&2

# Pass events array directly to Python
echo "$RESPONSE" | python3 /config/scripts/update_agenda.py

exit $?
