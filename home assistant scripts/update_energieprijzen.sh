#!/bin/bash
# Update energy price chart for ESPHome display
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

# Ensure tmpfs directory exists
mkdir -p /config/www/esphomefiles

# Get sensor state with attributes
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  "$HA_URL/api/states/sensor.decc_summary_sensors_huidige_verbruiksprijs" \
  | jq '.attributes' \
  | python3 /config/scripts/update_energieprijzen.py

exit $?
