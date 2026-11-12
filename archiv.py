#!/usr/bin/env python3
"""Friert die aktuelle Saison ein: kopiert die Seite nach docs/archiv/<name>/ und setzt den Rangverlauf zurück.

Aufruf:  python archiv.py "Saison 2026"
Danach gilt: GROUP (und bei Bedarf TEAM) in .github/workflows/update.yml auf die neue Gruppe ändern.
"""
import html
import json
import shutil
import sys
from datetime import date

from config import GROUP, OUT, TEAM, slug

SW_OFF = "navigator.serviceWorker.register('sw.js')"


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        raise SystemExit('Name fehlt, z. B.: python archiv.py "Saison 2026"')
    name = sys.argv[1].strip()
    src = OUT / "index.html"
    if not src.exists():
        raise SystemExit("docs/index.html fehlt – erst einen normalen Lauf machen.")
    key = slug(name) or "saison"
    dst = OUT / "archiv" / key
    dst.mkdir(parents=True, exist_ok=True)

    page = src.read_text(encoding="utf-8")
    # Pfade anpassen, weil die Seite zwei Ordner tiefer liegt
    for a, b in (('src="logo.png"', 'src="../../logo.png"'), ('href="logo.png"', 'href="../../logo.png"'),
              ('src="logo.svg"', 'src="../../logo.svg"'), ('href="logo.svg"', 'href="../../logo.svg"'),
                 ('src="spieler/', 'src="../../spieler/'), ('href="icon-180.png"', 'href="../../icon-180.png"')):
        page = page.replace(a, b)
    page = page.replace('<link rel="manifest" href="manifest.webmanifest">', "")
    page = page.replace('href="info.html', 'href="../../info.html')
    page = page.replace(SW_OFF, "Promise.resolve()")
    bar = (f'<div class="archivbar" style="background:#17100f;color:#f4eeee;padding:8px 16px;font:.9rem system-ui,sans-serif;text-align:center"><a href="../../" style="color:#f4a3a1">← zur aktuellen Saison</a> · Archiv: <b>{html.escape(name)}</b> '
           f'(eingefroren am {date.today().strftime("%d.%m.%Y")})</div>')
    page = page.replace("<body>", "<body>" + bar, 1)
    (dst / "index.html").write_text(page, encoding="utf-8")
    for f in ("data.json", "history.json", "dialogs.html"):
        if (OUT / f).exists():
            shutil.copyfile(OUT / f, dst / f)

    data = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
    wins = sum(1 for m in data["matches"] if int(m["points"].split(":")[0]) > int(m["points"].split(":")[1]))
    meta = {"name": name, "key": key, "team": TEAM, "group": GROUP, "date": date.today().isoformat(),
            "matches": len(data["matches"]), "wins": wins}
    (dst / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    # Neue Saison beginnt mit leerem Rangverlauf
    (OUT / "history.json").unlink(missing_ok=True)

    # Übersichtsseite aller Archive
    items = []
    for f in sorted((OUT / "archiv").glob("*/meta.json"), reverse=True):
        m = json.loads(f.read_text(encoding="utf-8"))
        items.append(f'<li><a href="{html.escape(m["key"])}/">{html.escape(m["name"])}</a>'
                     f'<span>{html.escape(m["group"])} · {m["wins"]} Siege aus {m["matches"]} Partien</span></li>')
    index = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Archiv – {html.escape(TEAM)}</title><style>
body{{font-family:system-ui,sans-serif;background:#f5f4f3;color:#1b1416;margin:0}}main{{max-width:640px;margin:0 auto;padding:32px 16px}}
h1{{font-family:Georgia,serif}}ul{{list-style:none;padding:0}}li{{display:flex;flex-direction:column;gap:2px;padding:12px 0;border-bottom:1px solid #ddd8d9}}
a{{color:#9a1b1c;font-weight:600;font-size:1.1rem}}span{{color:#675d60;font-size:.9rem}}
@media(prefers-color-scheme:dark){{body{{background:#141011;color:#eee8e8}}li{{border-color:#2f2628}}a{{color:#dd4a47}}span{{color:#aa9fa2}}}}
</style></head><body><main><h1>Archiv früherer Saisons</h1><ul>{"".join(items)}</ul><p><a href="../">← zur aktuellen Saison</a></p></main></body></html>"""
    (OUT / "archiv" / "index.html").write_text(index, encoding="utf-8")
    print(f"Archiviert nach {dst} ({wins} Siege aus {len(data['matches'])} Partien). Rangverlauf zurückgesetzt.")


if __name__ == "__main__":
    main()
