= User Guide

Willkommen im User Guide von Compolvo. Dieses Handbuch führt Sie durch die verschiedenen Seiten und Funktionen der Compolvo-Website, wie in den bereitgestellten Bildern dargestellt.

== Seitenübersicht

=== Startseite

#figure(image("../images/homepage.png"), caption: "Startseite")

- *Beschreibung*: Die Startseite begrüßt Benutzer der Compolvo-Seite mit einem Logo und einer Willkommensnachricht auf Deutsch: "Willkommen auf der Compolvo-Seite!".
  Dies ist eine statische Willkommensseite ohne interaktive Elemente. Um fortzufahren, melden Sie sich bei Ihrem Konto an. Nach dem Login verwenden Sie die Navigationsleiste, um die Website zu erkunden.

---

=== Anmeldeseite

#figure(image("../images/login_page.png"), caption: "Anmeldeseite")

- *Beschreibung*: Diese Seite ermöglicht es Benutzern, sich bei ihren Konten anzumelden.
- *Felder*:
    - *E-Mail*: Geben Sie Ihre registrierte E-Mail-Adresse ein.
    - *Password*: Geben Sie Ihr Passwort ein.
- *Schaltflächen*:
    - *Submit*: Meldet den Benutzer im System an.
    - *No account yet?*: Weiterleitung zur Registrierungsseite.

---

=== Registrierungsseite

#figure(image("../images/registration.png"), caption: "Registrierungsseite")

- *Beschreibung*: Diese Seite dient der Erstellung eines neuen Benutzerkontos.
- *Felder*:
    - *First name*: Geben Sie Ihren Vornamen ein.
    - *Last name*: Geben Sie Ihren Nachnamen ein.
    - *E-Mail*: Geben Sie Ihre E-Mail-Adresse ein.
    - *Password*: Erstellen Sie ein Passwort (muss mindestens 10 Zeichen lang sein).
    - *Repeat password*: Geben Sie das Passwort zur Bestätigung erneut ein.
- *Schaltflächen*:
    - *Submit*: Registriert den neuen Benutzer.

---

=== Hauptseite

#figure(image("../images/dashboard_ws.jpeg"), caption: "Dashboard")

- *Beschreibung*: Die Hauptseite zeigt ein Dashboard für angemeldete Benutzer. Wenn eine Software über diese Website installiert wurde, wird deren aktueller Status angezeigt.
- *Funktionen*:
    - *Begrüßung*: Personalisierte Begrüßungsnachricht.
    - *Dashboard*: Zeigt den Status der installierten Software (installiert, Update verfügbar, beschädigt) und ermöglicht das Deinstallieren oder Aktualisieren.
- *Navigationsleiste*:
    - *Dark Mode*: Umschalten zwischen Licht- und Dunkelmodus.
    - *Homepage*: Diese Seite.
    - *Compare Tab*: Weiterleitung zur Software-Vergleichsseite.
    - *Agent Panel*: Ermöglicht das Hinzufügen und den Status von Agents zu sehen.
    - *Profile*: Zeigt das Benutzerprofil und Bearbeitungsoptionen.
    - *Login/Logout*: Ermöglicht das Anmelden oder Abmelden.
    - *Session Timer*: Zeigt einen Countdown der aktuellen Sitzungszeit. Nach 1 Stunde müssen Sie sich erneut anmelden.

---

=== Software-Vergleich

#figure(image("../images/comparison.png"), caption: "Software-Vergleich")

- *Beschreibung*: Diese Seite ermöglicht es Benutzern, verschiedene Softwareoptionen zu vergleichen.
- *Filteroptionen*:
    - *Tags*: Filterung der Software nach Tags.
    - *Price*: Anpassung des Preisbereichsfilters.
    - *Period*: Auswahl des Zeitraums (Tag, Monat, Jahr).
    - *License*: Filterung nach Softwarelizenz.
    - *OS*: Filterung nach Betriebssystem.
- *Softwareliste*: Zeigt verschiedene Softwareoptionen mit kurzen Beschreibungen, Lizenzen, Betriebssystemkompatibilität und Preisinformationen an. Jede Softwarekarte ist anklickbar und führt zu einer detaillierteren Ansicht mit Kaufoptionen der Software.

---

=== Softwaredetails

#figure(image("../images/software_detail.png"), caption: "Softwaredetails")

- *Beschreibung*: Detaillierte Ansicht der ausgewählten Software.
- *Funktionen*:
    - *Software Information*: Umfassende Details zur Software, einschließlich Funktionen, Kompatibilität und Sicherheit.
    - *Purchase Options*: Benutzer können zwischen verschiedenen Abonnementplänen wählen (z. B. 1 Monat oder 1 Jahr).

---

=== Agent Management

#figure(image("../images/add_agent.png"), caption: "Agent Management")

- *Beschreibung*: Verwaltung der mit dem Benutzerkonto verbundenen Agents.
- *Funktionen*:
    - *Agent List*: Zeigt eine Liste von Agents mit Details wie Name, IP-Adresse, Verbindungsstatus und Zeitstempeln.
    - *Schaltflächen*:
        - *Refresh*: Aktualisiert die Agent-Liste.
        - *Delete*: Löscht ausgewählte Agents.
        - *Create*: Fügt einen neuen Agent hinzu.
    - *Agent-ID*: Nach dem Erstellen eines neuen Agents wird die Agent-ID in die Zwischenablage kopiert. Verwenden Sie diese ID, um Ihren lokal installierten Agent mit der Website zu verbinden, sodass Sie Installationen auf Ihrem Computer über die Website verwalten können.

---

== Benutzerfluss

Dieser Abschnitt beschreibt den allgemeinen Benutzerfluss auf der Compolvo-Website und führt die Benutzer von der Anmeldung bis zur Verwaltung/Kauf von Software und Agents.
Die folgenden Schritte zeigen den groben Ablauf, mehr Informationen zu den einzelnen Schritten sind im Anschluss zu finden.

+ Erstellen Sie ein Konto, indem Sie auf "Login" klicken und "No account yet?" auswählen.
+ Nach der Erstellung eines neuen Kontos melden Sie sich an. Sie werden nun von Ihrer personalisierten Startseite begrüßt.
+ Erstellen Sie einen Agent auf der Website, indem Sie auf den Agents-Tab in der Navigationsleiste und dann auf die blaue "Create"-Schaltfläche klicken.
+ Die Agent-ID wird in Ihre Zwischenablage kopiert. Downloaden Sie den Agent und führen Sie das Agenten-Init-Skript auf Ihrem Gerät aus und fügen Sie die Agent-ID ein, wenn Sie dazu aufgefordert werden.
+ Im Agents-Tab sollten Sie nun den Namen und die Verbindungsinformationen Ihres installierten Agents sehen (möglicherweise nach einer Aktualisierung).
+ Stellen Sie sicher, dass der Agent auf dem Agent-Gerät mit dem Befehl "run" ausgeführt wird.
+ Fügen Sie Ihre Zahlungsinformationen im Profil-Tab hinzu (nachdem Sie auf das Bearbeitungssymbol geklickt haben).
+ Vergleichen Sie verschiedene Softwareoptionen, indem Sie auf den "Compare Tab" in der Navigationsleiste klicken.
+ Filtern Sie die verfügbaren Software nach den für Sie wichtigen Kriterien.
+ Zur einfacheren Vergleichbarkeit werden bei Auswahl eines Zeitraums im Filter alle Preise für den gewählten Zeitraum angezeigt. Wenn ein Service-Angebot für diesen spezifischen Zeitraum existiert, wird dessen Preis angezeigt. Andernfalls wird der Preis angepasst, um den gewählten Zeitraum abzudecken. Beispielsweise, wenn nur ein monatliches Angebot verfügbar ist, Sie aber Dienste über ein Jahr hinweg vergleichen möchten, wird der monatliche Preis mit 12 multipliziert, oder das Jahresangebot wird angezeigt. Dies gewährleistet einen klaren und genauen Vergleich der verschiedenen Dienste für Ihren gewünschten Zeitraum.
+ Wählen Sie eine Software aus, um mehr Details und Kaufoptionen zu sehen.
+ Abonnieren Sie eine Software, indem Sie ein Service-Angebot abonnieren.
+ Nach positiver Bestätigung gehen Sie zum Profil-Tab, um die Software zu installieren.
+ Auf dem "Home"-Tab beobachten Sie die Installation der Software auf dem Agent.

=== Benutzerkonto registrieren

Gehen Sie zur [https://compolvo.mithem.uk/compolvo](Website). Sie werden von der Startseite begrüßt:
#figure(image("../images/homepage.png"), caption: "Startseite")

Optional können Sie Ihr bevorzugtes Farbschema auswählen, indem Sie auf das Themenmodus-Symbol oben rechts neben der Anmeldeschaltfläche klicken.

Klicken Sie auf "Login", um die Anmeldeseite zu sehen:
#figure(image("../images/login_page.png"), caption: "Anmeldeseite")

Da Sie wahrscheinlich noch kein Konto haben, klicken Sie auf den Link "No account yet?", um zur Registrierungsseite weitergeleitet zu werden:
#figure(image("../images/registration_submit_highlighted.png"), caption: "Registrierungsseite")

Nachdem Sie Ihre Informationen eingegeben haben, klicken Sie auf die Schaltfläche "Submit", um Ihr Konto zu erstellen. Sie werden automatisch angemeldet und zur Startseite weitergeleitet.
#figure(image("../images/home_page_empty.png"), caption: "Startseite")

=== Einen Agent hinzufügen

Dort wird unmittelbar eine Hilfestellung angezeigt, welche weiteren Aktionen für den Benutzer
empfohlen werden, um die Software optimal zu nutzen.
Beim Klick auf "agent panel" wird die Agent-Verwaltung geöffnet. Hier können neue Agents hinzugefügt
und bestehende Agents verwaltet werden:
#figure(image("../images/agent_management_create_highlighted.png"), caption: "Agent Panel")

Wenn der create-Button gedrückt wird, wird ein Dialogfenster angezeigt, welches die ID des neu
erstellten Agents anzeigt:
#figure(image("../images/agent_added.png"), caption: "Agent added")
Diese wird automatisch zur Zwischenablage des Benutzer-Rechners kopiert. Sie wird nun zur
Initialisierung des Agents benötigt.

=== Initialisieren des Agents

Da auf dem Rechner, der verwaltet werden soll, noch kein Agent installiert ist, muss dieser zunächst
heruntergeladen werden.
Dazu kann der "download"-Knopf gedrückt werden. Dieser zeigt dann ein Fenster an, in dem der Agent
für die jeweilige Umgebung heruntergeladen werden kann:
#figure(image("../images/agent_installation.png"), caption: "Agent-Installation")
Anschließend wird eine ausführbare Datei für das jeweilige System heruntergeladen.

Der Benutzer führt die entsprechende Datei aus und gibt als Argument den Befehl `init --compolvo-host compolvo.mithem.uk` an:
In einer Unix-Umgebung also bspw.:

```shell
./compolvo-agent-manjaro-x64 init --compolvo-host compolvo.mithem.uk
```

Das Programm fragt nun nach der Agent-ID, die zuvor in die Zwischenablage kopiert wurde. Außerdem kann ein Name für den Agenten vergeben werden, um die gemanagten Rechner besser unterscheiden zu können.
Damit gilt der Agent als initialisiert und betriebsbereit.
#figure(image("../images/agent_init.png"), caption: "Agent initialization")

Nun muss der Agent nur noch gestartet werden, damit er auf Befehle zur Installation von Software hören kann.
Dafür muss dieselbe Datei mit dem Argument `run` ausgeführt werden. Damit Software installiert werden kann, muss der Prozess über ausreichende Berechtigungen verfügen. Unter Unix-System kann es also z.B. so ausgeführt werden:

```shell
sudo ./compolvo-agent-manjaro-x64 run
```
#figure(image("../images/agent_run.png"), caption: "Agent running")
Damit ist der Agent empfangsbereit.

=== Auswahl von Software

Nun empfiehlt sich ein Blick auf die Software-Übersicht. Dazu kann der Reiter "compare" in der
Navigationsleiste ausgewählt werden:
#figure(image("../images/comparison.png"), caption: "Software Comparison")
Hier kann zwischen verschiedenen Software-Optionen gefiltert werden. Die Software kann nach Tags,
Preis, Lizenz, und unterstützten Betriebssystem und weiteren Kriterien gefiltert werden.
Insbesondere kann das Zahlintervall angepasst werden, um die Software-Preise für den gewünschten
Zeitraum zu vergleichen. Falls ein Service nur für einen anderen Zeitraum als ausgewählt angeboten wird, wird der Preis dafür
automatisch umgerechnet.
Sollte für eine Software Kaufinteresse bestehen, können durch einen Klick auf die Karte weitere Informationen angezeigt werden:

#figure(image("../images/software_detail.png"), caption: "Software Details")

=== Kauf von Software

Die Kaufoptionen (Abonnement-Pläne) können im unteren Teil angesehen werden.
Beim Klick auf "buy now" bei einem Angebot wird darauf hingewiesen, dass der Benutzer noch nicht über hinterlegte Zahlungsinformationen verfügt und gebeten, diese auszufüllen:
#figure(image("../images/payment_details.png"), caption: "Payment details")

Nach dem Abschicken der Informationen wird die Software abonniert, und der Benutzer aufgefordert, die profile-Seite zu besuchen.
Beim Klick auf "profile" in der Navigationsleiste kann der Benutzer die bestellte Software sehen:

#figure(image("../images/profile.png"), caption: "Profile")

Nach einem Klick auf "install" können bestehende und kompatible Agents ausgewählt werden, auf denen die Software installiert werden soll:
#figure(image("../images/software_install_agent_select.png"), caption: "Agent selection")

Nach der Bestätigung wird darauf hingewiesen, die home page zu besuchen.
Dort wird der Installationsprozess der Software auf dem Agenten angezeigt:

#figure(image("../images/home_page_installing.png"), caption: "Software installation")

Die Software wird nun installiert (sobald der Agent verbunden ist).
Sie kann über dieselben Kacheln, die für die Statusinformation genutzt werden, auch wieder deinstalliert werden.
Abonnements können über die profile-Seite gekündigt werden (was automatisch die Software von allen verbundenen Agents entfernt).