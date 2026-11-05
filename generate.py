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
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = "https://vfc.ch/"
GROUP = os.getenv("GROUP", "STSO S 2")
TEAM = os.getenv("TEAM", "Double Trouble Steeldarters")
TOP, MID = 10, 30          # Rang-Klassen: 1-10, 11-30, 31+
FORM_N = 5                 # Anzahl Einzel für die Formkurve
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


def today():
    return datetime.now(ZoneInfo("Europe/Zurich")).date()


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


_MOJI = re.compile("[ÃÂ][\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013\u2014"
                   "\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20ac\u2122]")


def _unmoji(m):
    for enc in ("latin-1", "cp1252"):
        try:
            return m.group().encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return m.group()


def fix(s):
    """Repariert doppelt kodierte Umlaute (z. B. 'MÃ¼ller' -> 'Müller', 'Ã\x84' -> 'Ä'), auch in gemischten Texten."""
    if "Ã" in s or "Â" in s:
        s = _MOJI.sub(_unmoji, s)
    return unicodedata.normalize("NFC", s)


def clean(s):
    return re.sub(r"\s+", " ", fix(s)).strip()


def pname(s):
    return re.sub(r"\s+Steeldart$", "", clean(s))


def dkey(d):
    for f in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(d, f)
        except (ValueError, TypeError):
            pass
    return datetime.min


# ---------- Rangliste, Tabelle, Spielplan ----------
def row_cells(tr):
    return [clean(c.get_text(" ")) for c in tr.find_all(["td", "th"], recursive=False)]


def parse_league_table(soup):
    league, seen = [], set()
    for tr in soup.find_all("tr"):
        c = row_cells(tr)
        if (len(c) >= 9 and re.fullmatch(r"\d+\.", c[0]) and c[1] and c[1].lower() not in seen
                and all(x.isdigit() for x in c[2:9])):
            n = [int(x) for x in c[2:9]]
            seen.add(c[1].lower())
            league.append({"rank": int(c[0][:-1]), "team": c[1], "played": n[0], "pp": n[1], "pm": n[2],
                           "gp": n[3], "gm": n[4], "sp": n[5], "sm": n[6]})
    return league


def parse_schedule(soup):
    fixtures = []
    for tr in soup.find_all("tr"):
        links = tr.find_all("a", href=re.compile(r"teamplan\.php\?team="))
        c = row_cells(tr)
        if len(links) != 2 or len(c) < 10 or not re.fullmatch(r"\d{2}\.\d{2}\.\d{2,4}", c[0]):
            continue
        m = re.search(r"sp_nr=(\d+)", str(tr))
        nums = c[-6:]
        fixtures.append({"nr": m.group(1) if m else "", "date": c[0], "home": clean(links[0].get_text(" ")),
                         "guest": clean(links[1].get_text(" ")), "place": c[-7],
                         "played": nums[0].isdigit() and nums[1].isdigit()})
    return fixtures


def parse_league_text(text):
    """Ersatz-Parser: liest die Tabelle aus dem reinen Text, falls die HTML-Struktur nicht passt."""
    i = text.find("Set-")
    j = text.find("Spielplan /", i)
    if i < 0 or j < 0:
        return []
    seg = text[i + 4:j]
    league, seen = [], set()
    for m in re.finditer(r"(\d{1,2})\.\s+(.+?)\s+((?:\d+\s+){6}\d+)(?=\s+\d{1,2}\.\s|\s*$)", seg.strip() + " "):
        n = [int(x) for x in m.group(3).split()]
        if m.group(2).lower() in seen:
            continue
        seen.add(m.group(2).lower())
        league.append({"rank": int(m.group(1)), "team": m.group(2), "played": n[0], "pp": n[1], "pm": n[2],
                       "gp": n[3], "gm": n[4], "sp": n[5], "sm": n[6]})
    return league


def parse_schedule_text(text, league, nrs):
    """Ersatz-Parser für den Spielplan aus dem reinen Text (Teamnamen kommen aus der Tabelle)."""
    j = text.find("Spielplan /")
    k = text.find(" GZ", j) if j >= 0 else -1
    e = text.find("Einzelrangliste", k)
    if k < 0:
        return []
    seg = text[k + 3:e if e > 0 else len(text)]
    names = "|".join(re.escape(t["team"]) for t in sorted(league, key=lambda t: -len(t["team"])))
    pat = re.compile(rf"^(\d{{2}}\.\d{{2}}\.\d{{2}})\s+({names})\s+({names})\s+(.+?)(?:\s+((?:\d+\s+){{5}}\d+))?\s*$")
    fixtures = []
    for chunk in re.split(r"(?=\b\d{2}\.\d{2}\.\d{2}\s)", seg):
        m = pat.match(chunk.strip())
        if m:
            fixtures.append({"nr": "", "date": m.group(1), "home": m.group(2), "guest": m.group(3),
                             "place": m.group(4), "played": bool(m.group(5))})
    if len(fixtures) == len(nrs):
        for f, nr in zip(fixtures, nrs):
            f["nr"] = nr
    return fixtures


def load_league():
    soup = get(f"{BASE}ligarang.php?gruppe={quote(GROUP)}")
    text = clean(soup.get_text(" "))
    i = text.find("Einzelrangliste")
    ranking = text[i:] if i >= 0 else text
    links = {}
    for a in soup.find_all("a", href=re.compile(r"sp_rapport\.php\?.*sp_nr=\d+")):
        links[re.search(r"sp_nr=(\d+)", a["href"]).group(1)] = urljoin(BASE, a["href"])
    league, schedule = parse_league_table(soup), parse_schedule(soup)
    if not league:
        league = parse_league_text(text)
        print(f"Tabelle über Text-Ersatzparser gelesen: {len(league)} Teams")
        if not league:
            k = text.find("Set-")
            print("DEBUG Tabelle nicht erkannt, Textausschnitt:", text[max(k - 80, 0):k + 400])
    if not schedule and league:
        schedule = parse_schedule_text(text, league, list(links))
        print(f"Spielplan über Text-Ersatzparser gelesen: {len(schedule)} Spiele")
        if not schedule:
            k = text.find("Spielplan /")
            print("DEBUG Spielplan nicht erkannt, Textausschnitt:", text[max(k, 0):k + 500])
    return ranking, links, league, schedule


def rank_of(ranking, name):
    m = re.search(r"(?<![\d.])(\d{1,3})\.\s+" + re.escape(name) + r"(?!\w)", ranking)
    return int(m.group(1)) if m else None


# ---------- Spielrapport ----------
def parse_report(soup):
    text = clean(soup.get_text(" "))
    m = re.search(r"Region/Klasse/Gruppe\s+(\d{2}\.\d{2}\.\d{4})", text)
    rep = {"date": m.group(1) if m else "", "home": "", "guest": "", "games": [], "summary": None,
           "extras": []}
    rnd = None
    for tr in soup.find_all("tr"):
        cells = row_cells(tr)
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
        elif (len(cells) >= 4 and cells[0].startswith(("Doppel", "Sudden")) and re.fullmatch(r"\d+:\d+", cells[2])
              and cells[3] in ("1:0", "0:1")):
            rep["extras"].append({"label": "Sudden Death" if cells[0].startswith("Sudden") else cells[0],
                                  "sets": cells[2], "home_win": cells[3] == "1:0"})
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


def order(rows):
    rows.sort(key=lambda r: (dkey(r["date"]), r.get("round") or 0))
    return rows


def build_stats():
    ranking, links, league, schedule = load_league()
    print(f"{len(links)} Rapporte gefunden, {len(league)} Teams in der Tabelle, {len(schedule)} Spiele im Spielplan")
    me = TEAM.lower()
    matches, singles = [], defaultdict(list)
    team_games = defaultdict(lambda: defaultdict(list))   # Team -> Spieler -> Einzel (Liga-weit)
    team_matches = defaultdict(list)                      # Team -> Partien (aus Sicht des Teams)
    others = {}                                           # Partien ohne uns (Sicht des Heimteams)
    for nr, url in sorted(links.items()):
        rep = parse_report(get(url))
        teams = (rep["home"].lower(), rep["guest"].lower())
        if not rep["games"]:
            continue
        for g in rep["games"]:
            for team, pl, opl, oteam, won, sets in (
                    (teams[0], g["home"], g["guest"], rep["guest"], g["home_win"], g["sets"]),
                    (teams[1], g["guest"], g["home"], rep["home"], not g["home_win"], swap(g["sets"]))):
                team_games[team][pl].append({"opp": opl, "opp_team": oteam, "won": won, "sets": sets,
                                             "date": rep["date"], "round": g["round"]})
        s = rep["summary"] or ["0:0", "0:0", "0:0"]
        for tl, oname, is_home in ((teams[0], rep["guest"], True), (teams[1], rep["home"], False)):
            team_matches[tl].append({"nr": nr, "date": rep["date"], "opp": oname, "home": is_home,
                                     "points": s[0] if is_home else swap(s[0]),
                                     "games": s[1] if is_home else swap(s[1])})
        if me not in teams:
            others[nr] = {"team": rep["home"], "date": rep["date"], "opp": rep["guest"], "home": True,
                          "points": s[0], "games": s[1], "sets": s[2], "url": url, "nr": nr,
                          "rounds": {}, "extras": [{"label": e["label"], "sets": e["sets"], "won": e["home_win"]}
                                                   for e in rep["extras"]]}
            for g in rep["games"]:
                others[nr]["rounds"].setdefault(g["round"] or 0, []).append(
                    {"mine": g["home"], "opp": g["guest"], "sets": g["sets"], "won": g["home_win"]})
            continue
        home = teams[0] == me
        opp_team = rep["guest"] if home else rep["home"]
        pts, gms = (s[0], s[1]) if home else (swap(s[0]), swap(s[1]))
        match = {"date": rep["date"], "opp": opp_team, "home": home, "points": pts, "games": gms,
                 "sets": s[2] if home else swap(s[2]), "url": url, "nr": nr, "rounds": {},
                 "extras": [{"label": e["label"], "sets": e["sets"] if home else swap(e["sets"]),
                             "won": e["home_win"] == home} for e in rep["extras"]]}
        matches.append(match)
        for g in rep["games"]:
            mine, opp = (g["home"], g["guest"]) if home else (g["guest"], g["home"])
            match["rounds"].setdefault(g["round"] or 0, []).append(
                {"mine": mine, "opp": opp, "sets": g["sets"] if home else swap(g["sets"]), "won": g["home_win"] == home})
            singles[mine].append({"opp": opp, "opp_team": opp_team, "won": g["home_win"] == home,
                                  "sets": g["sets"] if home else swap(g["sets"]), "date": rep["date"],
                                  "round": g["round"]})
    matches.sort(key=lambda m: dkey(m["date"]))
    for pl in team_games.values():
        for rows in pl.values():
            order(rows)

    players = []
    for name, rows in singles.items():
        order(rows)
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

    ranks = {}
    for pl in team_games.values():
        for name in pl:
            rk = rank_of(ranking, name)
            if rk:
                ranks[name] = rk
    return {"matches": matches, "players": players, "league": league, "schedule": schedule,
            "team_games": team_games, "ranks": ranks, "ranking": ranking,
            "team_matches": team_matches, "others": others}


# ---------- Rangverlauf (History) ----------
def update_history(ranks):
    path = OUT / "history.json"
    try:
        hist = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(hist, dict):
            hist = {}
    except (OSError, ValueError):
        hist = {}
    if ranks:
        hist[today().isoformat()] = ranks
    return hist


# ---------- HTML ----------
esc = html.escape


def pct(w, l):
    return f"{100 * w / (w + l):.1f} %" if w + l else "–"


def bar(w, l):
    t = (w + l) or 1
    return f'<span class="bar" aria-hidden="true"><i style="width:{100 * w / t:.0f}%"></i></span>'


def dots(rows, n=FORM_N):
    out = "".join(
        f'<span class="dot {"w" if r["won"] else "l"}" title="{"Sieg" if r["won"] else "Niederlage"} {esc(r["sets"])} '
        f'gegen {esc(r["opp"])} ({esc(r["date"][:6])})">{"S" if r["won"] else "N"}</span>' for r in rows[-n:])
    return f'<span class="dots">{out}</span>' if out else "–"


def spark(vals, label, lo=None, hi=None, invert=False, w=96, h=26):
    if len(vals) < 2:
        return "–"
    lo = min(vals) if lo is None else lo
    hi = max(vals) if hi is None else hi
    span = (hi - lo) or 1
    pts = []
    for i, v in enumerate(vals):
        t = (v - lo) / span
        pts.append((2 + i * (w - 4) / (len(vals) - 1), (2 + t * (h - 4)) if invert else (h - 2 - t * (h - 4))))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<polyline points="{line}"/><circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="2.4"/></svg>')


def quote_series(rows):
    out, w = [], 0
    for i, r in enumerate(rows, 1):
        w += r["won"]
        out.append(100 * w / i)
    return out


def short(name):
    parts = name.split()
    return f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else name


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


RESULT = {(3, 0): "Sieg", (2, 1): "Sieg im Sudden Death", (1, 2): "Niederlage im Sudden Death", (0, 3): "Niederlage"}


def dot(won, title=""):
    return f'<span class="dot {"w" if won else "l"}" title="{title or ("Sieg" if won else "Niederlage")}">{"S" if won else "N"}</span>'


def share_text(m):
    """Kurze Zusammenfassung einer Partie zum Einfügen in den Team-Chat."""
    pts = tuple(int(x) for x in m["points"].split(":"))
    team = m.get("team", TEAM)
    lines = [f"{team} – {m['opp']}", f"{m['points']} ({RESULT.get(pts, 'Resultat')}) · {fmt_date(m['date'])} · "
             f"{'Heimspiel' if m['home'] else 'Auswärtsspiel'}", f"Spiele {m['games']} · Sätze {m.get('sets', '–')}"]
    stat = defaultdict(lambda: [0, 0])
    for pairs in m["rounds"].values():
        for p in pairs:
            stat[p["mine"]][0 if p["won"] else 1] += 1
    if stat:
        lines += ["", "Einzel: " + ", ".join(f"{short(n)} {w}:{l}" for n, (w, l) in
                                              sorted(stat.items(), key=lambda kv: (-kv[1][0], kv[1][1], kv[0])))]
    if m["extras"]:
        lines.append(", ".join(f"{e['label']} {'Sieg' if e['won'] else 'Niederlage'} {e['sets']}" for e in m["extras"]))
    return "\n".join(lines)


def match_dialog(dom_id, m, ranks, total=None, i=0):
    pts = tuple(int(x) for x in m["points"].split(":"))
    won_match = pts[0] > pts[1]

    def pl(name):
        rk = ranks.get(name)
        return f"{esc(name)}{f' <small>#{rk}</small>' if rk else ''}"

    cards = ""
    for rnd in sorted(m["rounds"]):
        pairs = m["rounds"][rnd]
        w = sum(p["won"] for p in pairs)
        rows = "".join(
            f'<div class="pair"><span class="{"won" if p["won"] else ""}">{pl(p["mine"])}</span>'
            f'<b class="sc {"win" if p["won"] else "loss"}">{dot(p["won"])} {p["sets"]}</b>'
            f'<span class="r {"" if p["won"] else "won"}">{pl(p["opp"])}</span></div>' for p in pairs)
        cards += f'<div class="rc"><h4>Runde {rnd}<span>{w}:{len(pairs) - w}</span></h4>{rows}</div>'
    if m["extras"]:
        rows = "".join(f'<div class="pair xr"><span>{esc(e["label"])}</span>'
                       f'<b class="sc {"win" if e["won"] else "loss"}">{dot(e["won"])} {e["sets"]}</b><span></span></div>'
                       for e in m["extras"])
        cards += f'<div class="rc"><h4>Doppel und Sudden Death</h4>{rows}</div>'
    link = (f'<p class="hint"><a href="{esc(m["url"])}" target="_blank" rel="noopener">Originalreport auf vfc.ch</a></p>'
            if m.get("url") else "")
    return (f'<dialog id="{dom_id}" aria-label="Spielreport {esc(m["opp"])}"><div class="dlg">'
            f'<button class="x" data-close aria-label="Schliessen">✕</button>'
            f'<p class="sub">{fmt_date(m["date"])} · {"Heimspiel" if m["home"] else "Auswärtsspiel"}</p>'
            f'<h3 class="vs">{esc(m.get("team", TEAM))} <span class="sc {"win" if won_match else "loss"}">{m["points"]}</span> {esc(m["opp"])}</h3>'
            f'<p class="sub">{RESULT.get(pts, "")} · Spiele {m["games"]} · Sätze {m.get("sets", "–")}</p>'
            f'<div class="rounds">{cards}</div>{link}'
            f'<p><button class="rb" data-copy="{esc(share_text(m)).replace(chr(10), "&#10;")}">Zusammenfassung kopieren</button></p>'
            + (f'<div class="nav"><button class="rb nb-prev" data-go="m{i - 1}"{"" if i > 0 else " disabled"}>‹ Vorherige Partie</button>'
               f'<button class="rb nb-next" data-go="m{i + 1}"{"" if i < total - 1 else " disabled"}>Nächste Partie ›</button></div>'
               if total else "") + '</div></dialog>')


def team_dialog(idx, t, data, id_of):
    tl = t["team"].lower()
    ms = sorted(data["team_matches"].get(tl, []), key=lambda m: dkey(m["date"]))
    mrows = "".join(
        f"<tr class='click' data-open='{id_of[m['nr']]}'><td>{m['date'][:6]}</td><td>{esc(m['opp'])}</td>"
        f"<td>{'Heim' if m['home'] else 'Auswärts'}</td><td class='num'>{m['points']}</td><td class='num'>{m['games']}</td>"
        f"<td><button class='rb' data-open='{id_of[m['nr']]}'>Report</button></td></tr>" for m in ms if m["nr"] in id_of)
    pls = []
    for name, rows in data["team_games"].get(tl, {}).items():
        w = sum(r["won"] for r in rows)
        pls.append({"name": name, "rank": data["ranks"].get(name), "n": len(rows), "w": w, "rows": rows})
    pls.sort(key=lambda p: (p["rank"] or 999, -p["n"]))
    prow = "".join(
        f"<tr><td class='num'>{p['rank'] or '–'}</td><td>{esc(p['name'])}</td><td class='num'>{p['n']}</td>"
        f"<td class='num'>{p['w']}:{p['n'] - p['w']}</td><td class='num'>{pct(p['w'], p['n'] - p['w'])}</td>"
        f"<td>{dots(p['rows'])}</td></tr>" for p in pls)
    return (f'<dialog id="t{idx}" aria-label="Team {esc(t["team"])}"><div class="dlg">'
            f'<button class="x" data-close aria-label="Schliessen">✕</button>'
            f'<p class="sub">Platz {t["rank"]} in der Tabelle</p><h3 class="vs">{esc(t["team"])}</h3>'
            f'<p class="sub">{t["pp"]}:{t["pm"]} Punkte · Spiele {t["gp"]}:{t["gm"]} · Sätze {t["sp"]}:{t["sm"]} · {t["played"]} Partien</p>'
            f'<h4>Partien</h4><div class="scroll"><table class="cards"><thead><tr><th>Datum</th><th>Gegner</th><th>Ort</th><th>Punkte</th>'
            f'<th>Spiele</th><th></th></tr></thead><tbody>{mrows}</tbody></table></div>'
            f'<h4>Spieler</h4><div class="scroll"><table><thead><tr><th>Rang</th><th>Spieler</th><th>Spiele</th><th>Bilanz</th>'
            f'<th>Quote</th><th>Form (letzte {FORM_N})</th></tr></thead><tbody>{prow}</tbody></table></div>'
            f'</div></dialog>')


def fmt_date(d):
    """'02.12.26' oder '02.12.2026' -> '02.12.2026'."""
    dt = dkey(d)
    return dt.strftime("%d.%m.%Y") if dt != datetime.min else d


def section_next(data, matches):
    me = TEAM.lower()
    fx = sorted((f for f in data["schedule"] if not f["played"] and me in (f["home"].lower(), f["guest"].lower())),
                key=lambda f: (dkey(f["date"]), f["nr"]))
    if not fx:
        return "", ""
    league = {t["team"].lower(): t for t in data["league"]}
    nxt = fx[0]
    home = nxt["home"].lower() == me
    opp = nxt["guest"] if home else nxt["home"]
    ol = opp.lower()
    overdue = dkey(nxt["date"]).date() < today()
    t = league.get(ol)
    meta = [f"{fmt_date(nxt['date'])}{' (Termin offen / nachzuholen)' if overdue else ''}",
            "Heimspiel" if home else "Auswärtsspiel"]
    if nxt["place"]:
        meta.append(esc(nxt["place"]))
    lines = [" · ".join(meta)]
    if t:
        lines.append(f"{esc(opp)} steht auf Platz {t['rank']} mit {t['pp']} Punkten aus {t['played']} Partien "
                     f"(Spiele {t['gp']}:{t['gm']}).")
    earlier = [m for m in matches if m["opp"].lower() == ol]
    if earlier:
        lines.append("Bisher gegen sie: " + ", ".join(
            f"{m['points']} ({m['date'][:6]}, {'Heim' if m['home'] else 'Auswärts'}, Spiele {m['games']})" for m in earlier) + ".")
    else:
        lines.append("Gegen dieses Team habt ihr in dieser Saison noch nicht gespielt.")

    tidx = next((k for k, x in enumerate(data["league"]) if x["team"].lower() == ol), None)

    # Gegner-Kader
    vs_us = defaultdict(lambda: defaultdict(lambda: [0, 0]))     # Gegner -> unser Spieler -> [Siege Gegner, Niederlagen Gegner]
    for p in data["players"]:
        for r in p["rows"]:
            if r["opp_team"].lower() == ol:
                vs_us[r["opp"]][p["name"]][0 if not r["won"] else 1] += 1
    roster = []
    for name, rows in data["team_games"].get(ol, {}).items():
        w = sum(r["won"] for r in rows)
        roster.append({"name": name, "rank": data["ranks"].get(name), "n": len(rows), "w": w, "rows": rows})
    roster.sort(key=lambda r: (r["rank"] or 999, -r["n"]))
    if roster:
        body = ""
        for r in roster:
            vs = ", ".join(f"{esc(short(n))} {a}:{b}" for n, (a, b) in vs_us.get(r["name"], {}).items()) or "–"
            body += (f"<tr><td class='num'>{r['rank'] or '–'}</td><td>{esc(r['name'])}</td>"
                     f"<td class='num'>{r['n']}</td><td class='num'>{r['w']}:{r['n'] - r['w']}</td>"
                     f"<td class='num'>{pct(r['w'], r['n'] - r['w'])}</td><td>{dots(r['rows'])}</td><td>{vs}</td></tr>")
        table = ("<div class='scroll'><table><thead><tr><th>Rang</th><th>Spieler</th><th>Spiele</th><th>Bilanz</th>"
                 f"<th>Quote</th><th>Form (letzte {FORM_N})</th><th>Gegen euch (aus ihrer Sicht)</th></tr></thead>"
                 f"<tbody>{body}</tbody></table></div>")
    else:
        table = "<p class='hint'>Von diesem Team sind noch keine Einzel bekannt.</p>"

    nxt_html = (f"<section class='next'><h2>Nächstes Spiel: {esc(opp)}</h2>"
                + "".join(f"<p class='sub'>{l}</p>" for l in lines)
                + (f"<p><button class='rb' data-open='t{tidx}'>Team {esc(opp)} ansehen</button></p>" if tidx is not None else "")
                + table + "</section>")

    rows = ""
    for i, f in enumerate(fx):
        h = f["home"].lower() == me
        o = f["guest"] if h else f["home"]
        ot = league.get(o.lower())
        rows += (f"<tr{' class=hl' if i == 0 else ''}><td>{fmt_date(f['date'])}</td><td>{esc(o)}</td>"
                 f"<td class='num'>{ot['rank'] if ot else '–'}</td><td>{'Heim' if h else 'Auswärts'}</td>"
                 f"<td>{esc(f['place'])}</td></tr>")
    open_html = ("<h2>Ausstehende Spiele</h2><div class='scroll'><table class='cards up'><thead><tr><th>Datum</th><th>Gegner</th>"
                 f"<th>Platz</th><th>Ort</th><th>Spielort</th></tr></thead><tbody>{rows}</tbody></table></div>")
    return nxt_html, open_html


def section_league(data):
    if not data["league"]:
        return ("<section><h2>Tabelle</h2><p class='hint'>Die Tabelle konnte von vfc.ch gerade nicht gelesen werden. "
                "Der nächste automatische Lauf versucht es erneut.</p>")
    me = TEAM.lower()
    rows = "".join(
        f"<tr class='click{' hl' if t['team'].lower() == me else ''}' data-open='t{i}'><td class='num'>{t['rank']}</td>"
        f"<td><button class='tl' data-open='t{i}'>{esc(t['team'])}</button></td>"
        f"<td class='num'>{t['played']}</td><td class='num'>{t['pp']}:{t['pm']}</td>"
        f"<td class='num'>{t['gp']}:{t['gm']}</td><td class='num'>{t['sp']}:{t['sm']}</td></tr>" for i, t in enumerate(data["league"]))
    return ("<section><h2>Tabelle</h2><p class='hint'>Auf ein Team klicken, um dessen Partien und Spieler zu sehen.</p><div class='scroll'><table><thead><tr><th>Platz</th><th>Team</th><th>Partien</th>"
            f"<th>Punkte</th><th>Spiele</th><th>Sätze</th></tr></thead><tbody>{rows}</tbody></table></div>")


def section_form(players):
    def score(p):
        last = p["rows"][-FORM_N:]
        return (-(sum(r["won"] for r in last) / len(last)), -len(last))
    body = ""
    for p in sorted(players, key=score):
        last = p["rows"][-FORM_N:]
        lw = sum(r["won"] for r in last)
        q_all = 100 * p["w"] / p["n"]
        q_last = 100 * lw / len(last)
        diff = q_last - q_all
        trend = "▲" if diff >= 10 else "▼" if diff <= -10 else "–"
        cls = "up" if trend == "▲" else "down" if trend == "▼" else ""
        body += (f"<tr><td>{esc(p['name'])}</td><td>{dots(p['rows'])}</td>"
                 f"<td class='num'>{lw}:{len(last) - lw}</td><td class='num'>{q_all:.0f} %</td>"
                 f"<td class='num {cls}'>{trend}</td>"
                 f"<td>{spark(quote_series(p['rows']), 'Verlauf der Siegquote von ' + p['name'], 0, 100)}</td></tr>")
    return ("<section><h2>Form</h2><p class='hint'>Letzte Einzel von links (älter) nach rechts (neuer). S = Sieg, N = Niederlage. "
            "Trend: ▲ letzte Einzel mindestens 10 Prozentpunkte besser als die Gesamtquote, ▼ mindestens 10 schlechter. "
            "Die Kurve zeigt die Siegquote nach jedem Einzel.</p><div class='scroll'><table class='sticky'><thead><tr><th>Spieler</th>"
            f"<th>Letzte {FORM_N}</th><th>Bilanz</th><th>Quote gesamt</th><th>Trend</th><th>Verlauf</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div></section>")


def section_rank_history(players, hist):
    days = sorted(hist)
    if not days:
        return ""
    t = today().isoformat()
    prior = [d for d in days if d < t]
    limit = (today() - timedelta(days=7)).isoformat()
    older = [d for d in prior if d <= limit]
    base = older[-1] if older else (prior[0] if prior else None)
    first = datetime.strptime(days[0], "%Y-%m-%d").strftime("%d.%m.%Y")
    body = ""
    for p in sorted(players, key=lambda p: (p["rank"] or 999, p["name"])):
        series = [hist[d][p["name"]] for d in days if p["name"] in hist[d]]
        cur = p["rank"]
        change = "–"
        if base and cur and p["name"] in hist[base]:
            d = hist[base][p["name"]] - cur
            change = f'<span class="up">▲ {d}</span>' if d > 0 else f'<span class="down">▼ {-d}</span>' if d < 0 else "0"
        body += (f"<tr><td>{esc(p['name'])}</td><td class='num'>{cur or '–'}</td><td class='num'>{change}</td>"
                 f"<td>{spark(series, 'Rangverlauf von ' + p['name'], invert=True)}</td></tr>")
    if base:
        since = datetime.strptime(base, "%Y-%m-%d").strftime("%d.%m.%Y")
        note = (f"Veränderung seit {since} (▲ besser, ▼ schlechter). Die Aufzeichnung läuft seit {first}. "
                "Die Kurve zeigt den Rang, oben ist Rang 1.")
    else:
        note = (f"Die Aufzeichnung hat am {first} begonnen. Veränderung und Verlauf erscheinen, "
                "sobald ein weiterer Tag gespeichert ist.")
    return (f"<section><h2>Rangverlauf</h2><p class='hint'>{note}</p><div class='scroll'><table class='sticky'><thead><tr><th>Spieler</th>"
            f"<th>Rang heute</th><th>Veränderung</th><th>Verlauf</th></tr></thead><tbody>{body}</tbody></table></div></section>")


def render(data, hist):
    matches, players = data["matches"], data["players"]
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
        f"<tr class='click' data-open='m{i}'><td>{m['date'][:6]}</td><td>{esc(m['opp'])}</td><td>{'Heim' if m['home'] else 'Auswärts'}</td>"
        f"<td class='num'>{m['points']}</td><td class='num'>{m['games']}</td>"
        f"<td><button class='rb' data-open='m{i}'>Report</button></td></tr>" for i, m in enumerate(matches))
    id_of = {m["nr"]: f"m{i}" for i, m in enumerate(matches)}
    id_of.update({nr: f"o{nr}" for nr in data["others"]})
    dialogs = "".join(match_dialog(f"m{i}", m, data["ranks"], len(matches), i) for i, m in enumerate(matches))
    dialogs += "".join(match_dialog(f"o{nr}", m, data["ranks"]) for nr, m in data["others"].items())
    dialogs += "".join(team_dialog(i, t, data, id_of) for i, t in enumerate(data["league"]))

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

    next_html, open_html = section_next(data, matches)
    league_html = section_league(data) + "</section>"
    open_html = f"<section>{open_html}</section>" if open_html else ""
    last_html = ""
    if matches:
        items = ""
        for i, m in reversed(list(enumerate(matches))[-3:]):
            pt = tuple(int(x) for x in m["points"].split(":"))
            items += (f"<li><button class='resrow' data-open='m{i}'><span class='rd'>{m['date'][:6]}</span>"
                      f"<span class='ro'>{esc(m['opp'])}<small>{RESULT.get(pt, '')} · {'Heim' if m['home'] else 'Auswärts'}</small></span>"
                      f"<b class='sc {'win' if pt[0] > pt[1] else 'loss'}'>{m['points']}</b></button></li>")
        last_html = (f"<section><h2>Letzte Ergebnisse</h2><ul class='res'>{items}</ul>"
                     "<p class='hint'><a href='#partien'>Alle Partien ansehen</a></p></section>")
    tabs = "".join(f'<a href="#{k}">{n}</a>' for k, n in (("uebersicht", "Übersicht"), ("spieler", "Spieler"),
                                                          ("liga", "Liga"), ("partien", "Partien")))

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TEAM)} – Statistik {esc(GROUP)}</title>
{icon}
<style>{CSS}</style><script>document.documentElement.className='js'</script></head><body><main>
<header><div class="brand">{logo}<div><h1>{esc(TEAM)}</h1>
<p class="sub">Liga {esc(GROUP)} · Stand {now} · Rangliste jeweils aktuell</p></div></div></header>
<nav class="tabs" aria-label="Bereiche">{tabs}</nav>

<div class="panel" id="p-uebersicht">
<dl class="kpi">{kpi_html}
<div><dt>Spielbilanz (Einzel)</dt><dd>{W}:{L}</dd></div>
<div><dt>Ø Gegner-Rang</dt><dd>{(sum(allr) / len(allr)) if allr else 0:.1f}</dd></div>
</dl>
{next_html}
{last_html}
{open_html}
</div>

<div class="panel" id="p-spieler">
<section><h2>Spieler</h2>
<p class="hint">Nur Einzel, ohne Doppel und Sudden Death. Spaltenköpfe anklicken zum Sortieren. Ø Gegner-Rang: kleiner = stärkere Gegner.</p>
<div class="scroll"><table class="sortable sticky"><thead><tr><th>Spieler</th><th>Rang</th><th>Spiele</th><th>Bilanz</th>
<th>Quote</th><th>Ø Gegner</th><th>Rang 1–{TOP}</th><th>{TOP + 1}–{MID}</th><th>{MID + 1}+</th></tr></thead>
<tbody>{prow}</tbody>
<tfoot><tr><td>Team</td><td></td><td class="num">{W + L}</td><td class="num">{W}:{L}</td><td>{pct(W, L)}</td>
<td class="num">{(sum(allr) / len(allr)) if allr else 0:.1f}</td>
<td class="num">{tb['top'][0]}:{tb['top'][1]}</td><td class="num">{tb['mid'][0]}:{tb['mid'][1]}</td><td class="num">{tb['low'][0]}:{tb['low'][1]}</td></tr></tfoot>
</table></div></section>

{section_form(players)}

{section_rank_history(players, hist)}

<section><h2>Gegner pro Spieler</h2>{''.join(player_detail(p) for p in players)}</section>
</div>

<div class="panel" id="p-liga">
{league_html}
</div>

<div class="panel" id="p-partien">
<section><h2>Partien</h2>
<p class="hint">Auf eine Partie klicken, um den Spielreport zu öffnen.</p>
<div class="scroll"><table class="cards"><thead><tr><th>Datum</th><th>Gegner</th><th>Ort</th><th>Punkte</th><th>Spiele</th><th></th></tr></thead>
<tbody>{mrows}</tbody></table></div></section>

</div>
<footer>Quelle: vfc.ch · täglich automatisch aktualisiert · Made by {AUTHOR}</footer>
</main>{dialogs}<script>{JS}</script></body></html>"""


CSS = """
:root{--bg:#f2f4f1;--ink:#16221b;--mute:#5d6b62;--line:#d5dcd6;--green:#1f6b4a;--red:#b8392d;--card:#fff;--hl:#e3efe7}
@media (prefers-color-scheme:dark){:root{--bg:#101712;--ink:#e6ece7;--mute:#98a89d;--line:#27332b;--green:#4fb583;--red:#e0705f;--card:#17211a;--hl:#1d3326}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 48px}
h1{font-size:clamp(1.8rem,5vw,2.6rem);line-height:1.1;margin:0 0 4px;letter-spacing:-.02em}
h2{font-size:1.15rem;margin:36px 0 8px}
h3{font-size:1rem;margin:22px 0 6px}
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
tr.hl td{background:var(--hl);font-weight:600}
.next{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--green);border-radius:8px;padding:4px 16px 16px;margin-top:28px}
.next h2{margin-top:14px}
.next .sub{margin:0 0 6px}
.dots{display:inline-flex;gap:3px;vertical-align:middle}
.dot{display:inline-block;width:20px;height:20px;line-height:20px;text-align:center;border-radius:50%;font-size:.7rem;font-weight:700;color:#fff;cursor:default}
.dot.w{background:var(--green)}.dot.l{background:var(--red)}
@media (prefers-color-scheme:dark){.dot{color:#0d140f}}
.spark{vertical-align:middle;overflow:visible}
.spark polyline{fill:none;stroke:var(--green);stroke-width:1.8;stroke-linejoin:round;stroke-linecap:round}
.spark circle{fill:var(--green)}
.up{color:var(--green);font-weight:600}.down{color:var(--red);font-weight:600}
tr.click{cursor:pointer}tr.click:hover td{background:var(--hl)}
.rb{font:inherit;font-size:.82rem;color:var(--green);background:none;border:1px solid var(--green);border-radius:6px;padding:2px 10px;cursor:pointer}
.nav{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:14px}
.tl{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer;text-align:left;text-decoration:underline dotted;text-underline-offset:3px}
.dlg h4{margin:16px 0 6px;font-size:.95rem}
.rb[disabled]{opacity:.35;cursor:default}.rb[disabled]:hover{background:none;color:var(--green)}
.rb:hover{background:var(--green);color:var(--bg)}
dialog{border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--ink);padding:0;width:min(780px,calc(100vw - 20px));max-height:calc(100vh - 20px)}
dialog::backdrop{background:rgba(0,0,0,.55)}
.dlg{padding:18px 18px 12px;position:relative}
.dlg .x{position:absolute;top:10px;right:10px;font:inherit;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;width:34px;height:34px;cursor:pointer}
.vs{font-size:clamp(1.1rem,3.6vw,1.5rem);margin:2px 44px 4px 0;line-height:1.3}
.vs .sc{display:inline-block;padding:0 10px;margin:0 4px;border-radius:8px;background:var(--card);border:1px solid var(--line)}
.rounds{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin-top:14px}
.rc{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 12px 8px}
.rc h4{display:flex;justify-content:space-between;margin:4px 0 6px;font-size:.9rem}
.rc h4 span{color:var(--mute);font-variant-numeric:tabular-nums}
.pair{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;padding:5px 0;border-top:1px solid var(--line);font-size:.9rem}
.pair .r{text-align:right}.pair small{color:var(--mute)}.pair .won{font-weight:700}
.pair .sc{font-variant-numeric:tabular-nums;white-space:nowrap}
a{color:var(--green)}
.js .panel{display:none}.js .panel.on{display:block}
.tabs{display:flex;gap:4px;position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);margin:18px -16px 0;padding:0 12px}
.tabs a{flex:1;text-align:center;padding:12px 8px;color:var(--mute);text-decoration:none;font-weight:600;border-bottom:3px solid transparent;margin-bottom:-1px}
.tabs a:hover{color:var(--ink)}.tabs a.on{color:var(--green);border-bottom-color:var(--green)}
.res{list-style:none;margin:0;padding:0}
.resrow{all:unset;box-sizing:border-box;display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;width:100%;padding:10px 4px;border-bottom:1px solid var(--line);cursor:pointer}
.resrow:hover{background:var(--hl)}.resrow:focus-visible{outline:2px solid var(--green);outline-offset:-2px}
.resrow .rd{color:var(--mute);font-variant-numeric:tabular-nums}
.resrow small{display:block;color:var(--mute);font-size:.8rem}
.resrow .sc{font-size:1.2rem;font-variant-numeric:tabular-nums}
.sticky td:first-child,.sticky th:first-child{position:sticky;left:0;background:var(--bg);z-index:1}
.sticky tfoot td:first-child{background:var(--bg)}
@media (max-width:700px){
.tabs{position:fixed;top:auto;bottom:0;left:0;right:0;margin:0;padding:0 4px calc(env(safe-area-inset-bottom) + 0px);border-bottom:0;border-top:1px solid var(--line)}
.tabs a{border-bottom:0;border-top:3px solid transparent;margin:-1px 0 0;padding:14px 4px}
.tabs a.on{border-top-color:var(--green)}
main{padding-bottom:84px}
th,td{padding:7px 6px}
table.cards,table.cards tbody{display:block}
table.cards thead{display:none}
table.cards tr{display:grid;grid-template-columns:auto 1fr auto auto;grid-template-areas:"d o o p" "d c g b";gap:2px 10px;align-items:center;padding:10px 4px;border-bottom:1px solid var(--line)}
table.cards td{border:0;padding:0;white-space:normal;text-align:left}
table.cards td:nth-child(1){grid-area:d;color:var(--mute)}
table.cards td:nth-child(2){grid-area:o;font-weight:600}
table.cards td:nth-child(3){grid-area:c;color:var(--mute);font-size:.85rem}
table.cards td:nth-child(4){grid-area:p;font-weight:700;font-size:1.05rem;text-align:right}
table.cards td:nth-child(5){grid-area:g;color:var(--mute);font-size:.85rem}
table.cards td:nth-child(5)::before{content:"Spiele "}
table.cards td:nth-child(6){grid-area:b;text-align:right}
table.cards.up tr{grid-template-areas:"d o o p" "d c g g"}
table.cards.up td:nth-child(3){grid-area:p;text-align:right;color:var(--mute);font-size:.85rem}
table.cards.up td:nth-child(3)::before{content:"Platz "}
table.cards.up td:nth-child(4){grid-area:c;font-weight:400;font-size:.85rem;color:var(--mute);text-align:left}
table.cards.up td:nth-child(5){grid-area:g;font-size:.85rem}
table.cards.up td:nth-child(5)::before{content:""}
}
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
th.addEventListener('click',go);th.addEventListener('keydown',e=>{if(e.key==='Enter')go()})});
const TABS=['uebersicht','spieler','liga','partien'];
function showTab(){let h=(location.hash||'').slice(1);if(!TABS.includes(h))h='uebersicht';
document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id==='p-'+h));
document.querySelectorAll('.tabs a').forEach(a=>{const on=a.getAttribute('href')==='#'+h;a.classList.toggle('on',on);if(on)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
window.scrollTo(0,0)}
addEventListener('hashchange',showTab);showTab();
document.addEventListener('keydown',e=>{const d=document.querySelector('dialog[open]');
if(!d||(e.key!=='ArrowLeft'&&e.key!=='ArrowRight'))return;const b=d.querySelector(e.key==='ArrowLeft'?'.nb-prev':'.nb-next');if(b&&!b.disabled)b.click()});
document.addEventListener('click',e=>{const c=e.target.closest('[data-copy]');
if(c){const txt=c.dataset.copy,o=c.textContent,done=()=>{c.textContent='Kopiert ✓';setTimeout(()=>{c.textContent=o},1800)};
const fb=()=>{const a=document.createElement('textarea');a.value=txt;(c.closest('dialog')||document.body).appendChild(a);a.select();
try{document.execCommand('copy');done()}catch(_){c.textContent='Kopieren nicht möglich'}a.remove()};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,fb)}else{fb()}return}
const g=e.target.closest('[data-go]');
if(g){if(!g.disabled){const n=document.getElementById(g.dataset.go);if(n){g.closest('dialog').close();n.showModal()}}return}
const t=e.target.closest('[data-open]');
if(t){const d=document.getElementById(t.dataset.open);if(d&&d.showModal){document.querySelectorAll('dialog[open]').forEach(x=>x.close());d.showModal()}return}
const d=e.target.closest('dialog');if(e.target.tagName==='DIALOG'||e.target.closest('[data-close]'))(d||e.target).close()})"""


def main():
    data = build_stats()
    if not data["players"]:
        raise SystemExit(f"Keine gespielten Partien für '{TEAM}' gefunden – Teamname/Gruppe prüfen.")
    OUT.mkdir(exist_ok=True)
    if LOGO:
        shutil.copyfile(LOGO, OUT / "logo.svg")
    hist = update_history(data["ranks"])
    (OUT / "history.json").write_text(json.dumps(hist, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (OUT / "index.html").write_text(render(data, hist), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps({"matches": data["matches"], "players": data["players"],
                                               "league": data["league"], "schedule": data["schedule"]},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(data['matches'])} Partien, {len(data['players'])} Spieler")


if __name__ == "__main__":
    main()
