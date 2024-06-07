
= Anforderungsanalyse

== Funktionale Anforderungen

+ *Benutzerregistrierung und -anmeldung*
  - Das System soll eine sichere Authentifizierungsmethode bereitstellen, bei der sich Benutzer über E-Mail und Passwort
    registrieren und anmelden können.
+ *Filteroptionen für Software*
  - Das System soll die Möglichkeit bieten, Software anhand verschiedener Kriterien zu filtern, einschließlich:
    - *Tags*: z.B. Kategorien, Funktionen, Technologien.
    - *Preis*: Die Preise sollen in einem anpassbaren Intervall dargestellt werden.
    - *Lizenz*: Verschiedene Lizenztypen (z.B. Open Source, kommerziell).
    - *Unterstützte Betriebssysteme*: Auswahl der Betriebssysteme, die die Software unterstützt.
    - *Weitere Kriterien*: Andere relevante Filtermöglichkeiten, wie z.B. Anbieter, Bewertungen, etc.
+ *Preisintervall-Anpassung*
  - Das System soll die Möglichkeit bieten, das Preisintervall der angezeigten Softwareprodukte für einen gewünschten
    Zeitraum anzupassen.
  - Falls eine Software nur für einen anderen Zeitraum als den ausgewählten angeboten wird, soll der Preis automatisch auf
    den gewünschten Zeitraum umgerechnet und angezeigt werden.
+ *Anzeige und Interaktion*
  - Das System soll es ermöglichen, durch einen Klick auf eine Softwarekarte zusätzliche Informationen über die Software
    anzuzeigen.
  - Diese zusätzlichen Informationen sollen Details wie Beschreibung, Features, Preisstruktur, Lizenzinformationen und
    unterstützte Betriebssysteme umfassen.
+ *Preisanpassung und Vergleich*
  - Das System soll in der Lage sein, die Preise verschiedener Softwareprodukte für den ausgewählten Zeitraum zu
    vergleichen und dementsprechend anzuzeigen.
+ *Abonnements für Drittanbieter-Software*
  - Das System soll es Benutzern ermöglichen, Abonnements für verschiedene Drittanbieter-Software über eine einheitliche
    Web-Benutzeroberfläche abzuschließen.
+ *Servicepläne erstellen*
  - Das System soll Benutzern die Möglichkeit bieten, Servicepläne basierend auf den abonnierten Softwareprodukten zu
  erstellen.
+ *Verwaltung von Agents*
  - Das System soll Funktionen zur Einrichtung, Konfiguration und Verwaltung von Agents bereitstellen (Computerprogramme,
  die zu gewissem eigenständigem und eigendynamischem Verhalten fähig sind).
+ *Automatisches Ausrollen von Software*
  - Das System soll in der Lage sein, Software automatisch auf Agents mithilfe von Ansible Playbooks basierend auf den
    ausgewählten Serviceplänen auszurollen.
+ *Überwachung und Verwaltung von installierter Software*
  - Das System soll eine Benutzeroberfläche bieten, über die alle installierten Softwareprodukte auf den Agents überwacht
    und verwaltet werden können.
+ *Abonnementverwaltung*
  - Das System soll Benutzern die Möglichkeit bieten, ihre Abonnements zu aktualisieren, zu ändern oder zu kündigen.
  - Das System soll in der Lage sein, Kündigungen von Abonnements, die über andere Software (z.B. Stripe) durchgeführt
    werden, zu synchronisieren, sodass das Abonnement auch in der Anwendung als gekündigt gekennzeichnet wird.
+ *Integration von Zahlungsabwicklungen*
  - Das System soll sichere Zahlungsgateways integrieren, um die Zahlungsabwicklung für die Abonnements zu ermöglichen.
+ *Berichtsgenerierung*
  - Das System soll Berichte über Abonnementnutzung, Installationen und andere relevante Metriken für Benutzer und
    Administratoren generieren können.
+ *Unterstützung für Mehrbenutzerumgebungen*
  - Das System soll Mehrbenutzerumgebungen mit verschiedenen Rollen und Berechtigungen unterstützen, z. B. Administrator,
    Benutzer und Supportpersonal.
+ *Einordnung der Software in spezifische Tags und Gruppen*
  - Das System soll es ermöglichen, Softwareprodukte in spezifische Tags einzuordnen, die ihrer Funktion und Beschreibung
    entsprechen, um einen schnellen und einfachen Vergleich zu ermöglichen.
  - Zusätzlich soll das System die Möglichkeit bieten, Software in Gruppen zu kategorisieren, um eine strukturierte
    Übersicht zu gewährleisten.
  

== Nichtfunktionale Anforderungen

+ *Sicherheit*
  - Das System soll robuste Sicherheitsmaßnahmen implementieren, einschließlich Datenverschlüsselung, sicherer
    Authentifizierung und Autorisierung, um Benutzerdaten und sensible Informationen zu schützen. Dies umfasst:
    - Nutzung von HTTPS für die sichere Übertragung von Daten.
    - Speicherung von Passwörtern als gehashte und gesalzene Werte.
    - Auslagerung von Zahlungsinformationen an Stripe, um die Sicherheit und Integrität der Zahlungsabwicklung zu
      gewährleisten.
+ *Benutzerfreundlichkeit*
  - Die Benutzeroberfläche soll intuitiv und benutzerfreundlich gestaltet sein, um eine einfache Navigation und
    Interaktion für Benutzer zu ermöglichen. Das Design soll den Nutzern eine nahtlose und angenehme Benutzererfahrung
    bieten.
+ *Performance*
  - Die Plattform soll schnell und reaktionsschnell sein, um eine effiziente Interaktion mit den Benutzern zu ermöglichen.
    Dies ist besonders wichtig während der Softwareinstallation und -verwaltung, um lange Wartezeiten und Verzögerungen zu
    vermeiden.
+ *Kompatibilität*
  - Die Anwendung soll mit verschiedenen Betriebssystemen, Browsern und Geräten kompatibel sein, um eine breite
    Benutzerbasis zu erreichen. Sie soll plattformübergreifend funktionieren und sowohl auf Desktop- als auch auf mobilen
    Geräten eine optimale Leistung bieten.
+ *Datenschutz und Compliance*
  - Das System soll relevante Datenschutzbestimmungen und Branchenstandards einhalten, um die Privatsphäre der Benutzer zu schützen und rechtliche Anforderungen zu erfüllen. Dies umfasst die Integration von Stripe zur Sicherstellung der Konformität mit Zahlungsrichtlinien und Datenschutzgesetzen.