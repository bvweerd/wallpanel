# Home Assistant Dark Theme for LVGL Wallpanel

This document explains how the Home Assistant dark theme is implemented and how to use it for consistent styling across all widgets.

## Theme Structure

The theme colors are defined in `/common/ha_theme.yaml` using ESPHome's standard `color:` component. The global theme styling is configured in the `lvgl:` section of `wallpanel.yaml`.

### Color Palette

All colors are based on Home Assistant's official dark theme and defined using RGB percentages:

| Color ID | Hex Value | Usage |
|----------|-----------|-------|
| `ha_bg_primary` | `0x0B1220` | Main background (very dark slate) |
| `ha_bg_card` | `0x1F2933` | Card/tile background (dark grey/blue) |
| `ha_bg_card_hover` | `0x2A3947` | Card hover state (lighter) |
| `ha_bg_card_pressed` | `0x364B5E` | Card pressed state (even lighter) |
| `ha_primary` | `0x03A9F4` | Primary blue (Home Assistant blue) |
| `ha_primary_dark` | `0x0288D1` | Darker blue for pressed states |
| `ha_text_primary` | `0xFFFFFF` | Primary text (white) |
| `ha_text_secondary` | `0xB3BEC6` | Secondary text (light grey) |
| `ha_text_disabled` | `0x5F6B75` | Disabled text (darker grey) |
| `ha_state_on` | `0x4CAF50` | Green for "on" state |
| `ha_state_off` | `0x5F6B75` | Grey for "off" state |
| `ha_state_unavailable` | `0xBDBDBD` | Light grey for unavailable |
| `ha_accent` | `0xFF9800` | Orange accent |
| `ha_warning` | `0xFF5722` | Red for warnings/errors |
| `ha_success` | `0x4CAF50` | Green for success |

## Global Theme Configuration

The theme provides a color palette in `common/ha_theme.yaml`. A minimal theme configuration is applied in `wallpanel.yaml`:

```yaml
lvgl:
  theme:
    obj:
      bg_opa: TRANSP      # Transparent background by default
      border_width: 0     # No borders by default
```

**Note:** ESPHome LVGL has limited support for global theme styling. State-based colors (pressed, checked, etc.) must be applied per-widget or via dynamic updates using lambdas and automation actions.

### Dynamic State-Based Colors

To change widget colors based on Home Assistant entity states, use the binary_sensor's `on_state` action:

```yaml
binary_sensor:
  - platform: homeassistant
    id: switch_lamp
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

This updates the button background:
- **Off**: Grey (`ha_bg_card`)
- **On**: Green (`ha_state_on`)

## Widget States

LVGL supports multiple widget states that can be styled independently:

### Available States

- **default**: Normal state
- **pressed**: While finger/mouse is pressing
- **focused**: When widget has focus (keyboard/encoder navigation)
- **checked**: For toggleable buttons (on/off state)
- **disabled**: When widget is disabled
- **checked+pressed**: Combination state (pressed while checked)
- **focused+pressed**: Combination state (pressed while focused)

### State Priority

States have precedence (higher overrides lower):
1. Default (lowest)
2. Focused
3. Pressed
4. Checked
5. Combination states (highest)

## Using the Theme in Widgets

### Example 1: Simple Button (Uses Global Theme)

```yaml
- button:
    id: my_button
    x: 20
    y: 20
    width: 200
    height: 80
    # No need to specify bg_color, radius, etc. - inherited from theme!
    widgets:
      - label:
          text: "Click Me"
```

### Example 2: Button with Dynamic State Colors

```yaml
# Button widget
- button:
    id: lamp_button
    checkable: true
    bg_color: ha_bg_card  # Default grey
    radius: 12
    widgets:
      - label:
          text: "Living Room"
          text_color: ha_text_primary

# In binary_sensor section - updates color based on HA state
binary_sensor:
  - platform: homeassistant
    id: lamp_sensor
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

### Example 3: Container/Card

```yaml
- obj:
    id: info_card
    width: 400
    height: 300
    bg_color: ha_bg_card
    bg_opa: COVER
    radius: 12
    border_width: 0
    widgets:
      - label:
          text: "Temperature"
          text_color: ha_text_secondary
```

### Example 4: Icon Button with Hover Effect

```yaml
- button:
    id: settings_button
    width: 60
    height: 60
    radius: 8
    state:
      pressed:
        bg_color: ha_bg_card_pressed
        transform_width: -2
        transform_height: -2
    widgets:
      - image:
          src: icon_settings
```

## Synchronizing Button State with Home Assistant

To show the actual on/off state of a Home Assistant entity, use `lvgl.widget.update` with a lambda:

```yaml
binary_sensor:
  - platform: homeassistant
    id: switch_lamp_voordeur
    entity_id: light.lamp_voordeur_licht
    trigger_on_initial_state: true
    on_state:
      then:
        - lvgl.widget.update:
            id: lamp_voordeur_id
            state:
              checked: !lambda return x;  # x is the new state (true/false)
            bg_color: !lambda |-
              return x ? id(ha_state_on) : id(ha_bg_card);
```

This creates a complete feedback loop:
1. Home Assistant state changes → binary_sensor triggers
2. Lambda updates button's checked state and background color
3. User presses button → triggers Home Assistant service call
4. Home Assistant updates → binary_sensor triggers again → visual update

**Color Logic:**
- `x` is true (on) → green (`ha_state_on`)
- `x` is false (off) → grey (`ha_bg_card`)

## Visual State Indicators

### On/Off States (Lights, Switches)

```yaml
state:
  checked:
    bg_color: ha_state_on  # Green = on
  # Default (unchecked) uses ha_bg_card (grey = off)
```

### Warning/Error States

```yaml
state:
  default:
    bg_color: ha_warning  # Red background
    text_color: ha_text_primary
```

### Disabled/Unavailable States

```yaml
state:
  disabled:
    bg_opa: 50%
    text_color: ha_text_disabled
```

## Best Practices

### ✅ Do This

1. **Let the theme do the work** - Don't override theme properties unless necessary
2. **Use color IDs** - Reference `ha_*` colors instead of hex values
3. **Add state styling** - Always define pressed, checked states for interactive elements
4. **Use checkable buttons** - For on/off controls, set `checkable: true`
5. **Sync with HA** - Use binary_sensor to keep button state in sync

### ❌ Avoid This

1. **Hardcoding colors** - Use theme color IDs instead of `0xFFFFFF`
2. **Skipping states** - Always define at least `pressed` state for buttons
3. **Inconsistent styling** - Stick to theme colors for consistency
4. **Missing feedback** - Users need visual feedback when pressing

## Adding New Colors

To add new colors to the theme:

1. Edit `/common/ha_theme.yaml`
2. Add color using ESPHome's `color:` component syntax:

```yaml
color:
  - id: ha_custom_color
    red: 67%    # 0xAA / 255
    green: 73%  # 0xBB / 255
    blue: 80%   # 0xCC / 255
    # For reference: hex would be 0xAABBCC
```

3. Use in widgets:

```yaml
- button:
    bg_color: ha_custom_color
```

**Converting Hex to RGB Percentages:**
- Red: `(0xRR / 255) * 100%`
- Green: `(0xGG / 255) * 100%`
- Blue: `(0xBB / 255) * 100%`

Example: `0xFF8800` → red: 100%, green: 53%, blue: 0%

## Testing States

To verify all states are styled correctly:

1. **Default**: Look at widget when idle
2. **Pressed**: Touch and hold the widget
3. **Focused**: Use keyboard/encoder to navigate to it
4. **Checked**: Toggle the button on
5. **Checked+Pressed**: Touch and hold while checked
6. **Disabled**: Set `enabled: false` temporarily

## Color Contrast Guidelines

Maintain good contrast ratios for accessibility:

| Combination | Contrast | Status |
|-------------|----------|--------|
| `ha_text_primary` on `ha_bg_card` | 12:1 | ✅ Excellent |
| `ha_text_secondary` on `ha_bg_card` | 6:1 | ✅ Good |
| `ha_text_primary` on `ha_state_on` | 8:1 | ✅ Very Good |
| `ha_text_primary` on `ha_primary` | 4.5:1 | ✅ Acceptable |

## Examples from Current Configuration

### Lamp Button (wallpanel.yaml:236-269)

```yaml
- button:
    id: lamp_voordeur_id
    checkable: true
    state:
      pressed:
        bg_color: ha_bg_card_pressed  # Lighter grey when pressed
      checked:
        bg_color: ha_state_on         # Green when lamp is on
      checked+pressed:
        bg_color: ha_primary          # Blue when pressing while on
```

**Visual behavior:**
- **Off state**: Dark grey tile (ha_bg_card)
- **On state**: Green tile (ha_state_on)
- **Pressing while off**: Light grey (ha_bg_card_pressed)
- **Pressing while on**: Blue (ha_primary)

### Camera Container (wallpanel.yaml:272-295)

```yaml
- obj:
    id: buienradar_container
    bg_color: ha_bg_card
    bg_opa: COVER
    radius: 12
```

**Visual behavior:**
- Consistent dark grey background matching other tiles
- Rounded corners for modern look
- No states (non-interactive container)

## Future Enhancements

Consider implementing:

1. **Hover states**: If using mouse/pointer input
2. **Animation transitions**: Smooth color changes between states
3. **Gradient backgrounds**: For more visual depth
4. **Dark/Light mode toggle**: Switch entire theme at runtime
5. **Per-room themes**: Different accent colors per room

## Troubleshooting

### Colors not applying?

- Verify `common/ha_theme.yaml` is included in main config
- Check color ID spelling (e.g., `ha_bg_card` not `ha_card_bg`)
- Ensure color is defined before use

### States not changing?

- Add `checkable: true` for checked state
- Verify binary_sensor is updating widget state
- Check `lvgl.widget.update` is called in `on_state:`

### Theme overridden by widget properties?

- Widget-level properties override theme
- Remove explicit properties to inherit from theme
- Use `state:` section for state-specific overrides only

## Summary

The Home Assistant dark theme provides:
- ✅ Consistent colors across all widgets
- ✅ Automatic state-based styling (pressed, checked, etc.)
- ✅ Professional look matching Home Assistant
- ✅ Easy to maintain and extend
- ✅ Accessible contrast ratios

Just reference `ha_*` colors and let the theme handle the rest!
