#!/bin/bash
# Update camera snapshots for ESPHome display (using tmpfs to prevent SSD wear)
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

# Download camera 1 (deurbel)
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/camera_proxy/camera.deurbel_snapshots_sub" \
  -o /tmp/camera1_temp.jpg

# Download camera 2 (oprit)
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/camera_proxy/camera.camera_oprit_snapshots_sub" \
  -o /tmp/camera2_temp.jpg

# Convert and resize camera 1 to PNG (to tmpfs)
ffmpeg -loglevel error -y -i /tmp/camera1_temp.jpg \
  -vf "scale=314:220" \
  /config/www/esphomefiles/camera1.png

# Convert and resize camera 2 to PNG (to tmpfs)
ffmpeg -loglevel error -y -i /tmp/camera2_temp.jpg \
  -vf "scale=314:220" \
  /config/www/esphomefiles/camera2.png

echo "Camera snapshots updated (tmpfs)"
exit 0
