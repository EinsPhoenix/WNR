# WNR - Schulprojekt

Dieses Projekt ist ein **Schulprojekt**, das verschiedene Kommunikationsprotokolle und Technologien demonstriert.

## Verwendete Technologien

Das Projekt nutzt folgende Kommunikationsprotokolle und Technologien:
- **OPC UA** - für sensor Kommunikation
- **MQTT** - für livedaten
- **REST** - für APIs
- **TCP** - für direkte Socket-Kommunikation
- **WebSockets** - für Video

Technologien:
- **Frontend** - SventKit
- **Backend** - Python
- **Connector** - Rust
- **Database** - Neo4j


## Quickstart

Um das Projekt zu starten, folgen Sie bitte den Anleitungen in dieser Reihenfolge:

### 1. Datenbank Connector
Zuerst muss die Datenbankverbindung eingerichtet werden:
- [Info-Files-Database\Database.md](Info-Files-Database/Database.md)

### 2. Backend
Anschließend das Backend starten:
- [Robot\README.md](Robot/README.md)

### 3. Frontend
Zum Schluss das Frontend einrichten und starten:
- [WNR-Frontend\README.md](WNR-Frontend/README.md)

**Wichtig:** Die Reihenfolge muss eingehalten werden, da die Komponenten aufeinander aufbauen.

## License
Dieses Projekt steht unter der Apache License 2.0, jedoch mit der folgenden zusätzlichen Einschränkung:

### Zusätzlicher Zusatz zur Apache 2.0-Lizenz (Commons Clause)
"Der Lizenznehmer darf diese Software oder daraus abgeleitete Werke nicht für kommerzielle Zwecke nutzen, verkaufen oder lizenzieren, es sei denn, er hat die ausdrückliche schriftliche Genehmigung des Urhebers erhalten."