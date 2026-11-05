"""Einstellungen und Pfade. Teamname und Gruppe kommen aus den Umgebungsvariablen (siehe update.yml)."""
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---- Einstellungen (Team und Gruppe können über Umgebungsvariablen in update.yml gesetzt werden) ----
BASE = "https://vfc.ch/"
GROUP = os.getenv("GROUP", "STSO S 2")
TEAM = os.getenv("TEAM", "Double Trouble Steeldarters")
TOP, MID = 10, 30          # Rang-Klassen: 1-10, 11-30, 31+
FORM_N = 5                 # Anzahl Einzel für die Formkurve
OUT = Path(os.getenv("OUT", "docs"))
AUTHOR = "Kevin Notter"    # erscheint im Footer


def find_logo():
    """Nimmt das Vereinslogo: LOGO-Variable, sonst die erste .svg-Datei im Hauptordner."""
    if os.getenv("LOGO"):
        p = Path(os.environ["LOGO"])
        return p if p.exists() else None
    # unsichtbare Sonderzeichen im Dateinamen (z. B. U+200E) werden ignoriert
    found = sorted(p for p in Path(".").iterdir() if p.is_file()
                   and "".join(c for c in p.name if unicodedata.category(c) != "Cf").lower().endswith(".svg"))
    return found[0] if found else None


LOGO = find_logo()


def today():
    """Heutiges Datum (Zürich). TODAY_OVERRIDE=YYYY-MM-DD dient nur Tests."""
    if os.getenv("TODAY_OVERRIDE"):
        return datetime.strptime(os.environ["TODAY_OVERRIDE"], "%Y-%m-%d").date()
    return datetime.now(ZoneInfo("Europe/Zurich")).date()


PHOTO_DIR = Path("spieler")   # hier liegen die Spielerbilder, z. B. kevin-notter.png


def slug(name):
    """kevin-notter aus 'Kevin Notter' (Umlaute: ä -> ae usw.)."""
    s = name.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "-".join("".join(ch if ch.isalnum() else " " for ch in s).split())


def find_photo(name):
    """Dateiname des Spielerbilds (png/jpg/jpeg/webp/svg, Gross-/Kleinschreibung egal) oder None.
    Kommt mit Leerzeichen oder Unterstrich statt Bindestrich zurecht."""
    if not PHOTO_DIR.is_dir():
        return None
    want = slug(name)
    for f in sorted(PHOTO_DIR.iterdir()):
        if f.suffix.lower().lstrip(".") in ("png", "jpg", "jpeg", "webp", "svg") and slug(f.stem.replace("_", " ")) == want:
            return f"{want}{f.suffix.lower()}"
    return None


def photo_source(name):
    """Pfad der Originaldatei im Ordner spieler/ (passend zu find_photo)."""
    want = slug(name)
    for f in sorted(PHOTO_DIR.iterdir()):
        if f.suffix.lower().lstrip(".") in ("png", "jpg", "jpeg", "webp", "svg") and slug(f.stem.replace("_", " ")) == want:
            return f
    return None
