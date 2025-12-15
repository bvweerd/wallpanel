#!/bin/bash
# Script to download and convert Buienradar GIF frames to PNG (using tmpfs to prevent SSD wear)
# Extracts all frames from the GIF for animated radar display

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

curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/camera_proxy/camera.buienradar" \
  -o /tmp/buienradar.gif

# Remove old frames from tmpfs
rm -f /config/www/esphomefiles/buienradar_frame_*.png

# Extract all frames from GIF and resize to 314x220 (to tmpfs)
# The GIF typically has 10 frames showing radar movement
ffmpeg -loglevel error -y -i /tmp/buienradar.gif \
  -vf "scale=314:220" \
  /config/www/esphomefiles/buienradar_frame_%d.png

# Count number of frames extracted
FRAME_COUNT=$(ls /config/www/esphomefiles/buienradar_frame_*.png 2>/dev/null | wc -l)

# If less than 10 frames, duplicate the last frame to fill up to 10
if [ $FRAME_COUNT -lt 10 ] && [ $FRAME_COUNT -gt 0 ]; then
  echo "Only $FRAME_COUNT frames found, duplicating last frame to reach 10"
  LAST_FRAME="/config/www/esphomefiles/buienradar_frame_${FRAME_COUNT}.png"
  for i in $(seq $((FRAME_COUNT + 1)) 10); do
    cp "$LAST_FRAME" "/config/www/esphomefiles/buienradar_frame_${i}.png"
  done
  echo "Created 10 frames (${FRAME_COUNT} original + $((10 - FRAME_COUNT)) duplicates)"
elif [ $FRAME_COUNT -eq 0 ]; then
  echo "ERROR: No frames extracted from GIF!"
  exit 1
else
  echo "Extracted $FRAME_COUNT frames from buienradar GIF"
fi

echo "Buienradar frames updated (tmpfs)"
exit 0
