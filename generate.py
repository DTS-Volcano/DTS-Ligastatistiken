#!/usr/bin/env python3
"""Einstiegspunkt: liest vfc.ch und schreibt docs/index.html (plus Logo, history.json, data.json).

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

from config import LOGO, VFC_LOGO, OUT, PHOTO_DIR, TEAM, find_photo, photo_source
import page
from page import render
from scraper import BlockedError
from stats import build_stats, update_history


SW = """// Netz zuerst; bei fehlendem Netz die zuletzt geladene Version (die App funktioniert auch offline)
const C = 'dts-v2';
const PRE = __PRE__;
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(C).then(c => Promise.all(PRE.map(u => c.add(u).catch(() => {})))));
});
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const c = r.clone(); caches.open(C).then(x => x.put(e.request, c)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || (e.request.mode === 'navigate' ? caches.match('./') : undefined))));
});
"""


def write_pwa():
    """Macht die Seite auf dem Handy als App installierbar (Startbildschirm, Vollbild, Offline)."""
    manifest = {"name": f"{TEAM} – Statistik", "short_name": "DTS Statistik", "start_url": "./", "scope": "./",
                "display": "standalone", "background_color": "#17100f", "theme_color": "#17100f",
                "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                          {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}
    OUT.mkdir(exist_ok=True)
    (OUT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    pre = ["./", "dialogs.html", "manifest.webmanifest", "icon-192.png", "history.json"]
    for stem in ("logo", "vfc-logo"):
        pre += [f.name for f in OUT.glob(stem + ".*")]
    if (OUT / "spieler").is_dir():
        pre += ["spieler/" + f.name for f in sorted((OUT / "spieler").iterdir()) if f.is_file()]
    (OUT / "sw.js").write_text(SW.replace("__PRE__", json.dumps(pre)), encoding="utf-8")


def copy_photos(players):
    """Kopiert die Spielerbilder nach docs/spieler/ unter dem Standardnamen (klein, mit Bindestrich),
    verkleinert auf höchstens 800 Pixel, damit die Seite am Handy schnell lädt."""
    if not PHOTO_DIR.is_dir():
        return
    (OUT / "spieler").mkdir(exist_ok=True)
    for p in players:
        src, name = photo_source(p["name"]), find_photo(p["name"])
        if not (src and name):
            continue
        dst = OUT / "spieler" / name
        try:
            from PIL import Image
            if src.suffix.lower() == ".svg":
                raise ImportError
            im = Image.open(src)
            im.thumbnail((800, 800))
            im.save(dst, optimize=True)
        except Exception:
            shutil.copyfile(src, dst)


def main():
    print(f"Logo: {LOGO.name!r}" if LOGO else "Logo: keine Bilddatei im Hauptordner gefunden")
    try:
        data = build_stats()
    except BlockedError as e:
        print(f"HINWEIS: {e}")
        if (OUT / "index.html").exists():
            print("Die Seite bleibt auf dem letzten Stand, der nächste Lauf versucht es erneut.")
            return
        raise SystemExit("Keine Daten erhalten und noch keine Seite vorhanden.")
    if not data["players"]:
        raise SystemExit(f"Keine gespielten Partien für '{TEAM}' gefunden – Teamname/Gruppe prüfen.")
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("logo.*"):
        old.unlink()
    if LOGO:
        shutil.copyfile(LOGO, OUT / ("logo" + LOGO.suffix.lower()))
    if VFC_LOGO:
        shutil.copyfile(VFC_LOGO, OUT / ("vfc-logo" + VFC_LOGO.suffix.lower()))
    copy_photos(data["players"])
    write_pwa()
    hist = update_history(data["ranks"])
    (OUT / "history.json").write_text(json.dumps(hist, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (OUT / "index.html").write_text(render(data, hist), encoding="utf-8")
    (OUT / "dialogs.html").write_text(page.DIALOGS, encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps({"matches": data["matches"], "players": data["players"],
                                               "league": data["league"], "schedule": data["schedule"]},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(data['matches'])} Partien, {len(data['players'])} Spieler")


if __name__ == "__main__":
    main()
