"""Flyer-Generator: eine Seite, die für jedes kommende Spiel ein Flyer-Bild (4:5) im Browser zeichnet."""
import json
import re
import shutil
from pathlib import Path

from config import GROUP, LOGO, OUT, TEAM, team_logo_name, team_logo_source
from farben import team_color
from sections import team_forms
from textutil import dkey, esc

ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI"}
HERE = Path(__file__).parent


def season_label(data):
    m = re.search(r"S\s*(\d+)\s*$", GROUP)
    years = [f["date"][-2:] for f in data["schedule"] if re.search(r"\d\d$", f["date"])]
    yr = max(years) if years else ""
    return f"SAISON {ROMAN.get(m.group(1), m.group(1))}/{yr}" if m and yr else GROUP.upper()


def logo_mode(name):
    """'round': Logo füllt einen Kreis (wird so gezeichnet), sonst 'disc' (auf weisser Scheibe, wie in den Tabellen)."""
    src = team_logo_source(name)
    try:
        from PIL import Image
        im = Image.open(src).convert("RGBA")
        im.thumbnail((100, 100))
        w, h = im.size
        if min(im.getpixel(p)[3] for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))) > 200:
            return "disc"
        n = ok = 0
        for y in range(h):
            for x in range(w):
                if (x - w / 2) ** 2 + (y - h / 2) ** 2 <= (min(w, h) * .45) ** 2:
                    n += 1
                    ok += im.getpixel((x, y))[3] > 200
        return "round" if ok / n >= .93 else "disc"
    except Exception:
        return "disc"


def flyer_data(data):
    forms = team_forms(data)
    info = data.get("teaminfo") or {}
    teams = {}
    for t in data["league"]:
        k = t["team"].lower()
        col = team_color(t["team"])
        logo = team_logo_name(t["team"])
        ti = info.get(k) or {}
        teams[k] = {"rank": t["rank"], "pp": t["pp"], "pm": t["pm"], "color": (col[1] if col else "#dd4a47"),
                    "logo": f"vereine/{logo}" if logo else None, "mode": logo_mode(t["team"]) if logo else "", "lokal": ti.get("lokal", ""), "strasse": ti.get("strasse", ""),
                    "ort": ti.get("ort", ""), "form": [w for w, _ in forms.get(k, [])]}
    fx = [{"date": f["date"], "home": f["home"], "guest": f["guest"], "place": f.get("place") or ""}
          for f in sorted((f for f in data["schedule"] if not f["played"]), key=lambda f: (dkey(f["date"]), f["nr"]))]
    return {"teams": teams, "fixtures": fx, "own": TEAM, "season": season_label(data), "sport": "STEELDARTS", "vfc": "vfc-logo.png"}


def build_flyer(data):
    shutil.copyfile(HERE / "fonts" / "BebasNeue-Regular.ttf", OUT / "BebasNeue-Regular.ttf")
    css = (HERE / "style.css").read_text(encoding="utf-8")
    js = (HERE / "flyer.js").read_text(encoding="utf-8")
    fd = json.dumps(flyer_data(data), ensure_ascii=False).replace("</", "<\\/")
    logo = f"<img class='logo' src='logo{LOGO.suffix.lower()}' alt='' width='56' height='56'>" if LOGO else ""
    if not flyer_data(data)["fixtures"]:
        body = "<p class='hint'>Es stehen keine kommenden Spiele im Spielplan.</p>"
    else:
        body = """<p class="hint">Wähle ein Spiel, dann entsteht der Flyer automatisch mit Logos, Datum, Spielort, Tabellenplatz und Form. Als Bild speichern oder direkt teilen.</p>
<div class="fl-f"><label>Spiel<select id="sel"></select></label>
<label>Startzeit<input id="time" value="20:00" maxlength="5" inputmode="numeric"></label>
<label>Support-Text<input id="sup" value="Wir freuen uns auf eure Unterstützung!" maxlength="60"></label>
<label class="fl-c"><input type="checkbox" id="tab" checked> Tabellenplatz und Form anzeigen</label></div>
<canvas id="cv" class="fl-cv"></canvas>
<p class="fl-b"><button class="rb" id="sh" hidden>Teilen</button> <button class="rb" id="dl">Als Bild speichern</button></p>"""
    return f"""<!doctype html><html lang="de-CH"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#17100f"><title>Flyer – {esc(TEAM)}</title><link rel="manifest" href="manifest.webmanifest">
<style>@font-face{{font-family:Bebas;src:url(BebasNeue-Regular.ttf) format("truetype");font-display:block}}{css}
.fl-f{{display:grid;gap:10px;margin:14px 0}}.fl-f label{{display:grid;gap:4px;font-size:.85rem;color:var(--mute)}}
.fl-f input,.fl-f select{{font:inherit;font-size:1rem;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);min-width:0}}
.fl-f .fl-c{{display:flex;align-items:center;gap:8px;color:var(--ink)}}.fl-f .fl-c input{{width:auto}}
.fl-cv{{width:100%;max-width:540px;height:auto;display:block;border-radius:10px;border:1px solid var(--line)}}.fl-b{{margin:12px 0}}.fl-b .rb{{font-size:.95rem;padding:8px 16px}}</style></head>
<body><header class="top"><div class="brand wrap">{logo}<div><h1>{esc(TEAM)}</h1><p class="sub">Flyer-Generator</p></div></div></header>
<main><p><a href="./">← Zur Statistik</a></p><section><h2>Flyer</h2>{body}</section></main>
<script type="application/json" id="fd">{fd}</script><script>{js}</script></body></html>"""
