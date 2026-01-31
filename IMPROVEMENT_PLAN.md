# Verbeterplan ESPHome Wallpanel YAML

## Samenvatting
Na analyse van de ~2600 regels YAML zijn er **6 significante verbeteringen** mogelijk die:
- Code met ~200 regels verkorten
- Prestaties verbeteren (minder CPU cycles)
- Onderhoud vereenvoudigen
- ESPHome standaard componenten beter benutten

---

## 1. LVGL `animimg` voor Buienradar Animatie (HOGE PRIORITEIT)

### Probleem
Huidige implementatie gebruikt 10 aparte if-statements (regels 322-391) die elke 500ms draaien:
```yaml
- if:
    condition:
      lambda: 'return id(buienradar_current_frame) == 1;'
    then:
      - lvgl.image.update: ...
# ... herhaald 10x
```

### Oplossing
ESPHome LVGL heeft een ingebouwd `animimg` widget dat precies hiervoor bedoeld is:
```yaml
# In LVGL widgets:
- animimg:
    id: buienradar_widget
    src:
      - buienradar_frame_1
      - buienradar_frame_2
      # ... etc
    duration: 5000ms  # 10 frames x 500ms
    repeat_count: -1  # Oneindig herhalen
```

### Voordeel
- **~70 regels minder code**
- Geen interval timer nodig
- Hardware-geoptimaliseerde animatie
- `buienradar_current_frame` global niet meer nodig

---

## 2. Gedupliceerde Datum/Tijd Lambda (MEDIUM PRIORITEIT)

### Probleem
Identieke lambda code op 2 plekken (regels 218-230 en 263-275):
```yaml
text: !lambda |-
  static const char* dagen[] = {"Zondag", "Maandag", ...};
  # ... 12 regels identieke code
```

### Oplossing
Verplaats naar een enkele `on_time` trigger en verwijder de 60s interval:
```yaml
time:
  - platform: homeassistant
    id: ha_time
    on_time:
      - seconds: 0  # Elke minuut op seconde 0
        then:
          - lvgl.label.update:
              id: header_datetime
              text: !lambda |-
                # ... code hier 1x
```

De huidige `on_time` trigger doet al precies dit - de interval is overbodig.

### Voordeel
- **~15 regels minder code**
- Geen dubbele code om te onderhouden

---

## 3. Online Images met YAML Anchors (MEDIUM PRIORITEIT)

### Probleem
10 identieke buienradar image declaraties (regels 97-166) die alleen verschillen in ID en URL nummer.

### Oplossing
Gebruik YAML anchors voor de gemeenschappelijke configuratie:
```yaml
online_image:
  - &buienradar_base
    type: RGB565
    byte_order: little_endian
    format: PNG
    resize: 314x220
    update_interval: 2min

  - <<: *buienradar_base
    url: http://192.168.2.2:8123/local/esphomefiles/buienradar_frame_1.png
    id: buienradar_frame_1
  - <<: *buienradar_base
    url: http://192.168.2.2:8123/local/esphomefiles/buienradar_frame_2.png
    id: buienradar_frame_2
  # ... etc
```

### Voordeel
- **~50 regels minder code**
- Wijzigingen aan base config werken door naar alle images

---

## 4. Clean Mode Efficiëntie (LAGE PRIORITEIT)

### Probleem
De 1-seconde interval draait altijd, ook als clean mode niet actief is:
```yaml
- interval: 1s
    then:
      - lambda: |-
          if (id(clean_mode_active)) {  # Check elke seconde
```

### Oplossing
Gebruik een `script` met `mode: restart` in plaats van interval:
```yaml
script:
  - id: clean_mode_script
    mode: restart
    then:
      - repeat:
          count: 30
          then:
            - lvgl.label.update:
                id: clean_mode_timer
                text: !lambda |-
                  return str_sprintf("%d", 30 - x);
            - delay: 1s
      - lvgl.widget.hide: clean_mode_overlay

# Activeren:
on_press:
  - script.execute: clean_mode_script
  - lvgl.widget.show: clean_mode_overlay
```

### Voordeel
- Geen CPU cycles wanneer clean mode niet actief is
- `clean_mode_active` en `clean_mode_countdown` globals niet meer nodig
- Duidelijkere logica

---

## 5. Camera Toggle Vereenvoudigen (LAGE PRIORITEIT)

### Probleem
```yaml
- if:
    condition:
      lambda: 'return id(camera_current) == 1;'
    then:
      - lvgl.image.update: ...
- if:
    condition:
      lambda: 'return id(camera_current) == 2;'
    then:
      - lvgl.image.update: ...
```

### Oplossing
```yaml
- interval: 5s
    then:
      - lvgl.image.update:
          id: camera_widget
          src: !lambda |-
            static int cam = 0;
            cam = 1 - cam;  // Toggle 0/1
            return cam ? id(camera1_image) : id(camera2_image);
```

### Voordeel
- **~10 regels minder**
- `camera_current` global niet meer nodig

---

## 6. Ongebruikte Globals Verwijderen (LAGE PRIORITEIT)

### Probleem
Deze globals lijken niet gebruikt te worden:
```yaml
- id: consumption_start
  type: float
  restore_value: yes
  initial_value: '0.0'
- id: production_start
  type: float
  restore_value: yes
  initial_value: '0.0'
```

### Oplossing
Verwijderen (na bevestiging dat ze niet nodig zijn).

---

## Implementatie Volgorde

| # | Verbetering | Impact | Risico | Regels bespaard |
|---|-------------|--------|--------|-----------------|
| 1 | LVGL animimg | Hoog | Laag | ~70 |
| 2 | Datum/tijd deduplicatie | Medium | Geen | ~15 |
| 3 | YAML anchors images | Medium | Geen | ~50 |
| 4 | Clean mode script | Laag | Laag | ~20 |
| 5 | Camera toggle | Laag | Geen | ~10 |
| 6 | Unused globals | Laag | Geen | ~8 |

**Totaal: ~170 regels bespaard**

---

## Aanbeveling

Start met verbeteringen **1, 2, en 3** - deze hebben de meeste impact met minimaal risico. Test na elke wijziging.

Verbetering **1 (animimg)** is de belangrijkste omdat het:
- De meeste code bespaart
- Een ESPHome standaard component gebruikt dat geoptimaliseerd is voor dit doel
- De complexe interval-based animatie logica volledig elimineert
