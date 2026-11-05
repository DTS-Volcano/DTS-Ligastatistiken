"""Lädt Tabelle, Spielplan und Spielreports von vfc.ch und liest sie in Datenstrukturen ein."""
import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from config import BASE, GROUP
from textutil import clean, pname


session = requests.Session()
session.headers["User-Agent"] = "dart-team-stats (privates Hobbyprojekt)"


class BlockedError(RuntimeError):
    """vfc.ch hat statt der Seite eine Prüfseite ausgeliefert (Bot-Schutz)."""


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
            if "your request is being verified" in txt or txt.lstrip()[:400].lower().find("one moment, please") >= 0:
                raise BlockedError(f"vfc.ch zeigt eine Prüfseite statt der Daten ({url})")
            return BeautifulSoup(txt, "html.parser")
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)


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


def fetch_report(url):
    """Lädt und liest einen einzelnen Spielreport."""
    return parse_report(get(url))
