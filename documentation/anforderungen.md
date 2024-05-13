# Anforderungsanalyse

## Funktionale Anforderungen

- Benutzerregistrierung und -anmeldung über eine sichere Authentifizierungsmethode wie E-Mail und
  Passwort.
- Möglichkeit für Benutzer, Abonnements für verschiedene Drittanbieter-Software über eine
  einheitliche Web-Benutzeroberfläche abzuschließen.
- Erstellung von Serviceplänen basierend auf den abonnierten Softwareprodukten.
- Verwaltung von Agents (Computerprogramme, die zu gewissem eigenständigem und eigendynamischem
  Verhalten fähig sind), einschließlich der Möglichkeit, Agents einzurichten, zu konfigurieren und
  zu verwalten.
- Automatisches Ausrollen von Software auf Agents mithilfe von Ansible Playbooks basierend auf den
  ausgewählten Serviceplänen.
- Benutzeroberfläche zur Überwachung und Verwaltung aller installierten Software auf den Agents.
- Möglichkeit für Benutzer, ihre Abonnements zu aktualisieren, zu ändern oder zu kündigen.
- Integration von Zahlungsabwicklungen für die Abonnements über sichere Zahlungsgateways.
- Generierung von Berichten über Abonnementnutzung, Installationen und andere relevante Metriken für
  Benutzer und Administratoren.
- Unterstützung für Mehrbenutzerumgebungen mit verschiedenen Rollen und Berechtigungen, z. B.
  Administrator, Benutzer und Supportpersonal.

## Nichtfunktionale Anforderungen

- Sicherheit: Implementierung von robusten Sicherheitsmaßnahmen, einschließlich
  Datenverschlüsselung, sichere Authentifizierung und Autorisierung, um Benutzerdaten und sensible
  Informationen zu schützen (HTTPS, Hashed + salted Passwörter, Auslagerung von
  Zahlungsinformationen an Stripe).
- Benutzerfreundlichkeit: Die Benutzeroberfläche sollte intuitiv und benutzerfreundlich sein, um
  eine einfache Navigation und Interaktion für Benutzer zu ermöglichen.
- Performance: Die Plattform sollte schnell und reaktionsschnell sein, um eine effiziente
  Interaktion mit den Benutzern zu ermöglichen, insbesondere während der Softwareinstallation und
  -verwaltung.
- Kompatibilität: Die Anwendung sollte möglichst mit verschiedenen Betriebssystemen, Browsern und
  Geräten kompatibel sein, um eine breite Benutzerbasis zu erreichen.
- Datenschutz und Compliance: Einhaltung relevanter Datenschutzbestimmungen und Branchenstandards,
  um die Privatsphäre der Benutzer zu schützen und rechtliche Anforderungen zu erfüllen (
  Stripe-Integration).