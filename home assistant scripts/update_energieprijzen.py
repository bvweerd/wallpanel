#!/usr/bin/env python3
"""
Generate energy price bar chart image for ESPHome display.
Place in /config/scripts/ in Home Assistant.
"""

import sys
import json
import os
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# Configuration
WIDTH = 648  # 2 cards width (314 + 20 + 314)
HEIGHT = 50  # Top bar height
BAR_HEIGHT = 18
LABEL_HEIGHT = 12  # Height for hour labels
LEFT_MARGIN = 8  # Left margin to prevent label cutoff
RIGHT_MARGIN = 8  # Right margin
OUTPUT_PATH = '/config/www/esphomefiles/energieprijzen.png'

# Colors
COLOR_LOW = (34, 197, 94)     # #22c55e green
COLOR_MID = (209, 213, 219)   # #d1d5db gray
COLOR_HIGH = (239, 68, 68)    # #ef4444 red
COLOR_NOW = (0, 122, 255)     # blue indicator
COLOR_BG = (26, 26, 28)       # #1A1A1C background
COLOR_TEXT = (156, 163, 175)  # #9CA3AF gray text for labels

def get_font(size=10):
    """Get font for labels. Try to use system font, fallback to default."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        try:
            return ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()

def get_sensor_data():
    """Read sensor data from stdin (passed by HA automation)."""
    try:
        data = json.load(sys.stdin)
        return data
    except:
        # Fallback: return empty structure
        return {'net_prices_today': [], 'net_prices_tomorrow': []}

def generate_image(sensor_data):
    """Generate the energy price bar chart."""
    td = sensor_data.get('net_prices_today', [])
    tm = sensor_data.get('net_prices_tomorrow', [])

    # Handle None values (when tomorrow's prices aren't available yet)
    if td is None:
        td = []
    if tm is None:
        tm = []

    all_prices = td + tm

    if not all_prices:
        # No data: create blank image with message
        img = Image.new('RGB', (WIDTH, HEIGHT), COLOR_BG)
        return img

    # Filter to 24-hour window (4h past, 20h future)
    # Use local timezone-aware datetime
    try:
        from zoneinfo import ZoneInfo
        local_tz = ZoneInfo('Europe/Amsterdam')
    except ImportError:
        # Fallback for older Python versions
        import pytz
        local_tz = pytz.timezone('Europe/Amsterdam')
    now = datetime.now(local_tz)
    win_start = now - timedelta(hours=4)
    win_end = now + timedelta(hours=20)

    visible = []
    for item in all_prices:
        start = datetime.fromisoformat(item['start'].replace('Z', '+00:00'))
        # Convert to local timezone for comparison
        start_local = start.astimezone(local_tz)
        if win_start <= start_local <= win_end:
            visible.append({
                'start': start_local,
                'value': item['value']
            })

    if not visible:
        img = Image.new('RGB', (WIDTH, HEIGHT), COLOR_BG)
        return img

    # Calculate percentiles for color coding
    values = sorted([p['value'] for p in visible])
    n = len(values)
    p20 = values[int(0.20 * (n - 1))]
    p80 = values[int(0.80 * (n - 1))]

    def color_for(value):
        if value <= p20:
            return COLOR_LOW
        elif value >= p80:
            return COLOR_HIGH
        else:
            return COLOR_MID

    # Create image
    img = Image.new('RGB', (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)
    font = get_font(9)

    # Calculate bar width (using available width minus margins)
    num_bars = len(visible)
    available_width = WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    bar_width = available_width / num_bars  # Use float for precise positioning
    gap = 1

    # Draw bars (positioned to leave room for labels below)
    y_offset = 8  # Top margin
    for i, price in enumerate(visible):
        x = LEFT_MARGIN + int(i * bar_width)
        x_end = LEFT_MARGIN + int((i + 1) * bar_width) - gap
        color = color_for(price['value'])
        draw.rectangle(
            [x, y_offset, x_end, y_offset + BAR_HEIGHT],
            fill=color
        )

    # Draw hour labels below bars
    # Show label on every whole hour (minute == 0)
    label_y = y_offset + BAR_HEIGHT + 3
    for i, price in enumerate(visible):
        minute = price['start'].minute
        # Show label if this is a whole hour
        if minute == 0:
            hour_str = f"{price['start'].hour:02d}"
            x = LEFT_MARGIN + int((i + 0.5) * bar_width)
            # Center text at x position
            bbox = draw.textbbox((0, 0), hour_str, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text((x - text_width // 2, label_y), hour_str,
                     fill=COLOR_TEXT, font=font)

    # Debug: print current time and visible range
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}", file=sys.stderr)
    if visible:
        print(f"First visible: {visible[0]['start'].strftime('%Y-%m-%d %H:%M:%S %Z')}", file=sys.stderr)
        print(f"Last visible: {visible[-1]['start'].strftime('%Y-%m-%d %H:%M:%S %Z')}", file=sys.stderr)

    # Find current hour position
    current_idx = 0
    for i in range(len(visible) - 1):
        if visible[i]['start'] <= now < visible[i + 1]['start']:
            current_idx = i
            break

    # If we didn't find a match, check if we're past all times
    if current_idx == 0 and len(visible) > 0:
        if now >= visible[-1]['start']:
            current_idx = len(visible) - 1

    print(f"Current index: {current_idx}, time: {visible[current_idx]['start'].strftime('%H:%M')}", file=sys.stderr)

    # Calculate exact position within hour
    if current_idx + 1 < len(visible):
        next_time = visible[current_idx + 1]['start']
        curr_time = visible[current_idx]['start']
        hour_duration = (next_time - curr_time).total_seconds()
        elapsed = (now - curr_time).total_seconds()
        within_frac = min(1.0, max(0.0, elapsed / hour_duration))
        print(f"Within hour: {within_frac:.2f} ({elapsed:.0f}s / {hour_duration:.0f}s)", file=sys.stderr)
    else:
        within_frac = 0.5

    # Draw current time indicator (vertical line) - account for left margin
    # Thicker blue line (4px) to make it stand out
    now_x = LEFT_MARGIN + int((current_idx + within_frac) * bar_width)
    draw.line([(now_x, y_offset), (now_x, y_offset + BAR_HEIGHT)],
              fill=COLOR_NOW, width=4)

    return img

def main():
    """Main entry point."""
    sensor_data = get_sensor_data()
    img = generate_image(sensor_data)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Save image
    img.save(OUTPUT_PATH, 'PNG')
    print(f"Energy price chart saved to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
