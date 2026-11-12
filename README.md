# Dart-Team-Statistik

Liest täglich die Spielrapporte von vfc.ch und erzeugt eine Statistik-Seite (`docs/index.html`).

## Einrichten
1. Neues GitHub-Repository anlegen (z. B. `dart-stats`) und alle Dateien dieses Ordners hochladen
   (inklusive `.github/workflows/update.yml` und `docs/`).
2. **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, Ordner = `/docs`.
3. **Actions** → *Statistiken aktualisieren* → *Run workflow* (erster Lauf von Hand).
4. Nach 1–2 Minuten ist die Seite unter `https://<dein-name>.github.io/<repo>/` erreichbar.

Danach läuft die Aktualisierung jeden Tag um 04:15 UTC automatisch.

## Anpassen
In `.github/workflows/update.yml` unter `env:` stehen `GROUP` (Liga-Gruppe) und `TEAM` (exakter Teamname wie auf vfc.ch).
Rang-Klassen (Top 10 / 11–30 / 31+) stehen oben in `generate.py` (`TOP`, `MID`).

## Spielerbilder
Bilder in den Ordner `spieler/` legen (Dateiname = `vorname-nachname.png`, siehe `spieler/LIESMICH.txt`).
Sie erscheinen im Spielerprofil. Ohne Bild werden die Initialen angezeigt.

## Saison abschliessen (Archiv)
1. Auf GitHub unter **Actions → Saison archivieren → Run workflow** den Namen eingeben, z. B. `Saison 2026`.
2. Die Seite wird unter `docs/archiv/saison-2026/` eingefroren und ist über den Link «Archiv früherer Saisons» im Fuss der Startseite erreichbar. Der Rangverlauf beginnt wieder bei null.
3. Wenn die neue Gruppe auf vfc.ch steht: in `.github/workflows/update.yml` (und `archiv.yml`) bei `GROUP` die neue Gruppe eintragen. Die gespeicherten Reports liegen pro Gruppe in `daten/reports/<gruppe>/`, die alte Saison wird dadurch nicht vermischt.

## VFC-Logo im Seitenkopf (optional)

Eine Bilddatei, deren Name mit `vfc` beginnt (z. B. `vfc-logo.png`, auch .svg/.jpg/.webp), in den Hauptordner legen. Sie erscheint oben rechts im Seitenkopf und verlinkt auf vfc.ch.

## Info-Seite (Über uns)

Die Seite `info.html` wird aus `info.json` erzeugt. Dort Text, Spiellokal, Training und Kontakt eintragen. Leere Felder werden weggelassen. Der Heimort wird sonst aus dem Spielplan übernommen.

## Besucherzähler (optional)

Zählt nur, wie oft die Seite pro Tag geöffnet wird (eine Zahl pro Tag, keine Daten über Besucher).
1. Neue Google-Tabelle anlegen, dort **Erweiterungen → Apps Script** öffnen und den Inhalt von `zaehler/apps-script.gs` einfügen.
2. **Bereitstellen → Neue Bereitstellung → Typ: Web-App**. Ausführen als: *Ich*, Zugriff: *Jeder*. Die angezeigte Web-App-URL kopieren.
3. Die URL in `info.json` bei `zaehler_url` eintragen. Fertig, die Zahlen erscheinen im Tabellenblatt «Besuche».
4. Eigene Besuche nicht mitzählen: einmal die Seite mit `?ich` am Ende der Adresse öffnen (pro Gerät und Browser).
