<p align="center">
  <img src="https://raw.githubusercontent.com/BeGiBue/home-assistant-eaton-ups-card/main/images/eaton-ups-card-icon-160.png?v=2" alt="Eaton UPS Card" width="160">
</p>

<h1 align="center">Eaton UPS Card</h1>

<p align="center">
  Responsive Home-Assistant-Dashboard-Card für eine Eaton 3S 850 USV.
</p>

<p align="center">
  <strong>Version 2.0.1</strong><br>
  <a href="https://github.com/BeGiBue/home-assistant-eaton-ups-card/actions/workflows/validate.yml"><img src="https://github.com/BeGiBue/home-assistant-eaton-ups-card/actions/workflows/validate.yml/badge.svg" alt="HACS validation"></a>
</p>

## Vorschau

**Normalbetrieb**

<img src="https://raw.githubusercontent.com/BeGiBue/home-assistant-eaton-ups-card/main/screenshots/eaton-ups-normal-350-light.png" width="350" alt="Eaton UPS Card im Normalbetrieb: Online, 230 V, 21 Prozent Last">

**Batteriebetrieb**

<img src="https://raw.githubusercontent.com/BeGiBue/home-assistant-eaton-ups-card/main/screenshots/eaton-ups-battery-350-light.png" width="350" alt="Eaton UPS Card im Batteriebetrieb: Versorgung über Akku">

**Alarm: Überlast**

<img src="https://raw.githubusercontent.com/BeGiBue/home-assistant-eaton-ups-card/main/screenshots/eaton-ups-alarm-350-light.png" width="350" alt="Eaton UPS Card mit Überlastalarm: 95 Prozent Last">

## Funktionen

- Theme-sensitive Darstellung für Light Mode, Dark Mode und benutzerdefinierte Themes
- Eingebettetes Eaton-3S-850-Produktbild – keine zusätzliche Bilddatei in Home Assistant erforderlich
- Native Home-Assistant-Entity-Picker im grafischen Karteneditor
- Automatische Auswertung typischer NUT-Statuswerte
- Klick auf Messwerte öffnet den Home-Assistant-Mehr-Informationen-Dialog
- Optimiert für Hochformat und Touch – iPhone, iPad und Raspberry-Pi-Kiosk: Schrift wächst mit der Kartenbreite, große Tippflächen, kein Hover-Zwang
- Last mit Fortschrittsbalken (orange ab 70 %, rot ab 90 %)

## Voraussetzungen und Grenzen

- Eine Home-Assistant-Integration wie NUT muss die benötigten USV-Entitäten bereits bereitstellen; die Karte verbindet sich nicht selbst mit der USV.
- Die Standard-Entity-IDs (siehe vollständiges Beispiel unten) sind Beispiele und müssen zur eigenen Installation passen.
- Nicht verfügbare Werte werden als „—“ angezeigt. Die Karte überwacht und schaltet die USV nicht selbst.

## Installation über HACS

Das Projekt ist im offiziellen HACS-Katalog enthalten. Ein benutzerdefiniertes Repository ist für die reguläre Installation nicht erforderlich.

1. HACS öffnen und nach **Eaton UPS Card** suchen.
2. **Eaton UPS Card** auswählen und installieren.
3. Browser bzw. Home-Assistant-App vollständig neu laden.
4. Die Karte im Dashboard hinzufügen und die Entitäten auswählen.

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=BeGiBue&repository=home-assistant-eaton-ups-card&category=plugin)

### Bestehende Installation aus einem Custom Repository übernehmen

1. Prüfen, dass **Eaton UPS Card** in der HACS-Suche im offiziellen Katalog verfügbar ist.
2. Danach unter **HACS → Benutzerdefinierte Repositories** nur den Eintrag für `BeGiBue/home-assistant-eaton-ups-card` entfernen.
3. Die bestehende Installation **nicht deinstallieren**. Dashboard-Karten, YAML-Konfiguration und vorhandene Ressourcen beibehalten.
4. HACS aktualisieren bzw. die Repository-Informationen neu laden und prüfen, dass die installierte Karte weiterhin erkannt wird und Updates angeboten werden.
5. Nach einem Update das Frontend neu laden und die bestehenden Karten prüfen.

Die Major-Version 2.0.0 kennzeichnet die Aufnahme in den offiziellen HACS-Katalog und bedeutet nicht automatisch Breaking Changes. Der Kartentyp `custom:eaton-ups-card` und die Konfigurationsschlüssel bleiben erhalten; vorhandene Kartenkonfigurationen müssen nicht geändert werden.

## Card hinzufügen

Minimal:

```yaml
type: custom:eaton-ups-card
```

Vollständiges Beispiel:

```yaml
type: custom:eaton-ups-card
name: Eaton 3S 850
status_entity: sensor.ups_status
status_data_entity: sensor.ups_statusdaten
voltage_entity: sensor.ups_ausgangsspannung
load_entity: sensor.ups_last
runtime_entity: sensor.ups_akkulaufzeit
power_entity: sensor.waschkeller_ups_wirkleistung
show_status_data: true
```

Alle Entitäten können auch im grafischen Karteneditor über die Home-Assistant-Entity-Picker geändert werden.

## Optionen

| Option | Werte | Standard | Beschreibung |
|---|---|---|---|
| `scale` | `0.8` – `1.8` | `1` | Skaliert die gesamte Card. Für Kiosk-Displays empfiehlt sich `1.2` – `1.5`. |
| `image_mode` | `background` \| `inline` | `background` | `background`: Gerätebild groß im Hintergrund. `inline`: Gerätebild neben dem Titel. |
| `image` | URL | – | Optionale eigene Bild-URL. Leer = eingebettetes Standardbild. |

Beispiel für ein Kiosk-Display:

```yaml
type: custom:eaton-ups-card
scale: 1.3
image_mode: background
```

## Bild

Das Standardbild der Eaton 3S 850 ist direkt in `eaton-ups-card.js` eingebettet.

Optional kann eine eigene Bild-URL gesetzt werden:

```yaml
image: /local/images/meine_usv.png
```

Kann die eigene Bild-URL nicht geladen werden, fällt die Card auf das eingebettete Standardbild zurück.

Eigene Bild-URLs lädt der Browser direkt. Externe Anbieter sehen dabei die IP-Adresse des Browsers; HTTP-Bilder bieten keine Transportverschlüsselung und können unter HTTPS blockiert werden. Bevorzugt lokale `/local/`-Bilder oder vertrauenswürdige HTTPS-Quellen verwenden und keine Zugangsdaten in Bild-URLs hinterlegen.

## Layout

Bei schmaler Card stehen die vier Messwerte in einem 2×2-Raster, ab ca. 700 px Kartenbreite in einer Reihe:

```text
┌──────────────────────────────────────┐
│ Eaton 3S 850                         │
│ ( ● Online )                BILD     │
│ Alles in Ordnung                     │
├──────────────────┬───────────────────┤
│ Ausgangsspannung │ Last              │
├──────────────────┼───────────────────┤
│ Akkulaufzeit     │ Wirkleistung      │
└──────────────────┴───────────────────┘
```

Die Breite wird über Home Assistants **Layout**-Einstellungen festgelegt; die Card implementiert `getGridOptions()`. Eine feste Höhe gibt es nicht – die Höhe ergibt sich aus dem Inhalt. Die Card meldet Home Assistant ihre Mindesthöhe (`min_rows`); im Layout-Editor lässt sich die Höhe daher nicht kleiner einstellen, als der Inhalt braucht.

## Statusauswertung

Typische NUT-Statuswerte werden automatisch interpretiert:

- `OL` / `ONLINE` → Online / Alles in Ordnung
- `OL CHRG` / `CHARG` → Netzbetrieb / Akku wird geladen
- `OB` / `ON BATTERY` → Batteriebetrieb
- `LB` / `LOW` → Akku niedrig
- `BYPASS` → Bypass
- `OVER` → Überlast
- `FAULT` / `FSD` → Störung
- `OFF` → Ausgeschaltet

Für die Statusauswertung werden `status_entity` und `status_data_entity` gemeinsam berücksichtigt.

## Änderungen

Alle Versionen stehen unter [GitHub Releases](https://github.com/BeGiBue/home-assistant-eaton-ups-card/releases), die Änderungen im Detail in [`CHANGELOG.md`](CHANGELOG.md).

## Hinweise zu Marken

Dieses Projekt ist ein unabhängiges Community-Projekt und steht in keiner Verbindung zu Eaton oder Home Assistant. Es wird weder von Eaton noch von Home Assistant unterstützt oder herausgegeben.

**Eaton** und **Eaton 3S** sind Marken ihrer jeweiligen Rechteinhaber. Das im Repository verwendete Projektlogo ist ein eigenständiges Community-Projektlogo und nicht das offizielle Eaton-Unternehmenslogo.

## Lizenz

GNU Affero General Public License v3.0 (**AGPL-3.0**).

Details stehen in [`LICENSE`](LICENSE).
