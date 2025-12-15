# Camera Slideshow Setup voor ESPHome Display

## Overzicht

De camera card toont afwisselend snapshots van twee camera's (deurbel en oprit), elke 5 seconden wisselend.

## Features

- Live camera snapshots
- Automatisch wisselen tussen twee camera's (elke 5 seconden)
- Updates elke 10 seconden voor nieuwe snapshots
- Formaat: 314x220 pixels (past in camera card)

## Installatie Stappen

### 1. Kopieer Script naar Home Assistant

```bash
cp update_cameras.sh /config/scripts/
chmod +x /config/scripts/update_cameras.sh
```

### 2. Update het Shell Script

Bewerk `/config/scripts/update_cameras.sh` en pas aan indien nodig:

```bash
HA_TOKEN="YOUR_LONG_LIVED_ACCESS_TOKEN"
HA_URL="https://homeassistant.jvanw.nl"
```

Camera entities zijn:
- `camera.deurbel_snapshots_sub` → camera1.png
- `camera.camera_oprit_snapshots_sub` → camera2.png

### 3. Voeg Shell Command toe aan Home Assistant

Voeg toe aan `configuration.yaml`:

```yaml
shell_command:
  update_cameras: /config/scripts/update_cameras.sh
```

### 4. Maak Automation aan

Voeg toe aan `configuration.yaml` of via UI:

```yaml
automation:
  - alias: "Update Camera Snapshots"
    trigger:
      # Update elke 10 seconden
      - platform: time_pattern
        seconds: "/10"
      # Update bij HA start
      - platform: homeassistant
        event: start
    action:
      - service: shell_command.update_cameras
```

### 5. Herstart Home Assistant

```bash
# Via UI: Developer Tools > YAML > Restart
ha core restart
```

### 6. Test het Script Handmatig

```bash
cd /config/scripts
./update_cameras.sh
```

Controleer of `/config/www/camera1.png` en `/config/www/camera2.png` zijn aangemaakt.

### 7. Upload ESPHome Firmware

De ESPHome configuratie is al bijgewerkt. Upload de firmware.

## Hoe het werkt

1. **Shell script** (`update_cameras.sh`):
   - Downloadt snapshots van beide camera's via HA camera proxy API
   - Converteert JPEG naar PNG
   - Resize naar 314x220 pixels
   - Slaat op in `/config/www/`

2. **ESPHome** (`wallpanel.yaml`):
   - Laadt beide camera images elke 10 seconden (regel 216-229)
   - Global variable houdt bij welke camera actief is (regel 258-261)
   - Interval timer (5s) wisselt tussen camera 1 en 2 (regel 363-383)
   - Camera widget toont de actieve camera (regel 671-686)

## Configuratie Aanpassen

### Wissel interval aanpassen

In `wallpanel.yaml` (regel 363):

```yaml
- interval: 5s  # Pas aan: 3s = sneller, 10s = langzamer
```

**Aanbevolen intervallen:**
- **3s**: Snelle wisseling
- **5s**: Normale wisseling (standaard)
- **10s**: Langzame wisseling

### Update interval snapshots

In `wallpanel.yaml` (regel 222, 228):

```yaml
update_interval: 10s  # Hoe vaak nieuwe snapshots worden opgehaald
```

En in automation trigger:

```yaml
- platform: time_pattern
  seconds: "/10"  # Update elke 10 seconden
```

**Let op**: Frequente updates kunnen belasting geven op de camera's en netwerk.

### Andere camera's gebruiken

In `update_cameras.sh`:

```bash
# Wijzig entity_id naar jouw camera's
curl ... "$HA_URL/api/camera_proxy/camera.YOUR_CAMERA_1" ...
curl ... "$HA_URL/api/camera_proxy/camera.YOUR_CAMERA_2" ...
```

### Image formaat aanpassen

In `update_cameras.sh`:

```bash
-vf "scale=314:220"  # Pas aan naar gewenst formaat
```

En in `wallpanel.yaml`:

```yaml
resize: 314x220  # Moet matchen met card grootte
```

## Troubleshooting

### Camera images worden niet getoond

Controleer:
```bash
# Bestaan de images?
ls -lh /config/www/camera*.png

# Zijn ze bereikbaar?
curl http://192.168.2.2:8123/local/camera1.png -I
```

### Script errors

```bash
# Test handmatig met debug
bash -x /config/scripts/update_cameras.sh

# Check camera proxy API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://homeassistant.local:8123/api/camera_proxy/camera.deurbel_snapshots_sub" \
  -o test.jpg
```

### Images wisselen niet

Check ESPHome logs:
```
[lvgl:000] Image draw cannot open the image resource
```

Verifieer dat beide camera_widget updates werken in de interval timer.

### Zwarte of lege images

- Camera is mogelijk offline
- Check camera entity in HA: Developer Tools > States
- Verifieer dat camera snapshots beschikbaar zijn

## Meer dan 2 camera's

Als je meer camera's wilt toevoegen:

1. **Voeg meer downloads toe** in `update_cameras.sh`:
```bash
curl ... camera.camera_3 ... -o /tmp/camera3.jpg
ffmpeg ... /config/www/camera3.png
```

2. **Voeg online_image toe** in `wallpanel.yaml`:
```yaml
- url: http://192.168.2.2:8123/local/camera3.png
  id: camera3_image
  ...
```

3. **Pas interval timer aan** om door alle camera's te cyclen:
```yaml
- lambda: |-
    int cam = id(camera_current);
    cam++;
    if (cam > 3) cam = 1;  // 3 camera's
    id(camera_current) = cam;
```

4. **Voeg extra if conditions toe**:
```yaml
- if:
    condition:
      lambda: 'return id(camera_current) == 3;'
    then:
      - lvgl.image.update:
          id: camera_widget
          src: camera3_image
```

## Camera resolutie vs. kwaliteit

Camera images worden gecomprimeerd naar RGB565 (16-bit kleur). Voor betere kwaliteit:

- Gebruik hogere resolutie camera's
- Zorg voor goede belichting
- Overweeg een lagere compression rate bij de camera

De snapshots zijn real-time, dus beweging wordt ook getoond!
