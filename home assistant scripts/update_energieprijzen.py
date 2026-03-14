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
BAR_HEIGHT = 21  # Half height, room for axis labels below
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
    """Get font. Try to use system font, fallback to default."""
    font_paths = [
        "/config/fonts/DejaVuSans.ttf",  # Custom font location in Home Assistant
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
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
        # If no timezone info, assume already Amsterdam local time
        if start.tzinfo is None:
            start = start.replace(tzinfo=local_tz)
        start_local = start.astimezone(local_tz)
        if win_start <= start_local <= win_end:
            visible.append({
                'start': start_local,
                'value': item['value']
            })

    if not visible:
        img = Image.new('RGB', (WIDTH, HEIGHT), COLOR_BG)
        return img

    # Calculate percentiles over all available data (not just visible window)
    values = sorted([p['value'] for p in all_prices if isinstance(p.get('value'), (int, float))])
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

    # Calculate bar width (using available width minus margins)
    num_bars = len(visible)
    available_width = WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    bar_width = available_width / num_bars  # Use float for precise positioning
    gap = 1

    y_offset = 4  # top margin, leaves room for axis labels below

    # Build color segments (contiguous runs of the same color)
    colors = [color_for(p['value']) for p in visible]
    segments = []
    seg_start = 0
    for i in range(1, num_bars + 1):
        if i == num_bars or colors[i] != colors[seg_start]:
            segments.append({'start': seg_start, 'end': i - 1, 'color': colors[seg_start]})
            seg_start = i

    # Draw bars first, then labels on top
    for i, price in enumerate(visible):
        x = LEFT_MARGIN + int(i * bar_width)
        x_end = LEFT_MARGIN + int((i + 1) * bar_width) - gap
        color = color_for(price['value'])
        draw.rectangle(
            [x, y_offset, x_end, y_offset + BAR_HEIGHT],
            fill=color
        )

    # Draw time-range labels centered inside colored segments
    for seg in segments:
        if seg['color'] == COLOR_MID:
            continue
        seg_left_px = LEFT_MARGIN + int(seg['start'] * bar_width)
        seg_right_px = LEFT_MARGIN + int((seg['end'] + 1) * bar_width)
        seg_width_px = seg_right_px - seg_left_px

        start_h = visible[seg['start']]['start'].hour
        end_h = (visible[seg['end']]['start'] + timedelta(hours=1)).hour
        label = f"{start_h}-{end_h}"

        f = get_font(21)
        bbox = draw.textbbox((0, 0), label, font=f)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        text_x = seg_left_px + (seg_width_px - text_w) // 2
        # Subtract bbox[1] to correct for ascender offset so text is truly centered
        text_y = y_offset + (BAR_HEIGHT - text_h) // 2 - bbox[1]
        draw.text((text_x, text_y), label, fill=(10, 10, 10), font=f)

    # Draw hour axis labels below bar (every whole hour)
    axis_font = get_font(10)
    label_y = y_offset + BAR_HEIGHT + 3
    for i, price in enumerate(visible):
        if price['start'].minute == 0:
            hour_str = f"{price['start'].hour:02d}"
            x = LEFT_MARGIN + int(i * bar_width)
            bbox = draw.textbbox((0, 0), hour_str, font=axis_font)
            text_width = bbox[2] - bbox[0]
            draw.text((x - text_width // 2, label_y), hour_str,
                     fill=COLOR_TEXT, font=axis_font)

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

    # Calculate exact position within hour
    if current_idx + 1 < len(visible):
        next_time = visible[current_idx + 1]['start']
        curr_time = visible[current_idx]['start']
        hour_duration = (next_time - curr_time).total_seconds()
        elapsed = (now - curr_time).total_seconds()
        within_frac = min(1.0, max(0.0, elapsed / hour_duration))
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
