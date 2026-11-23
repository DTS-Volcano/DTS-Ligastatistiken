"""Akzentfarbe eines Vereins aus seinem Logo (häufigste kräftige Farbe)."""
import colorsys
from functools import lru_cache

from config import team_logo_source


VON_HAND = {   # festgelegte Farben je Verein: (für hellen Hintergrund, für dunklen Hintergrund)
    "double trouble steeldarters": ("#8b1a1a", "#e0605a"),   # dunkelrot
    "irish skulls steel": ("#1f7a3a", "#5fcf7e"),            # grün
    "irish skulls ;) steel": ("#1f7a3a", "#5fcf7e"),
    "dynamo tresen": ("#9a7000", "#f2c230"),                 # gelb (hell etwas dunkler, damit Text lesbar bleibt)
    "2010er steel": ("#5d646b", "#dfe3e8"),                  # grau-weisslich (schwarz-weisses Logo)
    "dart ost": ("#0e7c7b", "#4fd1c5"),                      # petrol
    "die humorlosen": ("#1d4f91", "#6aa6ee"),                # blau
    "dartfabrik steel": ("#b3541a", "#f29a4a"),              # orange
    "braschtli's darter 2": ("#5b3590", "#b794e8"),          # violett
}


@lru_cache(maxsize=None)
def team_color(name):
    """(Farbe für hellen Hintergrund, Farbe für dunklen Hintergrund) als '#rrggbb', oder None ohne kräftige Logofarbe."""
    if name.lower() in VON_HAND:
        return VON_HAND[name.lower()]
    src = team_logo_source(name)
    if not src or src.suffix.lower() == ".svg":
        return None
    try:
        from PIL import Image
        im = Image.open(src).convert("RGBA")
        im.thumbnail((96, 96))
    except Exception:
        return None
    bins = {}
    for r, g, b, a in im.getdata():
        if a < 200:
            continue
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s < 0.35 or l < 0.12 or l > 0.9:      # grau, fast schwarz oder fast weiss zählt nicht
            continue
        k = int(h * 24) % 24
        bins[k] = bins.get(k, 0) + s * (1 - abs(l - .45))
    if not bins:
        return None
    k = max(bins, key=bins.get)
    h = (k + .5) / 24
    hexc = lambda l, s: "#%02x%02x%02x" % tuple(round(x * 255) for x in colorsys.hls_to_rgb(h, l, s))
    return hexc(0.30, 0.62), hexc(0.62, 0.62)
