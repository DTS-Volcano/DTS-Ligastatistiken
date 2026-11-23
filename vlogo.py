"""Vereinslogos als kleines Bild oder, wenn keins vorhanden ist, als Kreis mit Initialen."""
import hashlib
from html import escape

from config import team_logo_name


def tlogo(name, size=""):
    """<span class='tlg'> mit Bild oder Initialen; size: '' (klein), 'l' (gross)."""
    f = team_logo_name(name)
    cls = f"tlg {size}".strip()
    if f:
        return f"<span class='{cls}'><img src='vereine/{escape(f)}' alt='' loading='lazy'></span>"
    words = [w for w in "".join(ch if ch.isalnum() else " " for ch in name).split() if w]
    ini = "".join(w[0] for w in words[:2]).upper() or "?"
    hue = int(hashlib.md5(name.lower().encode()).hexdigest()[:4], 16) % 360
    return f"<span class='{cls} ph' style='--h:{hue}' aria-hidden='true'>{escape(ini)}</span>"
