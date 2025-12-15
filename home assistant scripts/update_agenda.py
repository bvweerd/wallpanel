#!/usr/bin/env python3
"""
Generate calendar agenda image for ESPHome display.
Place in /config/scripts/ in Home Assistant.
"""

import sys
import json
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Configuration
WIDTH = 314
HEIGHT = 220
OUTPUT_PATH = '/config/www/esphomefiles/agenda.png'
DAYS_TO_SHOW = 2
MAX_EVENTS = 6  # Maximum events to display

# Colors (matching theme)
COLOR_BG = (26, 26, 28)           # #1A1A1C background
COLOR_TEXT_PRIMARY = (255, 255, 255)   # White
COLOR_TEXT_SECONDARY = (156, 163, 175) # #9CA3AF gray
COLOR_ACCENT = (0, 122, 255)      # Blue accent

def get_font(size=10):
    """Get font. Try to use system font, fallback to default."""
    # Try multiple font paths (custom location first!)
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
            font = ImageFont.truetype(font_path, size)
            print(f"Loaded font {font_path} at size {size}", file=sys.stderr)
            return font
        except Exception as e:
            print(f"Failed to load {font_path}: {e}", file=sys.stderr)
            continue

    # If no TrueType font found, use bitmap font scaled
    print(f"WARNING: No TrueType font found, using default bitmap font (size will be ignored)", file=sys.stderr)
    return ImageFont.load_default()

def get_calendar_events():
    """Read calendar events from stdin (passed by HA automation)."""
    try:
        data = json.load(sys.stdin)
        # API returns array directly
        if isinstance(data, list):
            return data
        # Or object with events array
        elif isinstance(data, dict) and 'events' in data:
            return data['events']
        else:
            print(f"Unexpected data format: {type(data)}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return []

def truncate_text(draw, text, font, max_width):
    """Truncate text to fit within max_width, adding ... if needed."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    if text_width <= max_width:
        return text

    # Binary search for the right length
    left, right = 0, len(text)
    while left < right:
        mid = (left + right + 1) // 2
        test_text = text[:mid] + "..."
        bbox = draw.textbbox((0, 0), test_text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            left = mid
        else:
            right = mid - 1

    return text[:left] + "..." if left > 0 else "..."

def generate_image(events):
    """Generate the agenda image."""
    img = Image.new('RGB', (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_title = get_font(21)   # 14 × 1.5
    font_time = get_font(17)    # 11 × 1.5
    font_event = get_font(18)   # 12 × 1.5

    # Draw title
    y = 10
    draw.text((10, y), "Agenda", fill=COLOR_TEXT_PRIMARY, font=font_title)
    y += 32  # 25 × 1.5 ≈ 38, maar iets kleiner voor ruimte

    if not events:
        # No events
        draw.text((10, y), "Geen afspraken", fill=COLOR_TEXT_SECONDARY, font=font_event)
        return img

    # Filter and sort events for next DAYS_TO_SHOW days
    try:
        from zoneinfo import ZoneInfo
        local_tz = ZoneInfo('Europe/Amsterdam')
    except ImportError:
        import pytz
        local_tz = pytz.timezone('Europe/Amsterdam')

    now = datetime.now(local_tz)
    end_date = now + timedelta(days=DAYS_TO_SHOW)

    # Parse and filter events
    upcoming_events = []
    for event in events:
        try:
            # Parse start time - calendar API format
            start_str = event.get('start')
            if isinstance(start_str, dict):
                # Service call format: {"dateTime": "...", "date": "..."}
                start_str = start_str.get('dateTime') or start_str.get('date')

            if not start_str:
                print(f"No start time found in event: {event.get('summary', 'Unknown')}", file=sys.stderr)
                continue

            # Detect if all-day event
            is_all_day = 'T' not in start_str

            # Parse datetime
            if is_all_day:
                # All-day event (format: YYYY-MM-DD)
                start = datetime.fromisoformat(start_str + 'T00:00:00')
                if start.tzinfo is None:
                    start = start.replace(tzinfo=local_tz)
            else:
                # Timed event (format: YYYY-MM-DDTHH:MM:SS or with Z/+HH:MM)
                start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))

            # Convert to local timezone
            start_local = start.astimezone(local_tz)

            # For all-day events, show if date is today or in future
            if is_all_day:
                event_date = start_local.date()
                today = now.date()
                if event_date >= today and event_date <= end_date.date():
                    upcoming_events.append({
                        'summary': event.get('summary', 'Geen titel'),
                        'start': start_local,
                        'all_day': is_all_day
                    })
                    print(f"Added all-day event: {event.get('summary')} on {event_date}", file=sys.stderr)
            else:
                # For timed events, show if not ended yet (even if already started)
                # Parse end time to check if event is still ongoing
                end_str = event.get('end')
                if isinstance(end_str, dict):
                    end_str = end_str.get('dateTime') or end_str.get('date')

                if end_str and 'T' in end_str:
                    end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00')).astimezone(local_tz)
                    # Show if event hasn't ended yet and starts before our end date
                    if end_time >= now and start_local <= end_date:
                        upcoming_events.append({
                            'summary': event.get('summary', 'Geen titel'),
                            'start': start_local,
                            'all_day': is_all_day
                        })
                        print(f"Added timed event: {event.get('summary')} at {start_local} (ends {end_time})", file=sys.stderr)
                elif start_local >= now and start_local <= end_date:
                    # Fallback: no end time, just check start time
                    upcoming_events.append({
                        'summary': event.get('summary', 'Geen titel'),
                        'start': start_local,
                        'all_day': is_all_day
                    })
                    print(f"Added future event: {event.get('summary')} at {start_local}", file=sys.stderr)
        except Exception as e:
            print(f"Error parsing event {event.get('summary', 'Unknown')}: {e}", file=sys.stderr)
            continue

    # Sort by start time
    upcoming_events.sort(key=lambda x: x['start'])

    # Limit to MAX_EVENTS
    upcoming_events = upcoming_events[:MAX_EVENTS]

    if not upcoming_events:
        draw.text((10, y), "Geen afspraken", fill=COLOR_TEXT_SECONDARY, font=font_event)
        return img

    # Draw events
    current_date = None
    line_height = 36  # Was 42, nu kleiner voor compactere layout
    max_text_width = WIDTH - 90  # Iets meer ruimte voor grotere tijd

    for event in upcoming_events:
        # Check if we're out of vertical space
        if y > HEIGHT - 45:
            # Draw "..." to indicate more events
            draw.text((10, y), "...", fill=COLOR_TEXT_SECONDARY, font=font_event)
            break

        start = event['start']

        # Draw date header if it's a new day
        event_date = start.date()
        if current_date != event_date:
            if current_date is not None:
                y += 7  # 5 × 1.4

            current_date = event_date

            # Format date
            dagen = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
            dag_naam = dagen[start.weekday()]

            if event_date == now.date():
                date_str = "Vandaag"
            elif event_date == (now + timedelta(days=1)).date():
                date_str = "Morgen"
            else:
                date_str = f"{dag_naam} {start.day}/{start.month}"

            draw.text((10, y), date_str, fill=COLOR_ACCENT, font=font_time)
            y += 24  # 18 × 1.33

        # Draw time or "Hele dag"
        if event['all_day']:
            time_str = "Hele dag"
        else:
            time_str = start.strftime('%H:%M')

        draw.text((10, y), time_str, fill=COLOR_TEXT_SECONDARY, font=font_time)

        # Draw event summary (truncated if needed) - altijd op dezelfde x positie
        event_x = 110
        summary = truncate_text(draw, event['summary'], font_event, WIDTH - event_x - 10)
        draw.text((event_x, y - 2), summary, fill=COLOR_TEXT_PRIMARY, font=font_event)

        y += line_height

    return img

def main():
    """Main entry point."""
    events = get_calendar_events()
    img = generate_image(events)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Save image
    img.save(OUTPUT_PATH, 'PNG')
    print(f"Agenda image saved to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
