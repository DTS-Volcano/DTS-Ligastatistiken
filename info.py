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
    name, adresse, mail = g("verantwortlich_name") or AUTHOR, g("verantwortlich_adresse"), g("verantwortlich_email")
    imp = (f"<section id='impressum'><h2>Impressum</h2><p>Verantwortlich für diese Seite: <b>{esc(name)}</b>"
           + (f"<br>{esc(adresse).replace(chr(10), '<br>')}" if adresse else "")
           + (f"<br><a href='mailto:{esc(mail)}'>{esc(mail)}</a>" if mail else "")
           + f"</p><p class='hint'>Private, nicht kommerzielle Seite des Dart-Teams {esc(TEAM)}. Kein offizielles Angebot des VFC Dartverbands.</p></section>")
    kontakt_dsg = f" Anfragen dazu bitte an <a href='mailto:{esc(mail)}'>{esc(mail)}</a>." if mail else ""
    dsg = ("<section id='datenschutz'><h2>Datenschutz</h2>"
           "<p><b>Daten dieser Seite.</b> Die Seite zeigt Ergebnisse, Spielerberichte und Ranglisten der Liga. Sie stammen aus den öffentlich "
           "einsehbaren Berichten auf vfc.ch und werden einmal täglich automatisch übernommen. Es werden Namen von Spielerinnen und Spielern "
           "sowie ihre Spielergebnisse gezeigt. Bilder und Figuren in den Profilen werden nur mit Einverständnis der Personen verwendet."
           f"{kontakt_dsg}</p>"
           "<p><b>Besucher.</b> Die Seite setzt keine Cookies und bindet keine Werbung oder Tracker ein. Im Browser werden nur Einstellungen "
           "gespeichert (z. B. gewählter Verein, Filter) sowie, wenn die Seite als App installiert ist, eine Kopie der Seite für den Offline-Betrieb. "
           "Diese Daten bleiben auf deinem Gerät.</p>"
           "<p><b>Hosting.</b> Die Seite wird über GitHub Pages ausgeliefert. Dabei kann GitHub technisch bedingt Zugriffsdaten wie die "
           "IP-Adresse verarbeiten (siehe Datenschutzerklärung von GitHub).</p>"
           "<p><b>Löschung.</b> Wer nicht auf der Seite erscheinen möchte oder ein Bild entfernt haben will, meldet sich bei der verantwortlichen Person.</p></section>")
    logo = f"<img class='logo' src='logo{LOGO.suffix.lower()}' alt='' width='56' height='56'>" if LOGO else ""
    return f"""<!doctype html><html lang="de-CH"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#17100f"><title>Info – {esc(TEAM)}</title><link rel="manifest" href="manifest.webmanifest">
<style>{CSS}</style></head><body><header class="top"><div class="brand wrap">{logo}<div><h1>{esc(TEAM)}</h1><p class="sub">Info</p></div></div></header>
<main><p><a href="./">← Zur Statistik</a></p>{ueber}{imp}{dsg}
<footer>Made by {esc(AUTHOR)} · <a href="./">Zur Statistik</a></footer></main></body></html>"""
