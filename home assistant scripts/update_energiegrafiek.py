#!/usr/bin/env python3
"""
Generate energy price detail chart image for ESPHome display.
Place in /config/scripts/ in Home Assistant.
Uses only Pillow (no matplotlib needed).

Primary axis (left):   levering prijs, nordpool marktprijs, teruglevering, predicted
Secondary axis (right): batterij vermogen (kW), batterij SoC (kWh)
"""

import sys
import json
import os
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# ── Canvas ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 984, 480
OUTPUT_PATH   = '/config/www/esphomefiles/energiegrafiek.png'

# ── Plot area margins ────────────────────────────────────────────────────────
LEFT   = 80   # room for left Y-axis labels
RIGHT  = 62   # room for right Y-axis labels
TOP    = 68   # room for legend (2 rows × ~26px + padding)
BOTTOM = 32   # room for X-axis labels
PLOT_W = WIDTH  - LEFT - RIGHT   # 842 px
PLOT_H = HEIGHT - TOP  - BOTTOM  # 380 px

# ── Data ranges ──────────────────────────────────────────────────────────────
Y1_MIN, Y1_MAX = -0.05, 0.50   # EUR/kWh  (primary / left)
Y2_MIN, Y2_MAX = -1.50, 2.50   # kW / kWh (secondary / right)

# ── Colors ───────────────────────────────────────────────────────────────────
BG          = (26,  26,  28)
GRID        = (42,  42,  46)
SPINE       = (63,  63,  70)
TEXT        = (156, 163, 175)
TEXT_BRIGHT = (209, 213, 219)
NOW_LINE    = (229, 231, 235)

C_NORDPOOL       = (107, 114, 128)
C_TERUGLEVERING  = ( 59, 130, 246)
C_PREDICTED      = ( 34, 197,  94)
C_BAT_POWER      = (249, 115,  22)
C_BAT_SOC        = (148, 163, 184)

# Levering thresholds (matching ApexCharts config)
C_LOW  = ( 55, 255,   0)   # < 0.20 EUR/kWh
C_MID  = (  0, 128, 255)   # 0.20 – 0.30
C_HIGH = (255,   0,  51)   # > 0.30
T_MID, T_HIGH = 0.20, 0.30


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_font(size=14):
    paths = [
        "/config/fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def get_local_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo('Europe/Amsterdam')
    except ImportError:
        import pytz
        return pytz.timezone('Europe/Amsterdam')


def parse_price_series(attrs, today_key, tomorrow_key):
    today    = attrs.get(today_key)    or []
    tomorrow = attrs.get(tomorrow_key) or []
    result = []
    for item in (today + tomorrow):
        raw_t = (item.get('start') or item.get('time')
                 or item.get('start_time') or item.get('begin'))
        raw_v = (item.get('value') or item.get('price')
                 or item.get('net') or item.get('v') or item.get('y') or 0)
        if raw_t is None:
            continue
        try:
            if isinstance(raw_t, (int, float)):
                ts = datetime.fromtimestamp(raw_t / 1000, tz=timezone.utc)
            else:
                ts = datetime.fromisoformat(str(raw_t).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            result.append((ts, float(raw_v)))
        except Exception:
            continue
    result.sort(key=lambda x: x[0])
    return result


def parse_battery_series(starts_raw, values_raw, local_tz):
    result = []
    for s, v in zip(starts_raw or [], values_raw or []):
        try:
            ts = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            result.append((ts.astimezone(local_tz), float(v)))
        except Exception:
            continue
    result.sort(key=lambda x: x[0])
    return result


def threshold_color(v):
    if v < T_MID:
        return C_LOW
    elif v < T_HIGH:
        return C_MID
    return C_HIGH


# ── Coordinate transforms ────────────────────────────────────────────────────

def make_tx(x_start, total_sec):
    def tx(ts):
        frac = max(0.0, min(1.0, (ts - x_start).total_seconds() / total_sec))
        return LEFT + int(frac * PLOT_W)
    return tx


def make_ty(y_min, y_max):
    span = y_max - y_min
    def ty(val):
        frac = max(0.0, min(1.0, (val - y_min) / span))
        return TOP + int((1.0 - frac) * PLOT_H)
    return ty


# ── Drawing primitives ───────────────────────────────────────────────────────

def draw_dashed_vline(draw, x, y0, y1, color, dash=6, gap=5, width=1):
    y = y0
    while y < y1:
        draw.line([(x, y), (x, min(y + dash, y1))], fill=color, width=width)
        y += dash + gap


def draw_step_line(draw, times, values, color_fn, tx, ty, lw=3):
    pts = [(tx(t), ty(v), v) for t, v in zip(times, values)]
    for i in range(len(pts) - 1):
        x0, y0, v0 = pts[i]
        x1, y1, _  = pts[i + 1]
        col = color_fn(v0)
        draw.line([(x0, y0), (x1, y0)], fill=col, width=lw)
        draw.line([(x1, y0), (x1, y1)], fill=col, width=lw)


def draw_step_area(overlay_draw, times, values, tx, ty, fill_rgba):
    y_zero = ty(0)
    for i in range(len(times) - 1):
        x0 = tx(times[i])
        x1 = tx(times[i + 1])
        yv = ty(values[i])
        top_y    = min(yv, y_zero)
        bottom_y = max(yv, y_zero)
        if x1 > x0:
            overlay_draw.rectangle([x0, top_y, x1 - 1, bottom_y], fill=fill_rgba)


def draw_dashed_step_line(draw, times, values, color, tx, ty, lw=2, dash=6, gap=5):
    for i in range(len(times) - 1):
        x0, y0 = tx(times[i]),     ty(values[i])
        x1     = tx(times[i + 1])
        y1     = ty(values[i + 1])
        # Dashed horizontal
        x = x0
        on = True
        while x < x1:
            xe = min(x + (dash if on else gap), x1)
            if on:
                draw.line([(x, y0), (xe, y0)], fill=color, width=lw)
            x = xe
            on = not on
        # Vertical connector
        draw.line([(x1, y0), (x1, y1)], fill=color, width=lw)


def text_center(draw, x, y, text, font, color):
    bb = draw.textbbox((0, 0), text, font=font)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((x - w // 2, y - bb[1]), text, fill=color, font=font)


def text_right(draw, x, y, text, font, color):
    bb = draw.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    draw.text((x - w, y - bb[1]), text, fill=color, font=font)


# ── Chart drawing ────────────────────────────────────────────────────────────

def draw_chart(data):
    local_tz  = get_local_tz()
    now       = datetime.now(local_tz)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    x_start   = day_start
    total_sec = 48 * 3600

    tx  = make_tx(x_start, total_sec)
    ty1 = make_ty(Y1_MIN, Y1_MAX)
    ty2 = make_ty(Y2_MIN, Y2_MAX)

    lev_attrs  = data.get('levering')      or {}
    np_attrs   = data.get('nordpool')      or {}
    tl_attrs   = data.get('teruglevering') or {}
    bat_attrs  = data.get('battery')       or {}

    levering      = parse_price_series(lev_attrs, 'net_prices_today', 'net_prices_tomorrow')
    nordpool      = parse_price_series(np_attrs,  'raw_today',        'raw_tomorrow')
    teruglevering = parse_price_series(tl_attrs,  'net_prices_today', 'net_prices_tomorrow')

    bat_starts = bat_attrs.get('step_start_times_iso') or []
    bat_power  = parse_battery_series(bat_starts, bat_attrs.get('power_schedule_kw'),        local_tz)
    bat_soc    = parse_battery_series(bat_starts, bat_attrs.get('soc_schedule_kwh'),         local_tz)
    predicted  = parse_battery_series(bat_starts, bat_attrs.get('price_forecast_predicted'), local_tz)

    font    = get_font(14)
    font_sm = get_font(12)

    # ── Base image ────────────────────────────────────────────────────────────
    img  = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # ── Horizontal grid lines (primary Y ticks) ───────────────────────────────
    y1_ticks = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    for v in y1_ticks:
        y = ty1(v)
        if TOP <= y <= TOP + PLOT_H:
            draw.line([(LEFT, y), (LEFT + PLOT_W, y)], fill=GRID, width=1)

    # ── Vertical grid lines (every 2h) ────────────────────────────────────────
    for h in range(0, 49, 2):
        x = tx(day_start + timedelta(hours=h))
        draw.line([(x, TOP), (x, TOP + PLOT_H)], fill=GRID, width=1)

    # ── Plot border ───────────────────────────────────────────────────────────
    draw.rectangle([LEFT, TOP, LEFT + PLOT_W, TOP + PLOT_H], outline=SPINE, width=1)

    # ── Nordpool area fill (RGBA overlay) ────────────────────────────────────
    if len(nordpool) >= 2:
        overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        t_np = [p for p, _ in nordpool]
        v_np = [v for _, v in nordpool]
        t_np.append(t_np[-1] + timedelta(hours=1)); v_np.append(v_np[-1])
        draw_step_area(od, t_np, v_np, tx, ty1, (*C_NORDPOOL, 28))
        img  = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

    # ── Series ────────────────────────────────────────────────────────────────

    if len(nordpool) >= 2:
        t = [p for p, _ in nordpool]; v = [x for _, x in nordpool]
        t.append(t[-1] + timedelta(hours=1)); v.append(v[-1])
        draw_step_line(draw, t, v, lambda _: C_NORDPOOL, tx, ty1, lw=3)

    if len(teruglevering) >= 2:
        t = [p for p, _ in teruglevering]; v = [x for _, x in teruglevering]
        t.append(t[-1] + timedelta(hours=1)); v.append(v[-1])
        draw_step_line(draw, t, v, lambda _: C_TERUGLEVERING, tx, ty1, lw=4)

    if len(predicted) >= 2:
        t = [p for p, _ in predicted]; v = [x for _, x in predicted]
        draw_dashed_step_line(draw, t, v, C_PREDICTED, tx, ty1, lw=2)

    if len(bat_soc) >= 2:
        t = [p for p, _ in bat_soc]; v = [x for _, x in bat_soc]
        draw_dashed_step_line(draw, t, v, C_BAT_SOC, tx, ty2, lw=1)

    if len(bat_power) >= 2:
        t = [p for p, _ in bat_power]; v = [x for _, x in bat_power]
        draw_step_line(draw, t, v, lambda _: C_BAT_POWER, tx, ty2, lw=2)

    if len(levering) >= 2:
        t = [p for p, _ in levering]; v = [x for _, x in levering]
        t.append(t[-1] + timedelta(hours=1)); v.append(v[-1])
        draw_step_line(draw, t, v, threshold_color, tx, ty1, lw=4)

    # ── "Nu" marker ───────────────────────────────────────────────────────────
    x_now = tx(now)
    draw.line([(x_now, TOP), (x_now, TOP + PLOT_H)], fill=NOW_LINE, width=2)

    # ── Dag-scheiding ─────────────────────────────────────────────────────────
    x_day2 = tx(day_start + timedelta(hours=24))
    draw_dashed_vline(draw, x_day2, TOP, TOP + PLOT_H, SPINE, dash=6, gap=5)
    draw.text((x_day2 + 4, TOP + 3), "morgen", fill=TEXT, font=font_sm)

    # ── Y-axis labels links (EUR/kWh) ─────────────────────────────────────────
    draw.text((2, TOP + PLOT_H // 2 - 26), "EUR/", fill=TEXT, font=font_sm)
    draw.text((2, TOP + PLOT_H // 2 - 12), "kWh",  fill=TEXT, font=font_sm)
    for v in y1_ticks:
        y = ty1(v)
        if TOP <= y <= TOP + PLOT_H:
            text_right(draw, LEFT - 5, y - 7, f"{v:.2f}", font, TEXT)

    # ── Y-axis labels rechts (kW/kWh) ────────────────────────────────────────
    xr = LEFT + PLOT_W
    draw.text((xr + 4, TOP + PLOT_H // 2 - 26), "kW/",  fill=TEXT, font=font_sm)
    draw.text((xr + 4, TOP + PLOT_H // 2 - 12), "kWh",  fill=TEXT, font=font_sm)
    for v in [-1.0, 0.0, 1.0, 2.0]:
        y = ty2(v)
        if TOP <= y <= TOP + PLOT_H:
            draw.text((xr + 5, y - 7), f"{v:.0f}", fill=TEXT, font=font)

    # ── X-axis labels (every 2h) ──────────────────────────────────────────────
    y_xlbl = TOP + PLOT_H + 6
    for h in range(0, 49, 2):
        t = day_start + timedelta(hours=h)
        x = tx(t)
        text_center(draw, x, y_xlbl, f"{t.hour:02d}", font_sm, TEXT)

    # ── Legend (2 rows) ───────────────────────────────────────────────────────
    # color=None + dashed='tricolor' → draws a 3-segment low/mid/high line
    legend_items = [
        (None,            'tricolor', "Levering"),
        (C_NORDPOOL,      False,      "Markt"),
        (C_TERUGLEVERING, False,      "Teruglevering"),
    ]
    extra = []
    if len(predicted) >= 2:
        extra.append((C_PREDICTED, True,  "Predicted"))
    if len(bat_power) >= 2:
        extra.append((C_BAT_POWER, False, "Bat. kW"))
    if len(bat_soc) >= 2:
        extra.append((C_BAT_SOC,   True,  "Bat. SoC"))

    def draw_legend_row(items, y_row):
        if not items:
            return
        line_len       = 24
        gap_after_line = 5
        gap_between    = 20
        item_widths = []
        total_w = 0
        for _, _, label in items:
            bb = draw.textbbox((0, 0), label, font=font_sm)
            w = line_len + gap_after_line + (bb[2] - bb[0])
            item_widths.append(w)
            total_w += w
        total_w += gap_between * (len(items) - 1)
        x = LEFT + (PLOT_W - total_w) // 2
        y_line = y_row + 8
        for (color, dashed, label), iw in zip(items, item_widths):
            if dashed == 'tricolor':
                seg = line_len // 3
                draw.line([(x,           y_line), (x + seg,     y_line)], fill=C_LOW,  width=3)
                draw.line([(x + seg,     y_line), (x + seg * 2, y_line)], fill=C_MID,  width=3)
                draw.line([(x + seg * 2, y_line), (x + line_len, y_line)], fill=C_HIGH, width=3)
            elif dashed:
                for dx in range(0, line_len, 7):
                    draw.line([(x + dx, y_line), (x + min(dx + 4, line_len), y_line)],
                              fill=color, width=2)
            else:
                draw.line([(x, y_line), (x + line_len, y_line)], fill=color, width=3)
            draw.text((x + line_len + gap_after_line, y_row), label,
                      fill=TEXT_BRIGHT, font=font_sm)
            x += iw + gap_between

    draw_legend_row(legend_items, 4)
    draw_legend_row(extra,        30)

    return img


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    img = draw_chart(data)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    img.save(OUTPUT_PATH, 'PNG')
    print(f"Energy detail chart saved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
