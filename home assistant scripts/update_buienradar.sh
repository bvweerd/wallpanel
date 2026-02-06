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

# Extract 5 frames from GIF (every 2nd frame) and resize to 200x140 for better performance
# Original GIF typically has 10 frames, we select frames 0,2,4,6,8 (becomes 1-5)
ffmpeg -loglevel error -y -i /tmp/buienradar.gif \
  -vf "select='not(mod(n\,2))',scale=200:140" -vsync vfr \
  /config/www/esphomefiles/buienradar_frame_%d.png

# Count number of frames extracted
FRAME_COUNT=$(ls /config/www/esphomefiles/buienradar_frame_*.png 2>/dev/null | wc -l)

# If less than 5 frames, duplicate the last frame to fill up to 5
if [ $FRAME_COUNT -lt 5 ] && [ $FRAME_COUNT -gt 0 ]; then
  echo "Only $FRAME_COUNT frames found, duplicating last frame to reach 5"
  LAST_FRAME="/config/www/esphomefiles/buienradar_frame_${FRAME_COUNT}.png"
  for i in $(seq $((FRAME_COUNT + 1)) 5); do
    cp "$LAST_FRAME" "/config/www/esphomefiles/buienradar_frame_${i}.png"
  done
  echo "Created 5 frames (${FRAME_COUNT} original + $((5 - FRAME_COUNT)) duplicates)"
elif [ $FRAME_COUNT -eq 0 ]; then
  echo "ERROR: No frames extracted from GIF!"
  exit 1
else
  echo "Extracted $FRAME_COUNT frames from buienradar GIF (200x140)"
fi

echo "Buienradar frames updated (5 frames, 200x140)"
exit 0
