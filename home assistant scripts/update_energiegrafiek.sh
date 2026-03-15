#!/bin/bash
# Update energy detail chart for ESPHome display
# Place in /config/scripts/ in Home Assistant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.ha_secrets" ]; then
    source "$SCRIPT_DIR/.ha_secrets"
elif [ -f "/config/scripts/.ha_secrets" ]; then
    source "/config/scripts/.ha_secrets"
else
    echo "Error: .ha_secrets file not found" >&2
    exit 1
fi

if [ -z "$HA_TOKEN" ] || [ -z "$HA_URL" ]; then
    echo "Error: HA_TOKEN or HA_URL not set in .ha_secrets" >&2
    exit 1
fi

mkdir -p /config/www/esphomefiles

fetch_attrs() {
    curl -s \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json" \
        "$HA_URL/api/states/$1" \
        | jq '.attributes // {}'
}

levering=$(fetch_attrs "sensor.decc_summary_sensors_huidige_verbruiksprijs")
nordpool=$(fetch_attrs "sensor.nordpool_kwh_nl_eur_5_10_0")
teruglevering=$(fetch_attrs "sensor.decc_summary_sensors_huidige_terugleverprijs")
battery=$(fetch_attrs "sensor.battery_controller_schedule")

jq -n \
    --argjson levering     "$levering" \
    --argjson nordpool     "$nordpool" \
    --argjson teruglevering "$teruglevering" \
    --argjson battery      "$battery" \
    '{levering: $levering, nordpool: $nordpool, teruglevering: $teruglevering, battery: $battery}' \
| python3 /config/scripts/update_energiegrafiek.py

exit $?
