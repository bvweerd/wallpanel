# ESPHome LVGL Wallpanel

A smart home wall-mounted touchscreen control panel built with ESPHome and LVGL, designed to interface with Home Assistant.

## Overview

This project creates a modern, responsive touchscreen interface for controlling smart home devices, displaying sensor data, and providing interactive home automation controls through a sleek wall panel.

## Hardware

- **Microcontroller**: ESP32-P4 (400MHz CPU, 16MB flash, 512KB RAM with PSRAM)
- **Display**: JC1060P470 MIPI DSI (1024x600 resolution, ~30 FPS)
- **Touch**: GT911 capacitive touchscreen controller (I2C)
- **Network**: ESP32-C6 coprocessor (WiFi via esp32_hosted)
- **Backlight**: PWM-controlled via GPIO23

## Features

- **Home Assistant Integration**: Bidirectional control and state synchronization via API
- **Touch Interface**: Tile-based button layout with Material Design Icons
- **Auto Sleep/Wake**: Configurable idle timeout (default 90s) with touch-to-wake
- **HA Dark Theme**: Complete Home Assistant dark theme with state-based styling (pressed, checked, focused, disabled)
- **OTA Updates**: Remote firmware updates with encryption
- **Modular Configuration**: Reusable color palettes, icon libraries, and theme system

## Architecture

```
ESP32-P4 (Main Controller)
    ├── ESP32-C6 (WiFi Coprocessor) → Home Assistant
    ├── MIPI DSI Display (1024x600)
    │   └── PWM Backlight Control
    ├── GT911 Touchscreen (I2C)
    │   └── Touch Events → LVGL
    └── LVGL Graphics Engine
        ├── Renders UI Pages/Widgets
        ├── Processes Touch Input
        └── Updates based on HA Entity States
```

## Project Structure

```
wallpanel/
├── wallpanel.yaml          # Main ESPHome configuration
├── common/
│   ├── colors.yaml        # Legacy color palette (23 colors)
│   ├── images.yaml        # MDI icons (20 icons, 32x32 RGB565)
│   └── ha_theme.yaml      # Home Assistant dark theme with state styles
├── README.md              # This file
├── AGENTS.md              # Agent instructions and configuration guide
└── THEME.md               # Theme system documentation
```

## Technology Stack

- **ESPHome**: ESP32 microcontroller framework (YAML-based)
- **LVGL**: Light and Versatile Graphics Library for embedded UI
- **ESP-IDF**: Espressif IoT Development Framework
- **Home Assistant**: Smart home platform integration
- **Material Design Icons**: Icon library for UI elements

## Current Status

**Early Development** - Foundation complete with:
- ✅ Hardware configuration fully defined
- ✅ Display and touch drivers configured
- ✅ Home Assistant API connection established
- ✅ Color palette and icon library created
- ✅ One working control: "Lamp Voordeur" (front door lamp)
- 🔄 Ready for expansion with additional entities and UI pages

## Configuration

The main configuration file (`wallpanel.yaml`) orchestrates:
- Hardware setup (display, touch, WiFi)
- LVGL graphics engine with Home Assistant dark theme
- Home Assistant entity bindings
- UI layout and theming
- Power management (sleep/wake)

Shared resources in `common/`:
- **ha_theme.yaml**: Home Assistant dark theme with 15 colors and state-based styling
- **colors.yaml**: Legacy color definitions (neutral, green, blue, red, orange, yellow)
- **images.yaml**: MDI icon resources for various functions (audio, HVAC, lighting, controls)

### Theme System

The wallpanel uses a comprehensive Home Assistant dark theme that automatically applies to all widgets:
- **Consistent colors** matching Home Assistant's official dark theme
- **State-based styling** for pressed, checked, focused, and disabled states
- **Visual feedback** for all user interactions
- **Easy customization** via theme color IDs

See `THEME.md` for complete documentation on using and customizing the theme.

## Future Development

- Additional Home Assistant entity integrations
- Multiple UI pages for different rooms/functions
- Sensor data displays (temperature, humidity, etc.)
- Scene and automation controls
- Weather information
- Calendar and notifications
