# Buienradar Animatie Setup

## Overzicht

De buienradar widget toont nu een geanimeerde radar in plaats van een statisch beeld. Het script extraheert alle frames uit de GIF en ESPHome speelt deze af als een slideshow.

## Hoe het werkt

1. **update_buienradar.sh** downloadt de GIF en extraheert alle frames (typisch 10 stuks)
2. **ESPHome** laadt alle frames in het geheugen als aparte online_image componenten
3. **Interval timer** (500ms) cyclet door de frames voor een vloeiende animatie

## Configuratie

### Animatiesnelheid aanpassen

In `wallpanel.yaml`:

```yaml
- interval: 1s  # Pas aan: 500ms = sneller, 2s = langzamer
```

**Aanbevolen snelheden:**
- **500ms**: Snelle animatie (2 frames/sec)
- **1s**: Normale animatie (1 frame/sec) - **standaard**
- **2s**: Langzame animatie (0.5 frame/sec)

### Aantal frames

Het script extraheert 5 frames uit de GIF (elke 2e frame voor betere prestaties).

### Image formaat

In `update_buienradar.sh`:

```bash
-vf "select='not(mod(n\,2))',scale=200:140"  # 5 frames, 200x140 pixels
```

Om terug te gaan naar 10 frames van 314x220 (meer geheugen):
```bash
-vf "scale=314:220"  # Alle frames, origineel formaat
```

## Geheugengebruik

De huidige configuratie is geoptimaliseerd voor prestaties:

**Geheugen per frame**: ~56KB (RGB565, 200x140 pixels)
**Totaal**: ~280KB voor 5 frames

Dit is een verbetering t.o.v. de oude configuratie (10 frames van 314x220 = 2.2MB).

Als je nog meer geheugen wilt besparen:
1. Gebruik RGB332 in plaats van RGB565 (lagere kwaliteit, halveert geheugen)
2. Verklein verder naar 160x112

## Installatie

### 1. Update het script

Het `update_buienradar.sh` script is al bijgewerkt. Test het:

```bash
cd /config/scripts
./update_buienradar.sh
```

Controleer of frames zijn aangemaakt:

```bash
ls -lh /config/www/buienradar_frame_*.png
```

Je zou moeten zien:
```
buienradar_frame_1.png
buienradar_frame_2.png
...
buienradar_frame_10.png
```

### 2. Upload ESPHome firmware

De configuratie is al bijgewerkt. Upload de firmware naar je ESP32.

### 3. Verifieer

Na het uploaden zou je een vloeiend bewegend radarbeeld moeten zien dat elke 500ms van frame wisselt.

## Troubleshooting

### Animatie loopt niet

Check ESPHome logs:
```
[lvgl:000] Image draw cannot open the image resource
```

Dit betekent dat één of meer frames niet beschikbaar zijn.

Oplossing:
1. Controleer of alle frames zijn gedownload
2. Verifieer URL's in browser: `http://192.168.2.2:8123/local/buienradar_frame_1.png`

### Geheugen errors

```
[esp32:000] Failed to allocate memory
```

Oplossing:
1. Reduceer aantal frames tot 5
2. Verklein image size
3. Gebruik alleen de even frames (2,4,6,8,10)

### Frames hebben verschillende groottes

Als de GIF frames verschillende groottes heeft, kan dat zorgen voor vreemde weergave.

Oplossing: Voeg `-vf "scale=314:220:force_original_aspect_ratio=decrease,pad=314:220:(ow-iw)/2:(oh-ih)/2"` toe aan ffmpeg command.

### Animatie is niet smooth

Als de animatie stottert:
1. Verhoog interval naar 1000ms
2. Reduceer aantal frames
3. Check CPU gebruik van ESP32

## Animatie pauzeren

Om de animatie te stoppen op één frame, comment de interval timer uit in `wallpanel.yaml`:

```yaml
# - interval: 500ms
#   then:
#     - lambda: |-
#         ...
```

Of stel een zeer lang interval in:
```yaml
- interval: 60s  # Update maar 1x per minuut
```

## Terugdraaien naar statisch beeld

Als je toch liever een statisch beeld wilt:

1. In `update_buienradar.sh`, voeg toe aan het einde:
```bash
cp /config/www/buienradar_frame_5.png /config/www/buienradar.png
```

2. In `wallpanel.yaml`, gebruik:
```yaml
- url: http://192.168.2.2:8123/local/buienradar.png
  id: buienradar_static
```

3. Verwijder de interval timer voor animatie
