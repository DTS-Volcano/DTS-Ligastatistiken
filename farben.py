"""Akzentfarbe eines Vereins aus seinem Logo (häufigste kräftige Farbe)."""
import colorsys
from functools import lru_cache

from config import team_logo_source


VON_HAND = {"dynamo tresen": ("#1d6b4a", "#4fb98f")}   # wo die automatische Wahl danebenliegt


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
