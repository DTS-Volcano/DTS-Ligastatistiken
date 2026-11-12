"""Auswertung: Spielerbilanzen, Gegnerstärke, Rangverlauf (History)."""
import json
from collections import defaultdict

from config import CACHE, MID, OUT, TEAM, TOP, today
import scraper
from scraper import BlockedError, fetch_report, load_league, rank_of
from textutil import dkey, swap


def bracket(rank):
    if rank is None:
        return None
    return "top" if rank <= TOP else "mid" if rank <= MID else "low"


def order(rows):
    rows.sort(key=lambda r: (dkey(r["date"]), r.get("round") or 0))
    return rows


def load_report(nr, url, state):
    """Gespielte Reports ändern sich nicht mehr: einmal laden, dann aus daten/reports/ lesen.
    Bei Sperre oder Netzfehler wird mit den gespeicherten Reports weitergearbeitet."""
    f = CACHE / f"{nr}.json"
    try:
        rep = json.loads(f.read_text(encoding="utf-8"))
        state["cached"] += 1
        return rep
    except (OSError, ValueError):
        pass
    if state["stop"]:
        return None
    try:
        rep = fetch_report(url)
    except BlockedError as e:
        state["stop"] = True
        state["error"] = e
        print(f"HINWEIS: {e} – weitere neue Reports werden beim nächsten Lauf geholt.")
        return None
    except Exception as e:      # Netzfehler bei einem einzelnen Report darf nicht alles stoppen
        print(f"HINWEIS: Report {nr} nicht ladbar ({e}), nächster Lauf versucht es erneut.")
        return None
    if rep["games"] and rep["summary"]:
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        state["new"] += 1
    return rep


def build_stats():
    ranking, links, league, schedule = load_league()
    print(f"{len(links)} Rapporte gefunden, {len(league)} Teams in der Tabelle, {len(schedule)} Spiele im Spielplan")
    me = TEAM.lower()
    matches, singles = [], defaultdict(list)
    team_games = defaultdict(lambda: defaultdict(list))   # Team -> Spieler -> Einzel (Liga-weit)
    team_matches = defaultdict(list)                      # Team -> Partien (aus Sicht des Teams)
    others = {}                                           # Partien ohne uns (Sicht des Heimteams)
    team_full = defaultdict(list)                         # Team -> Partien mit Runden (Sicht des Teams, wie matches)
    state = {"cached": 0, "new": 0, "stop": False, "error": None}
    for nr, url in sorted(links.items()):
        rep = load_report(nr, url, state)
        if rep is None:
            continue
        teams = (rep["home"].lower(), rep["guest"].lower())
        if not rep["games"]:
            continue
        for g in rep["games"]:
            for team, pl, opl, oteam, won, sets, is_home in (
                    (teams[0], g["home"], g["guest"], rep["guest"], g["home_win"], g["sets"], True),
                    (teams[1], g["guest"], g["home"], rep["home"], not g["home_win"], swap(g["sets"]), False)):
                team_games[team][pl].append({"opp": opl, "opp_team": oteam, "won": won, "sets": sets,
                                             "date": rep["date"], "round": g["round"], "home": is_home})
        s = rep["summary"] or ["0:0", "0:0", "0:0"]
        for tl, oname, is_home in ((teams[0], rep["guest"], True), (teams[1], rep["home"], False)):
            team_matches[tl].append({"nr": nr, "date": rep["date"], "opp": oname, "home": is_home,
                                     "points": s[0] if is_home else swap(s[0]),
                                     "games": s[1] if is_home else swap(s[1])})
        for tl, is_home in ((teams[0], True), (teams[1], False)):
            f = {"date": rep["date"], "opp": rep["guest"] if is_home else rep["home"], "home": is_home,
                 "points": s[0] if is_home else swap(s[0]), "games": s[1] if is_home else swap(s[1]),
                 "sets": s[2] if is_home else swap(s[2]), "nr": nr, "rounds": {}, "extras": []}
            for g in rep["games"]:
                mine, opp = (g["home"], g["guest"]) if is_home else (g["guest"], g["home"])
                f["rounds"].setdefault(g["round"] or 0, []).append(
                    {"mine": mine, "opp": opp, "sets": g["sets"] if is_home else swap(g["sets"]),
                     "won": g["home_win"] == is_home})
            team_full[tl].append(f)
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
                                  "round": g["round"], "home": home})
    print(f"Reports: {state['cached']} aus dem Speicher, {state['new']} neu geladen")
    if state["error"] and not matches:
        raise state["error"]
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
            "team_matches": team_matches, "others": others, "teaminfo": load_teaminfo(league),
            "team_full": {k: sorted(v, key=lambda m: dkey(m["date"])) for k, v in team_full.items()}}


def load_teaminfo(league):
    """Lokal, Adresse und Captain aller Teams (find_team.php). Bei Fehlern bleibt der gespeicherte Stand erhalten."""
    from config import CACHE
    path = CACHE.parent / f"teaminfo-{CACHE.name}.json"
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        info = {}
    old = json.dumps(info, sort_keys=True)
    for t in league:
        tl = t["team"].lower()
        code = scraper.TEAM_CODES.get(tl)
        if not code:
            continue
        try:
            got = scraper.fetch_teaminfo(code)
        except Exception as e:              # Netz, Bot-Schutz, geänderte Seite: alten Stand behalten
            print(f"Teaminfo {t['team']}: {type(e).__name__}")
            continue
        if any(got.values()):
            info[tl] = {**got, "code": code}
    if json.dumps(info, sort_keys=True) != old:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(info, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return info


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


def quote_series(rows):
    out, w = [], 0
    for i, r in enumerate(rows, 1):
        w += r["won"]
        out.append(100 * w / i)
    return out
