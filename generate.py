#!/usr/bin/env python3
"""Liest die VFC-Spielrapporte einer Gruppe und erzeugt docs/index.html mit Team-Statistiken."""
import html
import json
import os
import re
import shutil
import time
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = "https://vfc.ch/"
GROUP = os.getenv("GROUP", "STSO S 2")
TEAM = os.getenv("TEAM", "Double Trouble Steeldarters")
TOP, MID = 10, 30          # Rang-Klassen: 1-10, 11-30, 31+
OUT = Path(os.getenv("OUT", "docs"))


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
print(f"Logo: {LOGO.name!r}" if LOGO else "Logo: keine .svg-Datei im Hauptordner gefunden")
AUTHOR = "Kevin Notter"

session = requests.Session()
session.headers["User-Agent"] = "dart-team-stats (privates Hobbyprojekt)"


# ---------- Laden & Bereinigen ----------
def get(url):
    for attempt in range(3):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            time.sleep(0.4)  # Server schonen
            try:
                txt = r.content.decode("utf-8")
            except UnicodeDecodeError:
                txt = r.content.decode("cp1252", errors="replace")
            return BeautifulSoup(txt, "html.parser")
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)


def fix(s):
    """Repariert doppelt kodierte Umlaute (z. B. 'MÃ¼ller' -> 'Müller')."""
    s = unicodedata.normalize("NFC", s.replace("\xa0", " "))
    if "Ã" in s or "Â" in s:
        for enc in ("latin-1", "cp1252"):
            try:
                return s.encode(enc).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
    return s


def clean(s):
    return fix(re.sub(r"\s+", " ", s).strip())


def pname(s):
    return re.sub(r"\s+Steeldart$", "", clean(s))


# ---------- Rangliste ----------
def load_league():
    soup = get(f"{BASE}ligarang.php?gruppe={quote(GROUP)}")
    text = clean(soup.get_text(" "))
    i = text.find("Einzelrangliste")
    ranking = text[i:] if i >= 0 else text
    links = {}
    for a in soup.find_all("a", href=re.compile(r"sp_rapport\.php\?.*sp_nr=\d+")):
        links[re.search(r"sp_nr=(\d+)", a["href"]).group(1)] = urljoin(BASE, a["href"])
    return ranking, links


def rank_of(ranking, name):
    m = re.search(r"(?<![\d.])(\d{1,3})\.\s+" + re.escape(name) + r"(?!\w)", ranking)
    return int(m.group(1)) if m else None


# ---------- Spielrapport ----------
def parse_report(soup):
    text = clean(soup.get_text(" "))
    m = re.search(r"Region/Klasse/Gruppe\s+(\d{2}\.\d{2}\.\d{4})", text)
    rep = {"date": m.group(1) if m else "", "home": "", "guest": "", "games": [], "summary": None}
    rnd = None
    for tr in soup.find_all("tr"):
        cells = [clean(c.get_text(" ")) for c in tr.find_all(["td", "th"], recursive=False)]
        if not cells:
            continue
        if cells[0] == "HEIM-TEAM":
            rep["home"] = [c for c in cells if c][-1]
        elif cells[0] == "GAST-TEAM":
            rep["guest"] = [c for c in cells if c][-1]
        elif re.fullmatch(r"Runde \d+", cells[0]):
            rnd = int(cells[0].split()[1])
        elif len(cells) == 3 and all(re.fullmatch(r"\d+:\d+", c) for c in cells):
            rep["summary"] = cells  # Punkte, Spiele, Sätze (Heim:Gast)
        elif (len(cells) >= 4 and cells[1] and re.fullmatch(r"\d+:\d+", cells[2])
              and cells[3] in ("1:0", "0:1") and not cells[0].startswith(("Doppel", "Sudden"))):
            rep["games"].append({"round": rnd, "home": pname(cells[0]), "guest": pname(cells[1]),
                                 "sets": cells[2], "home_win": cells[3] == "1:0"})
    return rep


# ---------- Auswertung ----------
def swap(score):
    a, b = score.split(":")
    return f"{b}:{a}"


def bracket(rank):
    if rank is None:
        return None
    return "top" if rank <= TOP else "mid" if rank <= MID else "low"


def build_stats():
    ranking, links = load_league()
    print(f"{len(links)} Rapporte gefunden")
    matches, singles = [], defaultdict(list)
    for nr, url in sorted(links.items()):
        rep = parse_report(get(url))
        teams = (rep["home"].lower(), rep["guest"].lower())
        if TEAM.lower() not in teams or not rep["games"]:
            continue
        home = teams[0] == TEAM.lower()
        opp_team = rep["guest"] if home else rep["home"]
        s = rep["summary"] or ["0:0", "0:0", "0:0"]
        pts, gms = (s[0], s[1]) if home else (swap(s[0]), swap(s[1]))
        matches.append({"date": rep["date"], "opp": opp_team, "home": home, "points": pts, "games": gms})
        for g in rep["games"]:
            mine, opp = (g["home"], g["guest"]) if home else (g["guest"], g["home"])
            singles[mine].append({"opp": opp, "opp_team": opp_team, "won": g["home_win"] == home,
                                  "sets": g["sets"] if home else swap(g["sets"]), "date": rep["date"]})
    key = lambda d: datetime.strptime(d, "%d.%m.%Y") if d else datetime.min
    matches.sort(key=lambda m: key(m["date"]))

    players = []
    for name, rows in singles.items():
        for r in rows:
            r["opp_rank"] = rank_of(ranking, r["opp"])
        w = sum(r["won"] for r in rows)
        known = [r["opp_rank"] for r in rows if r["opp_rank"]]
        br = {k: [0, 0] for k in ("top", "mid", "low")}
        for r in rows:
            b = bracket(r["opp_rank"])
            if b:
                br[b][0 if r["won"] else 1] += 1
        players.append({"name": name, "rank": rank_of(ranking, name), "n": len(rows), "w": w,
                        "l": len(rows) - w, "avg_opp": sum(known) / len(known) if known else None,
                        "brackets": br, "rows": rows})
    players.sort(key=lambda p: (-(p["w"] / p["n"]), -p["n"]))
    return matches, players


# ---------- HTML ----------
esc = html.escape


def pct(w, l):
    return f"{100 * w / (w + l):.1f} %" if w + l else "–"


def bar(w, l):
    t = (w + l) or 1
    return f'<span class="bar" aria-hidden="true"><i style="width:{100 * w / t:.0f}%"></i></span>'


def player_detail(p):
    by_opp = defaultdict(list)
    for r in p["rows"]:
        by_opp[r["opp"]].append(r)
    items = sorted(by_opp.items(), key=lambda kv: (kv[1][0]["opp_rank"] or 999, kv[0]))
    body = ""
    for opp, rs in items:
        w = sum(r["won"] for r in rs)
        rk = rs[0]["opp_rank"]
        sets = ", ".join(f'<span class="{"win" if r["won"] else "loss"}">{r["sets"]}</span>' for r in rs)
        body += (f"<tr><td class='num'>{rk or '–'}</td><td>{esc(opp)}</td><td>{esc(rs[0]['opp_team'])}</td>"
                 f"<td class='num'>{w}:{len(rs) - w}</td><td>{sets}</td></tr>")
    return (f"<details><summary><b>{esc(p['name'])}</b><span>{p['w']}:{p['l']}</span></summary>"
            "<div class='scroll'><table><thead><tr><th>Rang</th><th>Gegner</th><th>Team</th><th>Bilanz</th>"
            f"<th>Sätze</th></tr></thead><tbody>{body}</tbody></table></div></details>")


def render(matches, players):
    now = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%d.%m.%Y %H:%M")
    mp = [tuple(int(x) for x in m["points"].split(":")) for m in matches]   # (eigene, gegnerische) Punkte
    wins = sum(p == (3, 0) for p in mp)
    sd_wins = sum(p == (2, 1) for p in mp)      # 9:9 nach regulären Spielen, Sudden Death gewonnen
    sd_losses = sum(p == (1, 2) for p in mp)    # Sudden Death verloren
    losses = sum(p == (0, 3) for p in mp)
    pts = sum(p[0] for p in mp)
    kpis = [("Partien", len(matches)), ("Siege", wins), ("Siege (Sudden Death)", sd_wins), ("Niederlagen", losses)]
    if sd_losses:
        kpis.append(("Niederlagen (Sudden Death)", sd_losses))
    kpis.append(("Punkte", pts))
    kpi_html = "".join(f"<div><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in kpis)
    logo = '<img class="logo" src="logo.svg" alt="Vereinslogo" width="96" height="96">' if LOGO else ""
    icon = '<link rel="icon" href="logo.svg" type="image/svg+xml">' if LOGO else ""
    W, L = sum(p["w"] for p in players), sum(p["l"] for p in players)
    allr = [r["opp_rank"] for p in players for r in p["rows"] if r["opp_rank"]]
    tb = {k: [sum(p["brackets"][k][i] for p in players) for i in (0, 1)] for k in ("top", "mid", "low")}

    mrows = "".join(
        f"<tr><td>{m['date'][:6]}</td><td>{esc(m['opp'])}</td><td>{'Heim' if m['home'] else 'Auswärts'}</td>"
        f"<td class='num'>{m['points']}</td><td class='num'>{m['games']}</td></tr>" for m in matches)

    prow = ""
    for p in players:
        b = p["brackets"]
        avg = f"{p['avg_opp']:.1f}" if p["avg_opp"] else "–"
        prow += (f"<tr><td data-v='{esc(p['name'])}'>{esc(p['name'])}</td>"
                 f"<td class='num' data-v='{p['rank'] or 9999}'>{p['rank'] or '–'}</td>"
                 f"<td class='num' data-v='{p['n']}'>{p['n']}</td>"
                 f"<td class='num' data-v='{p['w']}'>{p['w']}:{p['l']}</td>"
                 f"<td data-v='{p['w'] / p['n']:.3f}'>{bar(p['w'], p['l'])}<span class='q'>{pct(p['w'], p['l'])}</span></td>"
                 f"<td class='num' data-v='{p['avg_opp'] or 9999}'>{avg}</td>"
                 + "".join(f"<td class='num' data-v='{b[k][0] - b[k][1]}'>{b[k][0]}:{b[k][1]}</td>" for k in ("top", "mid", "low"))
                 + "</tr>")

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TEAM)} – Statistik {esc(GROUP)}</title>
{icon}
<style>{CSS}</style></head><body><main>
<header><div class="brand">{logo}<div><h1>{esc(TEAM)}</h1>
<p class="sub">Liga {esc(GROUP)} · Stand {now} · Rangliste jeweils aktuell</p></div></div>
<dl class="kpi">{kpi_html}
<div><dt>Spielbilanz (Einzel)</dt><dd>{W}:{L}</dd></div>
<div><dt>Ø Gegner-Rang</dt><dd>{(sum(allr) / len(allr)) if allr else 0:.1f}</dd></div>
</dl></header>

<section><h2>Spieler</h2>
<p class="hint">Nur Einzel, ohne Doppel und Sudden Death. Spaltenköpfe anklicken zum Sortieren. Ø Gegner-Rang: kleiner = stärkere Gegner.</p>
<div class="scroll"><table class="sortable"><thead><tr><th>Spieler</th><th>Rang</th><th>Spiele</th><th>Bilanz</th>
<th>Quote</th><th>Ø Gegner</th><th>Rang 1–{TOP}</th><th>{TOP + 1}–{MID}</th><th>{MID + 1}+</th></tr></thead>
<tbody>{prow}</tbody>
<tfoot><tr><td>Team</td><td></td><td class="num">{W + L}</td><td class="num">{W}:{L}</td><td>{pct(W, L)}</td>
<td class="num">{(sum(allr) / len(allr)) if allr else 0:.1f}</td>
<td class="num">{tb['top'][0]}:{tb['top'][1]}</td><td class="num">{tb['mid'][0]}:{tb['mid'][1]}</td><td class="num">{tb['low'][0]}:{tb['low'][1]}</td></tr></tfoot>
</table></div></section>

<section><h2>Partien</h2>
<div class="scroll"><table><thead><tr><th>Datum</th><th>Gegner</th><th>Ort</th><th>Punkte</th><th>Spiele</th></tr></thead>
<tbody>{mrows}</tbody></table></div></section>

<section><h2>Gegner pro Spieler</h2>{''.join(player_detail(p) for p in players)}</section>
<footer>Quelle: vfc.ch · täglich automatisch aktualisiert · Made by {AUTHOR}</footer>
</main><script>{JS}</script></body></html>"""


CSS = """
:root{--bg:#f2f4f1;--ink:#16221b;--mute:#5d6b62;--line:#d5dcd6;--green:#1f6b4a;--red:#b8392d;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#101712;--ink:#e6ece7;--mute:#98a89d;--line:#27332b;--green:#4fb583;--red:#e0705f;--card:#17211a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 48px}
h1{font-size:clamp(1.8rem,5vw,2.6rem);line-height:1.1;margin:0 0 4px;letter-spacing:-.02em}
h2{font-size:1.15rem;margin:36px 0 8px}
.sub,.hint,footer{color:var(--mute);font-size:.9rem;margin:0 0 12px}
footer{margin-top:40px}
.brand{display:flex;align-items:center;gap:16px}
.logo{width:clamp(64px,16vw,96px);height:auto;flex:none}
@media (prefers-color-scheme:dark){.logo{background:#f2f4f1;border-radius:14px;padding:4px}}
.kpi{display:flex;flex-wrap:wrap;gap:12px 36px;margin:20px 0 0}
.kpi div{border-left:3px solid var(--green);padding-left:10px}
.kpi dt{font-size:.8rem;color:var(--mute)}.kpi dd{margin:0;font-size:1.7rem;font-weight:700;font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.92rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-weight:600;color:var(--mute);font-size:.82rem}
.sortable th{cursor:pointer}.sortable th:hover,.sortable th:focus-visible{color:var(--ink)}
tfoot td{font-weight:700;border-top:2px solid var(--ink);border-bottom:0}
.num{text-align:right}
.bar{display:inline-block;width:64px;height:8px;background:var(--red);border-radius:4px;margin-right:8px;vertical-align:middle;overflow:hidden}
.bar i{display:block;height:100%;background:var(--green)}
.q{display:inline-block;min-width:3.6em}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:0 0 8px}
summary{cursor:pointer;padding:10px 12px;display:flex;justify-content:space-between;gap:12px}
summary span{font-variant-numeric:tabular-nums;color:var(--mute)}
details[open] summary{border-bottom:1px solid var(--line)}
.win{color:var(--green);font-weight:600}.loss{color:var(--red);font-weight:600}
.win+.win,.win+.loss,.loss+.win,.loss+.loss{margin-left:6px}
:focus-visible{outline:2px solid var(--green);outline-offset:2px}
"""

JS = """document.querySelectorAll('table.sortable th').forEach((th,i)=>{th.tabIndex=0;const go=()=>{const b=th.closest('table').tBodies[0],d=th.dataset.d=th.dataset.d==='a'?'d':'a';
[...b.rows].sort((x,y)=>{const a=x.cells[i].dataset.v??x.cells[i].textContent,c=y.cells[i].dataset.v??y.cells[i].textContent,
n=parseFloat(a),m=parseFloat(c),r=isNaN(n)||isNaN(m)?a.localeCompare(c):n-m;return d==='a'?r:-r}).forEach(r=>b.append(r))};
th.addEventListener('click',go);th.addEventListener('keydown',e=>{if(e.key==='Enter')go()})})"""


def main():
    matches, players = build_stats()
    if not players:
        raise SystemExit(f"Keine gespielten Partien für '{TEAM}' gefunden – Teamname/Gruppe prüfen.")
    OUT.mkdir(exist_ok=True)
    if LOGO:
        shutil.copyfile(LOGO, OUT / "logo.svg")
    (OUT / "index.html").write_text(render(matches, players), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps({"matches": matches, "players": players}, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    print(f"OK: {len(matches)} Partien, {len(players)} Spieler")


if __name__ == "__main__":
    main()
