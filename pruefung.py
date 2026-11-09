#!/usr/bin/env python3
"""Prüft nach dem Lauf, ob die erzeugte Seite plausibel ist. Bei einem Fehler endet das Skript mit Exit-Code 1,
der Workflow speichert dann nichts und die zuletzt gute Seite bleibt online.

Aufruf:  python pruefung.py
"""
import json
import re
import subprocess
import sys

from config import OUT, TEAM


def vorher(pfad):
    """Letzter gespeicherter Stand aus Git (None, falls nicht vorhanden)."""
    try:
        out = subprocess.run(["git", "show", f"HEAD:{OUT.as_posix()}/{pfad}"], capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except Exception:
        return None


def pruefe():
    fehler, hinweise = [], []
    idx, dj = OUT / "index.html", OUT / "data.json"
    if not idx.exists() or not dj.exists():
        return [f"{idx} oder {dj} fehlt"], []
    html = idx.read_text(encoding="utf-8")
    try:
        d = json.loads(dj.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"data.json nicht lesbar: {e}"], []
    alt = vorher("data.json")

    if len(html) < 60_000:
        fehler.append(f"index.html ist mit {len(html) // 1000} KB ungewöhnlich klein")
    for marker in ('id="p-uebersicht"', 'id="p-spieler"', 'id="p-liga"', 'id="p-analyse"', 'id="p-partien"', "data-t='own'"):
        if marker not in html:
            fehler.append(f"In der Seite fehlt: {marker}")
    if re.search(r">\s*(None|nan|undefined)\s*<", html):
        fehler.append("In der Seite steht ein Platzhalter wie «None» oder «undefined»")

    m, p, lg, sp = d.get("matches", []), d.get("players", []), d.get("league", []), d.get("schedule", [])
    if not m:
        fehler.append("Keine Partien gefunden")
    if not p:
        fehler.append("Keine Spieler gefunden")
    if len(lg) < 3:
        fehler.append(f"Tabelle hat nur {len(lg)} Teams")
    elif not any(t["team"].lower() == TEAM.lower() for t in lg):
        fehler.append(f"«{TEAM}» fehlt in der Tabelle")
    if not sp:
        fehler.append("Spielplan ist leer")
    for x in m:
        try:
            a, b = (int(v) for v in x["points"].split(":"))
            if a + b != 3:
                fehler.append(f"Partie {x['date']} gegen {x['opp']}: Punkte {x['points']} ergeben nicht 3")
        except (ValueError, KeyError):
            fehler.append(f"Partie {x.get('date')} hat keine lesbaren Punkte")
    if p and sum(1 for s in p if s.get("rank")) < len(p) / 2:
        fehler.append("Für mehr als die Hälfte der Spieler fehlt der Rang (Einzelrangliste nicht gelesen?)")
    if len(m) + len(p) and html.count("<dialog") < len(m) + len(p):
        fehler.append("Weniger Fenster als Partien und Spieler – Seite unvollständig")

    if alt:
        am, ap, al = alt.get("matches", []), alt.get("players", []), alt.get("league", [])
        if len(m) < len(am):
            fehler.append(f"Weniger Partien als zuvor ({len(m)} statt {len(am)})")
        if len(p) < len(ap) * 0.8:
            fehler.append(f"Deutlich weniger Spieler als zuvor ({len(p)} statt {len(ap)})")
        if len(lg) < len(al):
            fehler.append(f"Weniger Teams in der Tabelle als zuvor ({len(lg)} statt {len(al)})")
        if len(m) > len(am) + 3:
            hinweise.append(f"{len(m) - len(am)} neue Partien auf einmal – bitte kurz ansehen")
    else:
        hinweise.append("Kein früherer Stand zum Vergleichen gefunden")
    return fehler, hinweise


def main():
    fehler, hinweise = pruefe()
    for h in hinweise:
        print(f"Hinweis: {h}")
    if fehler:
        print("PRÜFUNG FEHLGESCHLAGEN – die Seite wird nicht gespeichert, die letzte gute Version bleibt online:")
        for f in fehler:
            print(f"  - {f}")
        sys.exit(1)
    print("Prüfung bestanden.")


if __name__ == "__main__":
    main()
