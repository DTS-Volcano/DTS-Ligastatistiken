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
