"""Auswertung: Spielerbilanzen, Gegnerstärke, Rangverlauf (History)."""
import json
from collections import defaultdict

from config import MID, OUT, TEAM, TOP, today
from scraper import fetch_report, load_league, rank_of
from textutil import dkey, swap


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
        rep = fetch_report(url)
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
