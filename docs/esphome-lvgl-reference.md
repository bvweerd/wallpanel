# ESPHome LVGL Reference Guide

> A comprehensive reference for ESPHome LVGL capabilities, limitations, and common pitfalls to avoid configuration errors.

## Table of Contents
- [Hardware Requirements](#hardware-requirements)
- [Core Capabilities](#core-capabilities)
- [Widget Reference](#widget-reference)
- [Styling System](#styling-system)
- [Image Handling](#image-handling)
- [Common Mistakes & Solutions](#common-mistakes--solutions)
- [Best Practices](#best-practices)

---

## Hardware Requirements

### Supported Microcontrollers
- **Required**: ESP32 or RP2040
- **PSRAM**: Not mandatory but highly recommended for large color displays
- **Without PSRAM**: Use `buffer_size: 25%`

### Display Configuration
```yaml
display:
  - platform: mipi_dsi  # or other supported platform
    auto_clear_enabled: false  # REQUIRED - LVGL manages rendering
    update_interval: never      # For most displays (OLED/ePaper need specific intervals)
```

**Critical**: Display must NOT have:
- `auto_clear_enabled: true`
- Custom lambda functions (LVGL takes full control)

---

## Core Capabilities

### Color & Styling

#### Color Specification
```yaml
# All formats are valid:
bg_color: 0xFF0000          # Hexadecimal (preferred)
text_color: RED             # CSS color names
border_color: my_color_id   # ESPHome color IDs
```

#### Opacity Formats
```yaml
bg_opa: TRANSP     # String constants (TRANSP/COVER)
bg_opa: 0.5        # Float (0.0-1.0)
bg_opa: 50%        # Percentage
bg_opa: !lambda return 128;  # Lambda integer (0-255)
```

#### Color Depth
- **Currently supported**: RGB565 only (16-bit, 2 bytes/pixel)
- Future versions may support other formats

---

## Widget Reference

### Widget to ESPHome Component Mapping

Some LVGL widgets function as native ESPHome components:

| LVGL Widget | ESPHome Component Type |
|-------------|------------------------|
| `button` | Switch, Binary Sensor |
| `switch`, `checkbox` | Switch |
| `slider`, `arc`, `spinbox` | Number, Sensor |
| `dropdown`, `roller` | Select |
| `label`, `textarea` | Text, Text Sensor |
| `led` | Light |

### Common Widget Properties

All widgets support:
```yaml
widgets:
  - obj:  # or any widget type
      id: my_widget
      x: 10              # Pixels from left
      y: 20              # Pixels from top
      width: 100         # Pixels or percentage
      height: 50
      align: CENTER      # Alignment relative to parent
      bg_color: 0x000000
      radius: 12         # Rounded corners
      border_width: 1
      scrollbar_mode: "off"  # "on", "off", "auto", "active"
```

### Widget-Specific Details

#### Object (`obj`)
- Base container widget
- By default: empty rounded rectangle
- Touch interaction enabled by default
- Best for creating custom layouts and containers

```yaml
- obj:
    id: container
    scrollbar_mode: "off"  # IMPORTANT: Prevent unwanted scrollbars
    widgets:
      # Child widgets here
```

#### Button
```yaml
- button:
    id: my_button
    checkable: true      # Enable toggle behavior
    widgets:
      - label:
          text: "Press Me"
    on_press:
      - logger.log: "Button pressed"
    on_value:            # Triggered when checkable state changes
      - if:
          condition:
            lambda: return x;  # x = boolean state
          then:
            - logger.log: "Button ON"
```

#### Dropdown
```yaml
- dropdown:
    id: my_dropdown
    options:
      - "Option 1"       # Use list format (NOT newline-separated strings)
      - "Option 2"
      - "Option 3"
    bg_color: 0x2C2C2E
    text_font: roboto_16
    border_width: 1
    radius: 8
    on_value:
      - logger.log:
          format: "Selected index: %d"
          args: [x]      # x = selected index (integer)
```

**CRITICAL LIMITATIONS**:
- ❌ NO `style:` or `styles:` property for dropdown list styling
- ❌ Cannot customize dropdown list appearance (background, selected item, etc.)
- ✅ Can only style the dropdown button itself
- The dropdown list uses LVGL's default theme styling

#### Label
```yaml
- label:
    id: my_label
    text: "Hello World"
    text_color: 0xFFFFFF
    text_font: roboto_20
    align: CENTER
    long_mode: "wrap"    # "wrap", "scroll", "clip", "dot"
```

#### Image
```yaml
- image:
    id: my_image
    src: my_image_id     # References image: component
    align: CENTER
    # Transformation properties:
    image_recolor: 0xFF0000        # Color to blend
    image_recolor_opa: COVER       # COVER (full), TRANSP (none), 50%, or 0.5
    angle: 450           # Rotation in 1/10 degrees (450 = 45°)
    zoom: 256            # Zoom level (256 = 100%, 512 = 200%)
    offset_x: 10         # Offset from calculated position
    offset_y: 5
```

**Image Recoloring**:
```yaml
# CORRECT - Use image_recolor and image_recolor_opa
- image:
    src: my_icon
    image_recolor: 0xFF6B6B      # Target color
    image_recolor_opa: COVER     # Full recolor (or 100%, 1.0)

# INCORRECT - These properties don't exist or wrong format
- image:
    src: my_icon
    recolor: 0xFF6B6B            # ❌ INVALID - use image_recolor
    color: 0xFF6B6B              # ❌ INVALID
    image_recolor_opa: 255       # ❌ INVALID - use COVER, 100%, or 1.0
```

---

## Styling System

### Style Priority (Highest to Lowest)
1. State-based styles (`:pressed`, `:checked`, etc.)
2. Locally specified styles (on widget)
3. Style definitions (reusable styles)
4. Theme styles (global defaults)

### 50+ Style Properties

#### Background
```yaml
bg_color: 0x000000
bg_opa: COVER
bg_grad_color: 0x333333
bg_grad_dir: VER         # VER, HOR, etc.
```

#### Borders
```yaml
border_width: 2
border_color: 0x444444
border_opa: COVER
border_side: ALL         # ALL, TOP, BOTTOM, LEFT, RIGHT, INTERNAL
```

#### Padding & Spacing
```yaml
pad_all: 10              # All sides
pad_top: 5
pad_bottom: 5
pad_left: 10
pad_right: 10
pad_row: 5               # Row gap in layouts
pad_column: 10           # Column gap in layouts
```

#### Effects
```yaml
radius: 12               # Rounded corners
shadow_width: 10
shadow_opa: 0.5
outline_width: 2
outline_color: 0xFF0000
```

#### Transforms
```yaml
transform_angle: 450     # 1/10 degrees
transform_zoom: 256      # 256 = 100%
transform_pivot_x: 50
transform_pivot_y: 50
```

### State-Based Styling
```yaml
- button:
    id: my_btn
    bg_color: 0x2C2C2E         # Default state
    state:
      pressed:
        bg_color: 0x3A3A3C     # When pressed
      checked:
        bg_color: 0x00FF00     # When checked (if checkable)
      disabled:
        bg_opa: 0.5            # When disabled
```

---

## Image Handling

### Image Component Definition

```yaml
image:
  - id: my_mdi_icon
    file: mdi:home              # Material Design Icon
    resize: 32x32
    type: RGB565                # BINARY, GRAYSCALE, RGB565, RGB
    # NO color property exists here! ❌

  - id: my_local_image
    file: images/logo.png
    resize: 100x100
    type: RGB565
    byte_order: little_endian   # For RGB565 only
```

**CRITICAL - Image Component Properties**:
- ✅ `file` (required): Local path, `mdi:icon`, `mdil:icon`, URL
- ✅ `id` (required)
- ✅ `type` (required): `BINARY`, `GRAYSCALE`, `RGB565`, `RGB`
- ✅ `resize`: `WIDTHxHEIGHT`
- ✅ `byte_order`: For RGB565 - `little_endian` or `big_endian`
- ❌ NO `color` property
- ❌ NO `recolor` property

**Color must be applied at widget level**, not in image definition!

### Online Images

```yaml
online_image:
  - url: http://example.com/image.png
    id: weather_image
    type: RGB565
    format: PNG
    resize: 300x200
    update_interval: 5min
    on_download_finished:
      - lvgl.image.update:
          id: my_image_widget
          src: weather_image
```

---

## Common Mistakes & Solutions

### ❌ Mistake 1: Adding `color` to Image Definition
```yaml
# INCORRECT
image:
  - id: my_icon
    file: mdi:thermometer
    resize: 24x24
    type: RGB565
    color: 0xFF0000           # ❌ This property doesn't exist!
```

**✅ Solution**: Use `image_recolor` on the image widget:
```yaml
image:
  - id: my_icon
    file: mdi:thermometer
    resize: 24x24
    type: BINARY           # Use BINARY for MDI icons

# Later in LVGL widgets:
- image:
    src: my_icon
    image_recolor: 0xFF0000
    image_recolor_opa: COVER    # Full recolor (or 100%, 1.0)
```

### ❌ Mistake 2: Using `recolor` Instead of `image_recolor`
```yaml
# INCORRECT
- image:
    src: my_icon
    recolor: 0xFF0000         # ❌ Invalid property
    image_recolor_opa: 255    # ❌ Invalid format
```

**✅ Solution**:
```yaml
- image:
    src: my_icon
    image_recolor: 0xFF0000   # ✅ Correct property name
    image_recolor_opa: COVER  # ✅ Use COVER, 100%, or 1.0 (not 255)
```

### ❌ Mistake 3: Trying to Style Dropdown List
```yaml
# INCORRECT
- dropdown:
    id: my_dropdown
    options: ["A", "B", "C"]
    style:                    # ❌ Invalid property
      list:
        bg_color: 0x000000
    styles:                   # ❌ Also invalid
      list:
        bg_color: 0x000000
```

**✅ Solution**: ESPHome LVGL doesn't support dropdown list styling. You can only style the dropdown button itself:
```yaml
- dropdown:
    id: my_dropdown
    options: ["A", "B", "C"]
    bg_color: 0x2C2C2E       # ✅ Styles the button only
    border_width: 1
    radius: 8
    # List appearance uses default theme - cannot be customized
```

### ❌ Mistake 4: Forgetting `scrollbar_mode: "off"`
```yaml
# INCORRECT - May show unwanted scrollbars
- obj:
    id: my_container
    width: 200
    height: 100
    widgets:
      - label:
          text: "Long text..."
```

**✅ Solution**:
```yaml
- obj:
    id: my_container
    width: 200
    height: 100
    scrollbar_mode: "off"     # ✅ Explicitly disable scrollbars
    widgets:
      - label:
          text: "Long text..."
```

### ❌ Mistake 5: Options as Newline String
```yaml
# INCORRECT
- dropdown:
    options: "Option 1\nOption 2\nOption 3"  # ❌ Old LVGL format
```

**✅ Solution**:
```yaml
- dropdown:
    options:                  # ✅ Use YAML list
      - "Option 1"
      - "Option 2"
      - "Option 3"
```

### ❌ Mistake 6: Performance Issues with `on_value`
```yaml
# PROBLEMATIC
- slider:
    on_value:
      then:
        - homeassistant.service:  # Called continuously while dragging!
            service: cover.set_position
```

**✅ Solution**: Use `on_release` for discrete actions:
```yaml
- slider:
    on_release:               # ✅ Only triggered when drag ends
      then:
        - homeassistant.service:
            service: cover.set_position
```

---

## Best Practices

### 1. Always Disable Scrollbars on Containers
```yaml
- obj:
    scrollbar_mode: "off"     # Prevent unwanted scrollbars
```

### 2. Use Theme-Based Styling
Apply common styles at the top level using LVGL's theme system:
```yaml
lvgl:
  theme:
    obj:                      # Applies to all objects
      bg_color: ha_bg_card
      radius: 12
      border_width: 0
```

### 3. Create Reusable Style Definitions
```yaml
lvgl:
  style_definitions:
    - id: tile_style
      bg_color: 0x2C2C2E
      radius: 8
      pad_all: 10

  # Apply to multiple widgets:
  widgets:
    - obj:
        styles: tile_style
```

### 4. Buffer Sizing for Performance
```yaml
lvgl:
  buffer_size: 100%           # Default, auto-fallback to 12% if fails
  # For better performance with PSRAM:
  buffer_size: 12%            # Uses faster internal RAM
```

**Formula**: For 320×240 RGB565 display:
- 100% = 320 × 240 × 2 = 153,600 bytes
- 12% = ~18,432 bytes

### 5. Image Sizing Best Practices
- Match online_image `resize` to widget dimensions
- Always specify both width and height
- Use `clip_corner: true` for rounded corners on image containers

```yaml
online_image:
  - url: http://example.com/weather.png
    resize: 314x220           # Match card dimensions

# In widget:
- obj:
    width: 314
    height: 220
    radius: 12
    clip_corner: true         # ✅ Clip image to rounded corners
    widgets:
      - image:
          src: weather_image
          align: CENTER
```

### 6. Screen Burn-In Prevention
For wall-mounted displays:
```yaml
lvgl:
  on_idle:
    timeout: 300s
    then:
      - light.turn_off: backlight
      - lvgl.pause:
          show_snow: true     # ✅ Exercise pixels to prevent burn-in
```

### 7. Font Management
```yaml
font:
  - file: "gfonts://Roboto"
    id: roboto_16
    size: 16
    glyphs: "!\"%()+=-,_.:°0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'/&@#?"
    # ✅ Specify all needed glyphs to reduce memory
```

For Material Design Icons in custom fonts:
```yaml
font:
  - file: fonts/materialdesignicons-webfont.ttf
    id: mdi_font
    size: 24
    glyphs: [
      "\U000F0046",  # mdi:checkmark
      "\U000F0047",  # mdi:close
    ]
```

---

## Actions & Automation

### Widget Actions
```yaml
# Redraw specific widget or entire screen
- lvgl.widget.redraw:
    id: my_widget             # Optional - omit to redraw all

# Refresh lambda-based properties
- lvgl.widget.refresh:
    id: my_widget

# Set focus
- lvgl.widget.focus:
    id: my_widget
    freeze: true              # Optional - prevent defocus
```

### Display Management
```yaml
# Pause/Resume rendering
- lvgl.pause:
    show_snow: false          # Prevent burn-in
- lvgl.resume:

# Update background
- lvgl.update:
    bg_color: 0x000000
```

### Page Navigation
```yaml
- lvgl.page.next:
    animation: OVER_LEFT      # NONE, OVER_*, MOVE_*, FADE_*, OUT_*
- lvgl.page.previous:
- lvgl.page.show:
    id: settings_page
```

### Conditions
```yaml
- if:
    condition:
      lvgl.is_idle:
        timeout: 60s
    then:
      - light.turn_off: backlight
```

---

## Layout Systems

### Flex Layout (Flexbox-style)
```yaml
- obj:
    layout:
      type: flex
      flex_flow: ROW_WRAP
      flex_align_main: SPACE_EVENLY
      flex_align_cross: CENTER
      flex_align_track: START
    pad_row: 10
    pad_column: 10
```

### Grid Layout
```yaml
- obj:
    layout:
      type: grid
      grid_rows: [FR(1), FR(1), FR(1)]  # 3 equal rows
      grid_columns: [100, CONTENT, FR(2)]
      grid_row_align: CENTER
      grid_column_align: STRETCH
```

---

## Quick Reference Checklist

Before deploying LVGL configuration:

- [ ] Display has `auto_clear_enabled: false`
- [ ] Display has `update_interval: never` (or appropriate for display type)
- [ ] No `color` property on `image:` definitions
- [ ] Image recoloring uses `image_recolor` + `image_recolor_opa` on widgets
- [ ] Dropdown options use YAML list format, not newline strings
- [ ] No `style:` or `styles:` on dropdown widgets
- [ ] `scrollbar_mode: "off"` on containers that shouldn't scroll
- [ ] `clip_corner: true` on image containers with rounded corners
- [ ] Online image `resize` matches widget dimensions
- [ ] Performance-critical actions use `on_release` not `on_value`
- [ ] Fonts include all required glyphs
- [ ] Buffer size appropriate for available RAM

---

## Version Information

This reference is based on ESPHome LVGL implementation as of 2024.
Always check the official documentation for the latest updates:
- https://esphome.io/components/lvgl/
- https://esphome.io/components/lvgl/widgets/

## Contributing

Found an error or have an addition? Update this document to keep it accurate and helpful for future development.
