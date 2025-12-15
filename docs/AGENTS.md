# Agent Instructions for ESPHome LVGL Wallpanel

This document contains critical information for AI agents working on this ESPHome wallpanel project to avoid common configuration errors and pitfalls.

## Project Overview

This is an ESPHome-based smart home wallpanel running on ESP32-P4 with a 1024x600 MIPI DSI display, GT911 touchscreen, and LVGL graphics library. It integrates with Home Assistant for device control and status display.

**Theme System**: The project uses a comprehensive Home Assistant dark theme with state-based styling (pressed, checked, focused, disabled). See `THEME.md` for complete documentation on using the theme system.

## Critical ESPHome Configuration Rules

### 1. Online Image Component

When adding camera feeds or external images, use the `online_image` component with these **exact parameters**:

```yaml
# REQUIRED: Add http_request component first
http_request:

# Then configure online_image
online_image:
  - url: https://your-home-assistant.url/api/camera_proxy/camera.entity_name
    id: image_id
    type: RGB565              # Display color format (required)
    format: PNG               # Source image format: PNG, JPEG, JPG, or BMP
    resize: 480x480           # Resize to fit display
    update_interval: 60s      # How often to fetch the image
    request_headers:          # Note: request_headers NOT headers
      Authorization: "Bearer YOUR_TOKEN_HERE"
```

**Common Mistakes to Avoid:**
- ❌ Using `format: RGB565` (RGB565 is the `type`, not `format`)
- ❌ Using `headers:` instead of `request_headers:`
- ❌ Forgetting to add `http_request:` component
- ❌ Using `platform: homeassistant` (doesn't exist for images)
- ❌ Missing the required `type:` parameter

### 2. Home Assistant Authentication

Home Assistant's camera proxy API requires Bearer token authentication:

**Correct Method:**
```yaml
request_headers:
  Authorization: "Bearer eyJhbGc..."  # Long-lived access token
```

**Incorrect Methods:**
- ❌ URL query parameters: `?token=...` (returns 403 Forbidden)
- ❌ Basic auth
- ❌ API key headers

**To create a token:**
1. Home Assistant → Profile → Security
2. Create Long-Lived Access Token
3. Use in `Authorization: "Bearer <token>"` header

### 3. Component Dependencies

Some ESPHome components require others to be enabled:

| Component | Requires |
|-----------|----------|
| `online_image` | `http_request` |
| `online_image` (HTTPS) | `http_request` |

Always add dependencies **before** the component that needs them in the YAML file.

### 4. LVGL Display Configuration Requirements

**CRITICAL:** The display component must be configured correctly for LVGL:

```yaml
display:
  - platform: mipi_dsi
    id: my_lcd
    auto_clear_enabled: false  # REQUIRED for LVGL - do not set lambda
    update_interval: 33ms      # Most displays use never except OLED/ePaper
```

**Why `auto_clear_enabled: false`?**
- LVGL manages its own rendering and screen clearing
- Display driver conflicts with LVGL if it clears the screen
- Never set a `lambda:` on displays used by LVGL

**Buffer Configuration:**
```yaml
lvgl:
  buffer_size: 100%  # Default, good for PSRAM devices
  # For devices without PSRAM, use 25%
  # With PSRAM available, 12% in internal RAM can be faster
```

Buffer calculation: `(width × height × 2 bytes) × percentage`
- LVGL only redraws changed areas, so smaller buffers have minimal performance impact

### 5. LVGL Widget Configuration

**Widget Hierarchy:**
- Display (hardware) → Pages → Widgets → Child Widgets
- All widgets need an `id:` to be referenced in automations
- Widgets map to ESPHome components:

| LVGL Widget | ESPHome Component |
|-------------|-------------------|
| button | Switch, Binary Sensor |
| switch, checkbox | Switch |
| slider, arc, spinbox | Number, Sensor |
| dropdown, roller | Select |
| label, textarea | Text, Text Sensor |
| led | Light |

**Container Widget (non-interactive):**
```yaml
- obj:
    id: container_id
    x: 360
    y: 20
    width: 500
    height: 520
    radius: 12
    bg_color: 0x1F2933
    widgets:
      - label:
          text: "Title"
          align: TOP_MID
      - image:
          src: image_id
          align: CENTER
```

**Button Widget (interactive):**
```yaml
- button:
    id: button_id
    x: 20
    y: 20
    width: 320
    height: 140
    on_press:
      - homeassistant.service:
          service: switch.toggle
          data:
            entity_id: light.entity_name
```

**Important Notes:**
- Image `src:` references the `id:` from `online_image` or `image` components
- Use `bg_image_src:` for widget background images, not `image_src`
- Coordinates are absolute unless using `align:` parameter or layouts
- Colors use hex format: `0xRRGGBB` or CSS names like `springgreen`
- Dark theme background: `0x0B1220` (Home Assistant style)
- Tile background: `0x1F2933` (dark grey/blue)

### 5a. LVGL Layout Systems (Avoid Manual Positioning)

Instead of manually setting `x:` and `y:` coordinates, use layouts:

**Flex Layout (CSS Flexbox subset):**
```yaml
- obj:
    layout:
      type: flex
      flex_flow: ROW_WRAP  # or COLUMN, ROW, COLUMN_WRAP, etc.
      flex_align_main: SPACE_EVENLY
      flex_align_cross: CENTER
      flex_align_track: CENTER
    widgets:
      - button:
          flex_grow: 1  # Widget grows to fill space
```

**Grid Layout (CSS Grid subset):**
```yaml
- obj:
    layout:
      type: grid
      grid_columns: [FR(1), FR(1), FR(1)]  # 3 equal columns
      grid_rows: [100, CONTENT, FR(2)]     # Fixed, auto, flexible
      grid_column_align: CENTER
      grid_row_align: START
    widgets:
      - button:
          grid_cell_column_pos: 0
          grid_cell_row_pos: 0
          grid_cell_column_span: 2
```

**Grid Units:**
- Pixels: `100` (absolute size)
- `CONTENT`: size based on content
- `FR(n)`: free units (proportional sizing)

### 5b. LVGL Fonts

**Built-in Library Fonts (always available):**
- `montserrat_8` through `montserrat_48` (8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48)
- All include ASCII + symbols + 60 FontAwesome icons
- `simsun_16_cjk` (CJK support)
- `unscii_8`, `unscii_16` (8-bit style)
- `dejavu_16_persian_hebrew`

**Custom ESPHome Fonts:**
```yaml
font:
  - file: "fonts/Roboto-Regular.ttf"
    id: roboto_20
    size: 20
    bpp: 4  # Use 4 for anti-aliasing, 1 for sharp pixelated
    glyphs: "0123456789:. °C%"  # Only include needed characters
```

**Note:** Custom fonts won't include FontAwesome symbols unless explicitly added to glyphs.

### 5c. LVGL Lambda Typing (CRITICAL)

LVGL uses **scaled integers**, not floats. Using wrong types causes silent failures:

| Property | Type | Range | Notes |
|----------|------|-------|-------|
| `opacity` | int | 0–255 | Not 0.0–1.0! |
| `brightness` | int | 0–255 | Same scale |
| `angle` | int | 0–3600 | Tenths of degrees (360° = 3600) |
| `color` | `lv_color_hex()` | — | Use `lv_color_hex(0xRRGGBB)` |
| `zoom` | int | 0–2560 | 256 = 1.0x, 2560 = 10.0x |

**Example Lambda:**
```yaml
- label:
    text_color: !lambda |-
      return lv_color_hex(0xFF0000);  # Red
    text_opacity: !lambda |-
      return 200;  # Not 0.78!
```

### 5d. LVGL State Management and Dynamic Colors

**Important:** ESPHome LVGL has limited support for declarative state-based styling. Colors must be updated dynamically using automation actions and lambdas.

**Dynamic Color Updates:**
Use `lvgl.widget.update` with lambdas in Home Assistant entity state changes:

```yaml
binary_sensor:
  - platform: homeassistant
    id: lamp_state
    entity_id: light.living_room
    on_state:
      then:
        - lvgl.widget.update:
            id: lamp_button
            state:
              checked: !lambda return x;
            bg_color: !lambda |-
              return x ? id(ha_state_on) : id(ha_bg_card);
```

This updates both the checked state and background color based on Home Assistant entity state.

**Idle Detection:**
```yaml
lvgl:
  on_idle:
    timeout: !lambda "return (id(display_timeout).state * 1000);"
    then:
      - light.turn_off: backlight
      - lvgl.pause:
```

**Conditions:**
- `lvgl.is_idle`: Check if timeout exceeded
- `lvgl.is_paused`: Check if LVGL is paused

### 5e. LVGL Actions and Updates

**Widget Update Operations:**

```yaml
# Update widget state (checked, value, etc.)
lvgl.widget.update:
  id: widget_id
  state:
    checked: true

# Redraw widget/screen (no property changes)
lvgl.widget.redraw:
  id: widget_id  # omit for full screen

# Refresh lambdas only (requires lambda properties)
lvgl.widget.refresh:
  id: widget_id

# Update style at runtime
lvgl.style.update:
  id: style_id
  bg_color: 0xFF0000
```

**Key Differences:**
- `update`: Changes state/properties
- `redraw`: Forces visual refresh (useful after resume)
- `refresh`: Re-evaluates lambdas
- `style.update`: Changes styles affecting all widgets using that style

### 5f. LVGL Page Navigation

**Multi-Page Configuration:**
```yaml
lvgl:
  pages:
    - id: main_page
      widgets: [...]
    - id: settings_page
      skip: true  # Skip in next/previous navigation
      widgets: [...]
    - id: info_page
      widgets: [...]
```

**Navigation Actions:**
```yaml
# Navigate to specific page
on_press:
  - lvgl.page.show:
      id: settings_page
      animation: OVER_LEFT  # Optional: NONE, OVER_*, MOVE_*, FADE_*, OUT_*

# Next/Previous page (respects skip flag)
on_press:
  - lvgl.page.next:  # or lvgl.page.previous
      animation: MOVE_LEFT
```

**Configuration Options:**
- `page_wrap: true` (default): Wraps from last to first page
- `skip: true`: Page excluded from next/previous navigation (but accessible via `show`)

**Animation Types:**
- `NONE`: Instant
- `OVER_LEFT/RIGHT/TOP/BOTTOM`: Slide over current page
- `MOVE_LEFT/RIGHT/TOP/BOTTOM`: Push current page out
- `FADE_IN/OUT`: Fade transition
- `OUT_LEFT/RIGHT/TOP/BOTTOM`: Slide out current page

### 6. Hardware Configuration

**Display Specifications:**
- Resolution: 1024x600
- Update rate: 33ms (~30 FPS)
- Color format: RGB565
- Interface: MIPI DSI

**Touchscreen:**
- Controller: GT911
- I2C: SDA=GPIO7, SCL=GPIO8
- Interrupt: GPIO21
- Used for wake-on-touch functionality

**Network:**
- ESP32-C6 coprocessor via esp32_hosted
- WiFi credentials in secrets.yaml

### 6. Project Structure

```
wallpanel/
├── wallpanel.yaml       # Main ESPHome configuration
├── common/
│   ├── colors.yaml     # Legacy color definitions (consider migrating to ha_theme.yaml)
│   ├── images.yaml     # 20 MDI icons (32x32 RGB565)
│   └── ha_theme.yaml   # Home Assistant dark theme with state-based styles
├── secrets.yaml        # WiFi credentials (not in git)
├── README.md           # Project documentation
├── AGENTS.md           # This file - Agent instructions
└── THEME.md            # Theme system documentation and usage guide
```

**Include Syntax:**
```yaml
<<: !include common/colors.yaml
<<: !include common/images.yaml
<<: !include common/ha_theme.yaml  # Home Assistant theme
```

**Theme Usage:**
All widgets automatically inherit Home Assistant dark theme styling. The `ha_theme.yaml` file defines 15 colors using ESPHome's `color:` component with RGB percentages. Reference colors by ID (e.g., `ha_bg_card`, `ha_text_primary`) instead of hex values. State-based styling (pressed, checked, focused, disabled) must be configured in the LVGL theme section of `wallpanel.yaml`. See `THEME.md` for complete documentation.

**Important:** Colors are defined using ESPHome's standard `color:` component syntax:
```yaml
color:
  - id: ha_bg_card
    red: 12%
    green: 16%
    blue: 20%
```

### 7. Common ESPHome Validation Errors

**online_image Component Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `'type' is a required option` | Missing `type:` parameter | Add `type: RGB565` for display format |
| `Unknown value 'RGB565' for format` | Wrong parameter name | Use `format: PNG/JPEG/BMP`, not `RGB565` |
| `is an invalid option. Did you mean [request_headers]?` | Wrong parameter name | Use `request_headers:` not `headers:` |
| `Component online_image requires component http_request` | Missing dependency | Add `http_request:` before `online_image:` |
| `'file' is a required option for [image]` | Wrong component type | Use `online_image:` not `image:` for URLs |

**LVGL Configuration Errors:**

| Error/Issue | Cause | Solution |
|-------------|-------|----------|
| Screen conflicts/flicker | Display has lambda or auto_clear_enabled | Set `auto_clear_enabled: false`, remove lambda |
| Widget not updating | Missing widget `id:` | Add `id: widget_name` to reference in automations |
| Lambda property not working | Returning float instead of int | Use scaled integers (opacity: 0-255, angle: 0-3600) |
| Color not displaying | Using hex without function | Use `lv_color_hex(0xRRGGBB)` in lambdas |
| Build error on refresh | Widget has no lambda properties | Only use `lvgl.widget.refresh` on widgets with lambdas |
| FontAwesome icons missing | Custom font without symbols | Use built-in Montserrat fonts or add symbols to glyphs |
| Background image not working | Wrong property name | Use `bg_image_src:` not `image_src:` for backgrounds |
| Grid cell positioning ignored | Applied to parent instead of child | `grid_cell_*` properties go on child widgets, not layout parent |

**Theme/Color Errors:**

| Error/Issue | Cause | Solution |
|-------------|-------|----------|
| `Component not found: ha_colors` | Invalid custom component name | Use `color:` component (standard ESPHome) |
| `No module named 'esphome.components.ha_colors'` | Custom component doesn't exist | Define colors with `color:` not `ha_colors:` |
| Color not recognized | Incorrect color definition syntax | Use `red:`, `green:`, `blue:` percentages or hex |
| Theme colors not applying | Include order wrong | Include `ha_theme.yaml` after standard components |

### 8. Security Best Practices

**ESPHome Secrets (secrets.yaml):**
Store ESPHome credentials in `secrets.yaml` (already in .gitignore):
```yaml
# secrets.yaml - ESPHome secrets
wifi_ssid: "YourSSID"
wifi_password: "YourPassword"
api_password: "your-api-password"
ota_password: "your-ota-password"

# wallpanel.yaml
substitutions:
  api_password: !secret api_password
  ota_password: !secret ota_password

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

**Shell Script Secrets (.ha_secrets):**
Home Assistant tokens for shell scripts are stored in `.ha_secrets` (in .gitignore):

```bash
# .ha_secrets - Home Assistant API credentials
HA_URL="https://your-homeassistant-url"
HA_TOKEN="your-long-lived-access-token-here"
```

**Setup Instructions:**
1. Copy `.ha_secrets.example` to `.ha_secrets`
2. Create a Long-Lived Access Token in Home Assistant:
   - Profile → Security → Long-Lived Access Tokens
   - Create Token → Give it a name (e.g., "ESPHome Scripts")
3. Fill in your `HA_TOKEN` and `HA_URL` in `.ha_secrets`
4. Never commit `.ha_secrets` to git (it's in .gitignore)

**Important Notes:**
- ❌ `!secret` does NOT work inside lambda strings (C++ code)
- ❌ ESPHome `online_image` cannot use runtime secrets in headers
- ✅ Current architecture: Scripts download images WITH auth, ESP loads WITHOUT auth via local network
- ✅ All shell scripts now load credentials from `.ha_secrets` file

**Why the Current Architecture Works:**
```
┌─────────────────────────────────────────────┐
│ Home Assistant Server                       │
│ ┌─────────────────────────────────────────┐ │
│ │ Shell scripts (with HA token)           │ │
│ │ - update_cameras.sh                     │ │
│ │ - update_energieprijzen.sh              │ │
│ │ - update_agenda.sh                      │ │
│ │   ↓ (authenticated downloads)           │ │
│ │ /config/www/esphomefiles/*.png          │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
                    ↓
        (local network, no auth needed)
                    ↓
┌─────────────────────────────────────────────┐
│ ESPHome Device (wallpanel)                  │
│ - Loads images via http://192.168.2.2:8123 │
│ - No authentication required                │
│ - online_image component works perfectly    │
└─────────────────────────────────────────────┘
```

### 9. Development State

**Implemented:**
- ✅ Hardware configuration (display, touch, WiFi)
- ✅ LVGL graphics engine with dark theme
- ✅ Home Assistant API integration
- ✅ Auto sleep/wake (configurable timeout)
- ✅ One device control (lamp_voordeur)
- ✅ One camera widget (buienradar)

**Not Yet Implemented:**
- Multiple pages/rooms
- Sensor data displays (temperature, humidity, etc.)
- Additional entity controls
- Navigation between pages
- Scene/automation controls

### 10. Testing and Validation

**Before committing changes:**
1. Run ESPHome validation: `esphome config wallpanel.yaml`
2. Check for common errors listed in section 7
3. Verify all `!include` files exist
4. Ensure secrets.yaml has required entries
5. Test compilation: `esphome compile wallpanel.yaml`

**Common compilation flags:**
- `-DBOARD_HAS_PSRAM` (required for this board)
- Memory: QIO OPI mode, 16MB flash, 512KB RAM

### 11. When Adding New Features

**Adding a new Home Assistant entity control:**
1. Add binary_sensor or sensor for state monitoring
2. Add LVGL widget (button for controls, label for display)
3. Link state updates with `lvgl.widget.update` in `on_state:`
4. Add `on_press:` action with `homeassistant.service:` call

**Adding a new page:**
```yaml
pages:
  - id: page_name
    bg_color: 0x0B1220
    widgets:
      # Your widgets here
```

**Adding navigation buttons:**
```yaml
on_press:
  - lvgl.page.show: page_name
```

### 12. Useful Resources

- [ESPHome Documentation](https://esphome.io/)
- [LVGL Documentation](https://docs.lvgl.io/)
- [Home Assistant API](https://developers.home-assistant.io/docs/api/rest/)
- ESP32-P4 Board: esp32-p4-evboard
- Display: JC1060P470 MIPI DSI

### 13. Quick Reference: Working Configuration

For adding camera feeds, use this template:

```yaml
# Step 1: Add http_request (if not already present)
http_request:

# Step 2: Add online_image
online_image:
  - url: https://homeassistant.jvanw.nl/api/camera_proxy/camera.ENTITY_NAME
    id: unique_image_id
    type: RGB565
    format: PNG
    resize: 480x480
    update_interval: 60s
    request_headers:
      Authorization: "Bearer YOUR_LONG_LIVED_TOKEN"

# Step 3: Add LVGL widget
lvgl:
  pages:
    - id: page_id
      widgets:
        - obj:
            id: container_id
            x: 360
            y: 20
            width: 500
            height: 520
            radius: 12
            bg_color: 0x1F2933
            widgets:
              - label:
                  text: "Camera Name"
                  align: TOP_MID
                  y: 10
                  text_color: 0xFFFFFF
              - image:
                  src: unique_image_id
                  align: CENTER
                  y: 20
```

### 14. LVGL Widget-Specific Capabilities and Limitations

**CRITICAL REFERENCE**: See `esphome-lvgl-reference.md` for complete documentation of all widget properties, styling options, and detailed examples.

#### Image Component vs Image Widget

**Image Component Definition (common/images.yaml):**
```yaml
image:
  - id: my_icon
    file: mdi:home
    resize: 32x32
    type: RGB565
    # ❌ NO color property exists
    # ❌ NO recolor property exists
```

**Valid Image Component Properties:**
- ✅ `file` (required): Local path, `mdi:icon`, URL
- ✅ `id` (required)
- ✅ `type` (required): `BINARY`, `GRAYSCALE`, `RGB565`, `RGB`
- ✅ `resize`: `WIDTHxHEIGHT`
- ✅ `byte_order`: For RGB565 - `little_endian` or `big_endian`
- ❌ **NO** `color` property
- ❌ **NO** `recolor` property

**Image Widget in LVGL:**
```yaml
# CORRECT - Color applied at widget level
- image:
    src: my_icon
    image_recolor: 0xFF6B6B        # Target color
    image_recolor_opa: COVER       # COVER (full), TRANSP (none), 50%, or 1.0

# INCORRECT - These don't exist or wrong format
- image:
    src: my_icon
    recolor: 0xFF6B6B              # ❌ INVALID - use image_recolor
    color: 0xFF6B6B                # ❌ INVALID
    image_recolor_opa: 255         # ❌ INVALID - use COVER, 100%, or 1.0
```

**Valid Image Widget Properties:**
- ✅ `src`: References image component `id`
- ✅ `image_recolor`: Color to blend with image
- ✅ `image_recolor_opa`: COVER (full), TRANSP (none), 50%, or 1.0
- ✅ `angle`: Rotation in 1/10 degrees (450 = 45°)
- ✅ `zoom`: Zoom level (256 = 100%, 512 = 200%)
- ✅ `offset_x`, `offset_y`: Position offset
- ❌ **NO** `recolor` (must use `image_recolor`)
- ❌ **NO** `color` (not a valid property)
- ❌ **NO** integer opacity like 255 (use COVER, 100%, or 1.0)

#### Dropdown Widget Limitations

**CRITICAL**: ESPHome LVGL dropdown has severe styling limitations:

```yaml
# CORRECT - Only button styling is supported
- dropdown:
    id: my_dropdown
    options:
      - "Option 1"         # ✅ Use YAML list
      - "Option 2"
      - "Option 3"
    bg_color: 0x2C2C2E     # ✅ Styles the button
    text_color: ha_text_primary
    text_font: roboto_16
    border_width: 1
    radius: 8

# INCORRECT - These don't work
- dropdown:
    id: my_dropdown
    options: "A\nB\nC"     # ❌ Old format, use list
    style:                 # ❌ Invalid property
      list:
        bg_color: 0x000000
    styles:                # ❌ Also invalid
      list:
        bg_color: 0x000000
```

**Dropdown Limitations:**
- ❌ Cannot style dropdown list background
- ❌ Cannot style selected item appearance
- ❌ Cannot customize list border/radius separately
- ✅ Can only style the dropdown button itself
- ✅ List appearance uses LVGL's default theme

**Workaround**: Use `roller` widget instead if custom list styling is critical.

#### Object (obj) Widget and Scrollbars

**CRITICAL**: Always disable scrollbars on container objects:

```yaml
# CORRECT - Explicitly disable scrollbars
- obj:
    id: my_container
    scrollbar_mode: "off"    # ✅ Prevents unwanted scrollbars
    clip_corner: true        # ✅ Clip children to rounded corners
    width: 314
    height: 220
    radius: 12
    widgets:
      - image:
          src: my_image

# INCORRECT - May show scrollbars unexpectedly
- obj:
    id: my_container
    # Missing scrollbar_mode
    widgets:
      - image:
          src: my_image
```

**Scrollbar Mode Options:**
- `"off"`: Never show scrollbars
- `"on"`: Always show scrollbars
- `"auto"`: Show only when content overflows (default)
- `"active"`: Show when scrolling

**When to use `scrollbar_mode: "off"`:**
- ✅ Fixed-size containers with images
- ✅ Temperature/status tiles
- ✅ Cards with exact content sizing
- ✅ Any widget where scrolling shouldn't be possible

#### Performance Considerations

**Slider on_value Performance Issue:**
```yaml
# PROBLEMATIC - Called continuously during drag
- slider:
    on_value:
      then:
        - homeassistant.service:
            service: cover.set_position  # ⚠️ Called 100s of times!

# CORRECT - Use on_release for discrete actions
- slider:
    on_release:
      then:
        - homeassistant.service:
            service: cover.set_position  # ✅ Called once when released
```

**Rule**: Use `on_release` instead of `on_value` for any action that:
- Calls Home Assistant services
- Updates external devices
- Performs heavy calculations
- Sends network requests

Use `on_value` only for:
- Updating local label displays
- Visual feedback on the panel itself
- Fast local state changes

#### Screen Burn-In Prevention

For wall-mounted displays with static content:

```yaml
lvgl:
  on_idle:
    timeout: 300s
    then:
      - light.turn_off: backlight
      - lvgl.pause:
          show_snow: true    # ✅ Prevent LCD burn-in by exercising pixels
```

**What `show_snow` does:**
- Displays random pixels across screen during pause
- Exercises all pixels periodically
- Prevents static content burn-in on LCD panels
- Invisible to users (screen is off)

### 15. LVGL Best Practices

Based on ESPHome LVGL documentation (v8.4):

**Performance & Memory:**
- ✅ Use 12% buffer in internal RAM when PSRAM available (faster than PSRAM)
- ✅ Use 25% buffer for non-PSRAM devices
- ✅ Rely on LVGL's smart redrawing (only changed areas)
- ✅ Set `bpp: 4` on custom fonts for anti-aliasing

**Layout & Design:**
- ✅ Use Flex or Grid layouts instead of manual x/y positioning
- ✅ Implement idle timeout for screen saver/backlight control
- ✅ Use state-based styling for interactive feedback (pressed, checked, etc.)
- ✅ Leverage style definitions for consistent theming across widgets
- ✅ Test gradient dithering (`ordered` vs `err_diff`) on actual hardware

**Widget Configuration:**
- ✅ Always add `id:` to widgets you want to reference in automations
- ✅ Use built-in Montserrat fonts (include FontAwesome icons automatically)
- ✅ Group related widgets with encoder/keypad configuration
- ✅ Use `bg_image_src:` for background images (not `image_src`)
- ✅ Always set `scrollbar_mode: "off"` on containers that shouldn't scroll
- ✅ Use `clip_corner: true` on image containers with rounded corners

**Image Handling:**
- ✅ Match `online_image` resize dimensions to widget size
- ✅ Apply color at widget level using `image_recolor` + `image_recolor_opa`
- ❌ Never add `color` property to image component definitions
- ✅ Use `image_recolor_opa: 255` for full recolor, 0 for no recolor

**Dropdown Usage:**
- ✅ Use YAML list format for options
- ✅ Only style the button (background, text, border, radius)
- ❌ Don't attempt to style the dropdown list (not supported)
- ✅ Consider `roller` widget if custom list styling is needed

**Lambda Considerations:**
- ✅ Return scaled integers, never floats (opacity: 0-255, angle: 0-3600)
- ✅ Use `lv_color_hex(0xRRGGBB)` for color values
- ✅ Only use `lvgl.widget.refresh` on widgets that have lambda properties

**Display Configuration:**
- ✅ Always set `auto_clear_enabled: false` for LVGL displays
- ✅ Never add a `lambda:` to displays used by LVGL
- ✅ Use `update_interval: never` for most displays (except OLED/ePaper)

**Input Handling:**
- ✅ Configure `long_press_time` and `long_press_repeat_time` for touchscreens
- ✅ Use `resume_on_input: true` (default) to wake from pause on touch
- ✅ Implement proper wake-on-touch in touchscreen `on_release:` handler
- ✅ Use `on_release` instead of `on_value` for performance-critical actions

---

## Summary

The most critical lessons learned:

**Online Image Component:**
1. **Always add `http_request:` before using `online_image`**
2. **Use `type: RGB565` and `format: PNG` (not the other way around)**
3. **Use `request_headers:` not `headers:` for authentication**
4. **Home Assistant requires Bearer token in Authorization header**

**LVGL Configuration:**
5. **Set `auto_clear_enabled: false` on displays used by LVGL**
6. **All widgets need an `id:` to be referenced in automations**
7. **Lambda properties must return scaled integers, not floats**
8. **Use `lv_color_hex()` for colors in lambdas**
9. **Use `bg_image_src:` for background images**
10. **Prefer Flex/Grid layouts over manual x/y positioning**

**Image Component & Widget Recoloring (Section 14):**
11. **NEVER add `color` property to image component definitions**
12. **Use `image_recolor` + `image_recolor_opa` on image widgets, NOT `recolor`**
13. **Image color must be applied at widget level, not in image definition**
14. **Use BINARY type for MDI icons, not RGB565 (prevents black squares)**
15. **Opacity format: Use COVER, 100%, or 1.0 (NOT 255)**

**Dropdown Widget Limitations (Section 14):**
16. **Dropdown list styling is NOT supported in ESPHome LVGL**
17. **Use YAML list format for options, NOT newline-separated strings**
18. **Only the dropdown button can be styled (bg_color, border, etc.)**
19. **NO `style:` or `styles:` property exists for dropdowns**

**Container Widgets and Scrollbars (Section 14):**
20. **Always set `scrollbar_mode: "off"` on containers that shouldn't scroll**
21. **Use `clip_corner: true` on image containers with rounded corners**

**Theme and State Management:**
22. **Define colors using ESPHome's `color:` component (not custom components)**
23. **State-based colors require dynamic updates via `lvgl.widget.update` with lambdas**
24. **Update widget colors in `binary_sensor on_state:` actions for Home Assistant sync**

**Performance Optimization (Section 14):**
25. **Use `on_release` instead of `on_value` for Home Assistant service calls**
26. **`on_value` triggers continuously during slider drag - performance killer!**

**Development Process:**
27. **Test configuration with `esphome config` before compiling**
28. **Check validation errors against section 7 error tables**
29. **Refer to `esphome-lvgl-reference.md` for complete widget property documentation**

Following these guidelines will prevent 95% of configuration errors when working with this project. See Section 14 for detailed widget-specific capabilities and limitations.
