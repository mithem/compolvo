= Architektur

== Allgemein

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

== Verwendete Libraries

=== Backend

Für die grundlegende Server-Umgebung wird das Framework Sanic mit Python verwendet, da aufgrund vorheriger Kenntnisse so in kurzer Zeit ein funktionsfähiger Server implementiert werden kann.
Außerdem ist Sanic dafür gut geeignet, da es asynchrones Programmieren unterstützt, was für die Verarbeitung von vielen gleichzeitigen Anfragen nötig ist.
Zudem ist es allgemein recht schnell.
Damit wird die REST-ähnliche Schnittstelle implementiert, auf welche das Frontend zugreift und die kritische Geschäftslogik beinhaltet.
Zum Zugriff auf die Datenbank wird Tortoise ORM verwendet, da dies eine simple Schnittstelle zur Datenbank bereitgestellt, welche das Datenmodell in Python-Objekten abbildet, welche unmittelbar zum Management der Daten verwendet werden können.
So ist keine (eigene) Zwischenebene nötig, die die Daten mittels SQL-Statements aus der Datenbank liest und primitiv in Objekte und umgekehrt SQL-Statements umwandelt.
Zudem bietet die dadurch gewonnene _type safety_ schnellere Entwicklung bei geringerer Fehleranfälligkeit.

==== Stripe
Mit der Möglichkeit für Benutzer, Software zu abonnieren, ist auch eine Zahlungsabwicklung nötig, um überhaupt Einnahmen aus dem geschaffenem Mehrwert generieren zu können.
Dazu wird der Zahlungsdienstleistungsanbieter Stripe verwendet.
Dieser ist geeignet, da durch seine Nutzung vollständig auf das Speichern von Zahlungsinformationen und besonders auf die Integration mit verschiedenen Banken und anderen Zahlungsmöglichkeiten verzichtet werden kann.
Dennoch bietet Stripe eine hohe Flexibilität durch verschiedene Abrechnungsmodelle (von denen aktuell technisch nur eins genutzt wird, jedoch zukünftig weitere Abonnementsmodelle ermöglicht).
Diese ist insbesondere daher nötig, da die Abonnements, die der Nutzer über Stripe abschließen kann, dynamisch vom Inhalt der Datenbank (der angebotenen Software) abhängen.
Entsprechend ist Stripe auch vorteilhaft, weil es über eine robuste und einfach nutzbare Python-API verfügt, was für die Integration ins Backend nötig ist.

==== WebSockets
Für die Kommunikation zwischen Server und Agent, als auch optional zwischen Server und Frontend, werden WebSockets verwendet.
Deren charakteristische Eigenschaft, eine durchgehende TCP-Verbindung, die über "lange" Zeit (verglichen mit gewöhnlichen HTTP-Anfragen) aufrechterhalten wird, ist aus folgendem Grund für die Server-Agent-Kommunikation nötig:
Die Agents können sich z.B. im Firmennetz des Kunden befindet, und sind daher nicht direkt vom Internet erreichbar.
Entsprechend können keine Befehle vom Server an die Agents geschickt werden, um z.B. die gewünschte Software zu installieren.
Die Verwendung von WebSockets löst dieses Problem wie folgt.
Der Agent baut eine Verbindung zum Server auf, und hält diese aufrecht.
Der Server kann dann über diese bestehende Verbindung mit dem Agent kommunizieren (und natürlich andersherum).
Sollte die Verbindung abbrechen, baut der Agent sie automatisch wieder auf.

Außerdem sind WebSocket-Verbindungen auch für die Kommunikation zum Frontend geeignet.
Sie bieten die Möglichkeit für eine push-basierte Kommunikation, d.h. der Server kann dem Frontend Daten senden, ohne dass das Frontend explizit in regelmäßigen Abständen danach fragen muss.
Dies verbessert die User Experience, indem das Frontend in passenden Bereichen automatisch aktualisiert wird.
Insbesondere der Status der Agents wird so unmittelbar vom Agent an den User übermittelt, ohne dass dieser die Seite neu laden muss, was insbesondere bei längeren Installationsvorgängen nützlich ist, und Verwirrung des Users vermeidet, dass sich die angezeigten Daten nicht ändern.

=== Frontend

Für das Frontend wird Vue.js verwendet, da damit dynamische _single page applications_ erstellt werden können.
Dies ist sinnvoll, damit nicht bei jeder Navigationsaktion auf der Seite (bspw. das Klicken auf "compare" in der Navigationsleiste) die gesamte Seite neu geladen werden muss.
Die dadurch verringerten Ladezeiten und verbesserte Responsiveness verbessert die allgemeine User Experience.
Es werden außerdem Komponenten vom Framework Vuetify verwendet, um ein einheitliches und ansprechendes Design zu gewährleisten, ohne jedes Element von Grund auf neu entwickeln zu müssen, und somit Aufwand zu sparen.
Die damit kombinierte Verwendung von (Google) Material Design Icons verbessert ebenso die Benutzererfahrung, indem die Knöpfe, die solche Icons verwenden, schnell und intuitiv durch die dem Nutzer häufig bereits bekannten simplen Icons verstanden werden können.

=== Agent

Der Agent ist in Python implementiert, da dies die Sprache ist, in der bereits Erfahrung vorlag, und (somit) eine Entwicklung in kurzer Zeit möglich ist.
Zur Installation der Software selber wird Ansible verwendet, da dies ein breites Angebot an Diensten einbindet, über welche Software installiert werden kann.
Dafür muss auf dem Agent ein lokaler Ansible Controller laufen, da ein Ansible Controller an einem Compolvo-Server nicht auf die Agents per SSH zugriefen könnte (damit werden die Ansible-Befehle übertragen).
Da allerdings der Ansible Controller nur UNIX-ähnliche Betriebssysteme (MacOS und viele Linux-Distributionen) unterstützt, kann keine Software durch den Agent auf Windows-Geräten installiert werden.

== Datenbankmodell

Die folgende Abbildung zeigt das Datenbankschema:
#figure(image("db-architecture-v2.png"), caption: "Datenbankmodell")