"""Info-Seite: Über uns, Impressum, Datenschutz (Inhalte aus info.json, leere Felder werden weggelassen)."""
import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from config import AUTHOR, GROUP, LOGO, TEAM, VFC_LOGO
from textutil import esc

CSS = Path(__file__).with_name("style.css").read_text(encoding="utf-8")


def load_info():
    try:
        return json.loads(Path("info.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def heimort(data):
    c = Counter(f["place"] for f in data["schedule"] if f.get("place") and f["home"].lower() == TEAM.lower())
    return c.most_common(1)[0][0] if c else ""


def build_info(data):
    i = load_info()
    g = lambda k: (i.get(k) or "").strip()
    ort = g("spiellokal") or heimort(data)
    adr = g("spiellokal_adresse") or ort
    blocks = []
    if g("ueber_uns"):
        blocks.append("".join(f"<p>{esc(x)}</p>" for x in g("ueber_uns").split("\n") if x.strip()))
    rows = []
    if ort:
        link = f" · <a href='https://www.google.com/maps/search/?api=1&query={quote(adr + ' Dart')}' target='_blank' rel='noopener'>Karte</a>"
        rows.append(("Spiellokal / Heimort", f"{esc(ort)}{link}"))
    if g("training"):
        rows.append(("Training", esc(g("training"))))
    kon = " · ".join(x for x in (esc(g("kontakt_name")),
                                 f"<a href='mailto:{esc(g('kontakt_email'))}'>{esc(g('kontakt_email'))}</a>" if g("kontakt_email") else "",
                                 esc(g("kontakt_telefon"))) if x)
    if kon:
        rows.append(("Kontakt", kon))
    rows.append(("Liga", f"{esc(GROUP)} · VFC Dartverband · <a href='https://vfc.ch' target='_blank' rel='noopener'>vfc.ch</a>"))
    ueber = ("<section id='ueber'><h2>Über uns</h2>" + "".join(blocks)
             + "<dl class='info'>" + "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in rows) + "</dl></section>")
    logo = f"<img class='logo' src='logo{LOGO.suffix.lower()}' alt='' width='56' height='56'>" if LOGO else ""
    return f"""<!doctype html><html lang="de-CH"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#17100f"><title>Info – {esc(TEAM)}</title><link rel="manifest" href="manifest.webmanifest">
<style>{CSS}</style></head><body><header class="top"><div class="brand wrap">{logo}<div><h1>{esc(TEAM)}</h1><p class="sub">Info</p></div></div></header>
<main><p><a href="./">← Zur Statistik</a></p>{ueber}
<footer>Made by {esc(AUTHOR)} · <a href="./">Zur Statistik</a></footer></main></body></html>"""
