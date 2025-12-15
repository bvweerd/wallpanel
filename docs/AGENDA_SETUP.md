# Agenda Setup voor ESPHome Display

## Overzicht

De agenda widget toont de komende afspraken uit een Home Assistant calendar entity in een visuele lijst op het ESPHome display.

**Features:**
- Toont maximaal 6 events
- Events van de komende 2 dagen
- Datum labels: "Vandaag", "Morgen", of "Ma 14/11"
- Tijd of "Hele dag" voor all-day events
- Tekst wordt automatisch ingekort als het te lang is
- Updates elke 5 minuten

## Vereisten

- Python 3 met Pillow (PIL) geïnstalleerd in Home Assistant
- Een calendar entity in Home Assistant (bijv. `calendar.gezamenlijke_agenda`)
- `jq` geïnstalleerd voor JSON parsing
- `date` command (standaard aanwezig in Linux)

## Installatie Stappen

### 1. Installeer Python Pillow (indien nog niet gedaan)

```bash
pip install Pillow
```

### 2. Kopieer Scripts naar Home Assistant

Kopieer de volgende bestanden naar `/config/scripts/`:

```bash
cp update_agenda.py /config/scripts/
cp update_agenda.sh /config/scripts/
chmod +x /config/scripts/update_agenda.sh
chmod +x /config/scripts/update_agenda.py
```

### 3. Update het Shell Script

Bewerk `/config/scripts/update_agenda.sh` en pas aan:

```bash
HA_TOKEN="YOUR_LONG_LIVED_ACCESS_TOKEN"
HA_URL="https://homeassistant.jvanw.nl"  # Of http://homeassistant.local:8123
CALENDAR_ENTITY="calendar.gezamenlijke_agenda"  # Pas aan naar jouw calendar
```

### 4. Voeg Shell Command toe aan Home Assistant

Voeg toe aan `configuration.yaml`:

```yaml
shell_command:
  update_agenda: /config/scripts/update_agenda.sh
```

### 5. Maak Automation aan

Voeg toe aan `configuration.yaml` of via UI:

```yaml
automation:
  - alias: "Update Agenda Display"
    trigger:
      # Update elke 5 minuten
      - platform: time_pattern
        minutes: "/5"
      # Update bij HA start
      - platform: homeassistant
        event: start
      # Update bij wijziging calendar
      - platform: state
        entity_id: calendar.gezamenlijke_agenda
    action:
      - service: shell_command.update_agenda
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
./update_agenda.sh
```

Controleer of `/config/www/agenda.png` is aangemaakt.

### 8. Verifieer in ESPHome

De ESPHome configuratie is al bijgewerkt. Upload de firmware en de agenda zou zichtbaar moeten zijn in Card 3.

## Configuratie Aanpassen

### Aantal dagen en events

In `update_agenda.py`:

```python
DAYS_TO_SHOW = 2       # Aantal dagen vooruit
MAX_EVENTS = 6         # Maximum aantal events
```

In `update_agenda.sh`:

```bash
END_DATE=$(date -u -d "+2 days" +"%Y-%m-%dT%H:%M:%S")  # Pas "+2 days" aan
```

### Font sizes

In `update_agenda.py`:

```python
font_title = get_font(14)   # Titel "Agenda"
font_time = get_font(11)    # Tijd en datum labels
font_event = get_font(12)   # Event beschrijving
```

### Kleuren

In `update_agenda.py`:

```python
COLOR_BG = (26, 26, 28)           # Achtergrond
COLOR_TEXT_PRIMARY = (255, 255, 255)   # Event tekst
COLOR_TEXT_SECONDARY = (156, 163, 175) # Tijd/datum
COLOR_ACCENT = (0, 122, 255)      # Datum headers (Vandaag, Morgen)
```

### Update interval

In `wallpanel.yaml`:

```yaml
update_interval: 5min  # Wijzig naar gewenste interval
```

In automation trigger:

```yaml
- platform: time_pattern
  minutes: "/5"  # Wijzig naar gewenst interval
```

## Troubleshooting

### Image wordt niet weergegeven

- Controleer ESPHome logs voor errors
- Verifieer dat `/config/www/agenda.png` bestaat
- Check dat image bereikbaar is: `http://192.168.2.2:8123/local/agenda.png`

### Geen events zichtbaar

Controleer calendar entity:

```bash
# Via Developer Tools > States in HA
# Zoek naar: calendar.gezamenlijke_agenda
```

Test calendar.get_events service:

```yaml
service: calendar.get_events
data:
  entity_id: calendar.gezamenlijke_agenda
  start_date_time: "2025-11-14T00:00:00"
  end_date_time: "2025-11-16T23:59:59"
```

### Script errors

```bash
# Test met verbose logging:
bash -x /config/scripts/update_agenda.sh

# Check Python script met dummy data:
echo '[]' | python3 /config/scripts/update_agenda.py
```

### Verkeerde timezone

Het script gebruikt `Europe/Amsterdam` timezone. Pas aan in `update_agenda.py`:

```python
local_tz = ZoneInfo('Europe/Amsterdam')  # Of jouw timezone
```

## Layout

De agenda wordt getoond met:

```
Agenda
--------------
Vandaag
09:00  Meeting met team
14:30  Doktersafspraak

Morgen
Hele dag  Vakantie
```

- **Headers**: Blauw accent voor "Vandaag", "Morgen", of datum
- **Tijd**: Grijs, links uitgelijnd
- **Event**: Wit, rechts van tijd
- **Lange events**: Worden ingekort met "..."
