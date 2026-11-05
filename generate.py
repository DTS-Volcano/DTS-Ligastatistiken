#!/usr/bin/env python3
"""Einstiegspunkt: liest vfc.ch und schreibt docs/index.html (plus logo.svg, history.json, data.json).

Aufbau:
  config.py      Einstellungen (Team, Gruppe, Rang-Klassen, Logo)
  textutil.py    kleine Hilfsfunktionen
  scraper.py     Daten von vfc.ch laden und einlesen
  stats.py       Auswertung und Rangverlauf
  components.py  HTML-Bausteine (Fenster, Kurven, Form-Punkte)
  sections.py    die einzelnen Bereiche der Seite
  page.py        Seite zusammensetzen
  style.css      Aussehen
  app.js         Verhalten (Reiter, Fenster, Sortieren, Kopieren)
"""
import json
import shutil

from config import LOGO, OUT, TEAM
from page import render
from stats import build_stats, update_history


def main():
    print(f"Logo: {LOGO.name!r}" if LOGO else "Logo: keine .svg-Datei im Hauptordner gefunden")
    data = build_stats()
    if not data["players"]:
        raise SystemExit(f"Keine gespielten Partien für '{TEAM}' gefunden – Teamname/Gruppe prüfen.")
    OUT.mkdir(exist_ok=True)
    if LOGO:
        shutil.copyfile(LOGO, OUT / "logo.svg")
    hist = update_history(data["ranks"])
    (OUT / "history.json").write_text(json.dumps(hist, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (OUT / "index.html").write_text(render(data, hist), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps({"matches": data["matches"], "players": data["players"],
                                               "league": data["league"], "schedule": data["schedule"]},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(data['matches'])} Partien, {len(data['players'])} Spieler")


if __name__ == "__main__":
    main()
