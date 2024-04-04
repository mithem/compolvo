# Architektur

## Allgemein

Das System besteht aus 3 Komponenten.

Der _Server_ (Backend) ist für die Geschäftslogik, und Softwaredaten- sowie Benutzerdatenverwaltung zuständig.
Er stellt außerdem die REST-Schnittstelle für das Frontend zur Verfügung.
Er speichert dabei folgende Daten in einer Datenbank:
- Daten zu angebotenen Diensten (Bezeichnung, Preis, Addresse zum Abrufen der Software, etc.)
- Benutzerdaten (Name, Zahlungsabwicklungsdaten, zugehörige Agents)
- Zustand der Agents (welche Software ist in welchem Zustand installiert etc. (z.B. Version, korrupt? etc.)?)
Zur Implementierung soll das Python-Framework Sanic verwendet werden, da dieses einfach zu verwenden, sehr schnell, und ausreichend flexibel für die Verwendung mit der Datenbank ist.
Die Datenbank selber soll eine MariaDB sein, da diese quelloffen ist, und als relationale Datenbank die nötige Flexibilität und Effizienz für das komplexe Datenmodell bereithält.

Das _Frontend_ stellt die Website zur Verfügung, die vom Endbenutzer zur Verwaltung und zum Vergleich von Software verwendet werden kann.
Dafür soll das JavaScript- (bzw. TypeScript-) Framework Vue.js verwendet werden, da hiermit bereits Erfahrungen vorliegen, und somit der Aufwand, ein neues Framework zu lernen, verringert werden kann.

Der _Agent_ läuft auf den jeweiligen Kundenrechnern, um lokale Änderungen an der Konfiguration machen zu können (z.B. Installation von Software (-Updates)).
Agents bauen bei Bedarf Verbindungen zum Server auf, damit dieser Befehle erteilen kann.
Dies ist nötig, da die Agents i.A. nicht vom Internet erreichbar sind (da sie hinter einer Firewall sind).