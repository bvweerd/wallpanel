# Energieprijzen Chart Setup voor ESPHome Display

## Vereisten

- Python 3 met Pillow (PIL) geïnstalleerd in Home Assistant
- `jq` geïnstalleerd voor JSON parsing
- Sensor `sensor.decc_summary_sensors_huidige_verbruiksprijs` met attributes:
  - `net_prices_today` (array)
  - `net_prices_tomorrow` (array)

## Installatie Stappen

### 1. Installeer Python Pillow in Home Assistant

SSH naar je Home Assistant installatie en run:

```bash
# Voor Home Assistant OS/Container:
pip install Pillow

# Of via apk (als je Alpine Linux gebruikt):
apk add py3-pillow
```

### 2. Kopieer Scripts naar Home Assistant

Kopieer de volgende bestanden naar `/config/scripts/`:

```bash
cp update_energieprijzen.py /config/scripts/
cp update_energieprijzen.sh /config/scripts/
chmod +x /config/scripts/update_energieprijzen.sh
chmod +x /config/scripts/update_energieprijzen.py
```

### 3. Update het Shell Script

Bewerk `/config/scripts/update_energieprijzen.sh` en pas aan:

```bash
HA_TOKEN="YOUR_LONG_LIVED_ACCESS_TOKEN"  # Maak aan in Profile > Security
HA_URL="https://homeassistant.jvanw.nl"  # Of http://homeassistant.local:8123
```

### 4. Voeg Shell Command toe aan Home Assistant

Voeg toe aan `configuration.yaml`:

```yaml
shell_command:
  update_energieprijzen: /config/scripts/update_energieprijzen.sh
```

### 5. Maak Automation aan

Voeg toe aan `configuration.yaml` of via UI (Settings > Automations & Scenes):

```yaml
automation:
  - alias: "Update Energieprijzen Chart"
    trigger:
      # Update elke 5 minuten
      - platform: time_pattern
        minutes: "/5"
      # Update bij HA start
      - platform: homeassistant
        event: start
      # Update bij wijziging sensor
      - platform: state
        entity_id: sensor.decc_summary_sensors_huidige_verbruiksprijs
    action:
      - service: shell_command.update_energieprijzen
```

### 6. Herstart Home Assistant

```bash
# Via UI: Developer Tools > YAML > Restart
# Of via CLI:
ha core restart
```

### 7. Test het Script Handmatig

```bash
cd /config/scripts
./update_energieprijzen.sh
```

Controleer of `/config/www/energieprijzen.png` is aangemaakt.

### 8. Verifieer in ESPHome

De ESPHome configuratie is al bijgewerkt. Upload de firmware en de energieprijzen chart zou zichtbaar moeten zijn in de top bar (rechts uitgelijnd).

## Troubleshooting

### Image wordt niet weergegeven

- Controleer ESPHome logs: `[lvgl:000]` errors
- Verifieer dat image bestaat: `ls -lh /config/www/energieprijzen.png`
- Check update_interval in wallpanel.yaml (standaard 5min)

### Script fouten

```bash
# Test Python script met dummy data:
echo '{"net_prices_today":[],"net_prices_tomorrow":[]}' | python3 update_energieprijzen.py

# Check jq installatie:
which jq

# Check curl output:
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://homeassistant.local:8123/api/states/sensor.decc_summary_sensors_huidige_verbruiksprijs
```

### Geen data zichtbaar

Controleer of de sensor attributes de juiste structuur hebben:

```json
{
  "net_prices_today": [
    {"start": "2025-11-14T00:00:00+01:00", "value": 0.123},
    {"start": "2025-11-14T01:00:00+01:00", "value": 0.145}
  ],
  "net_prices_tomorrow": []
}
```

## Kleurcodes

De chart gebruikt drie kleuren:

- **Groen (#22c55e)**: Laagste 20% prijzen (≤ p20)
- **Grijs (#d1d5db)**: Middenprijzen (tussen p20 en p80)
- **Rood (#ef4444)**: Hoogste 20% prijzen (≥ p80)
- **Blauw (#007AFF)**: Huidige tijd indicator (verticale lijn + driehoek)

## Aanpassingen

### Wijzig afmetingen

In `update_energieprijzen.py`:

```python
WIDTH = 648   # Breedte in pixels (2 cards + margin)
HEIGHT = 50   # Hoogte in pixels
BAR_HEIGHT = 18  # Hoogte van de gekleurde bars
```

In `wallpanel.yaml`:

```yaml
resize: 648x50  # Pas aan naar gewenste afmetingen
x: 356          # Pas aan voor positie (1024 - 648 - 20 = 356)
```

### Wijzig tijdvenster

In `update_energieprijzen.py`:

```python
win_start = now - timedelta(hours=4)   # 4 uur terug
win_end = now + timedelta(hours=20)    # 20 uur vooruit
```

### Update interval

In `wallpanel.yaml`:

```yaml
update_interval: 5min  # Wijzig naar gewenste interval (1min, 10min, etc.)
```
