# Generate Lage - Test Data Generator

**⚠️ Dies ist ein TEST-SKRIPT zum Generieren von Mock-Daten für die Datenbank.**

## Beschreibung

Dieses Python-Skript generiert zufällige Roboter-Daten und sendet sie über TCP an einen Rust-Server. Es dient ausschließlich zu Testzwecken und simuliert Sensordaten mit verschiedenen Parametern.

## Funktionen

- **TCP-Verbindung** zum Rust-Server
- **Authentifizierung** mit Passwort
- **Batch-weise Datenübertragung** in konfigurierbaren Größen
- **Mock-Daten Generation** mit zufälligen Werten:
  - UUID
  - Farben (blue, green, red, yellow, purple, orange, black, white)
  - Sensordaten (Temperatur, Luftfeuchtigkeit)
  - Zeitstempel
  - Energieverbrauch und -kosten

## Konfiguration

### Wichtige Parameter zum Anpassen:

#### 1. Anzahl der Einträge
```python
TOTAL_ENTRIES = 5000  # Gesamtanzahl der zu generierenden Einträge
```

#### 2. Batch-Größe
```python
BATCH_SIZE = 1  # Anzahl Einträge pro Batch
```
**⚠️ WICHTIG: `BATCH_SIZE` darf NICHT größer als 25 sein!**

#### 3. Server-Verbindung
```python
def __init__(self, host="localhost", port=12345):
```
**Für externe Datenbank:** Ändern Sie `"localhost"` zur entsprechenden IP-Adresse:
```python
def __init__(self, host="192.168.1.100", port=12345):  # Beispiel IP
```

## Verwendung

1. **Server starten** (Rust-Datenbank-Server muss laufen)
2. **Konfiguration anpassen** (siehe oben)
3. **Skript ausführen:**
   ```bash
   python generate_lage.py
   ```

## Generierte Datenstruktur

Jeder Eintrag enthält:
- `uuid`: Eindeutige Identifikation
- `color`: Zufällige Farbe
- `sensor_data`: 
  - `temperature`: 15.0-30.0°C
  - `humidity`: 30-80%
- `timestamp`: Fortlaufende Zeitstempel
- `energy_consume`: 0.1-1.0 kWh
- `energy_cost`: 0.005-0.02 €

## Authentifizierung

Standard-Passwort: `1234`

## Fehlerbehandlung

Das Skript behandelt automatisch:
- Verbindungsfehler
- Authentifizierungsfehler
- Übertragungsfehler
- JSON-Parsing-Fehler

## ⚠️ Wichtige Hinweise

- **NUR FÜR TESTS VERWENDEN**
- `BATCH_SIZE` maximal 25
- Server muss vor Ausführung gestartet sein
- Bei externen Servern Host-IP anpassen
- Das Skript wartet 1 Sekunde zwischen den Einträgen