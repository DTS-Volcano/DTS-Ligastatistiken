"""Auszeichnungen für Spieler: Spieler des Monats und Abzeichen im Profil."""
from collections import defaultdict

from config import TOP, today
from textutil import dkey

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
MIN_EINZEL = 5     # so viele Einzel braucht es im Monat, um zu zählen


def potm_ranking(players):
    """Monat (Jahr, Monat) -> Spieler nach Quote, Siegen und Stärke der Gegner sortiert."""
    mon = defaultdict(lambda: defaultdict(lambda: {"w": 0, "l": 0, "opp": [], "team": ""}))
    for p in players:
        for r in p["rows"]:
            d = dkey(r["date"])
            if d.year < 2000:
                continue
            e = mon[(d.year, d.month)][(p.get("team") or "", p["name"])]
            e["team"] = p.get("team") or ""
            e["w" if r["won"] else "l"] += 1
            if r["opp_rank"]:
                e["opp"].append(r["opp_rank"])
    out = {}
    for k, pl in mon.items():
        rows = []
        for (_, name), e in pl.items():
            n = e["w"] + e["l"]
            if n >= MIN_EINZEL:
                rows.append({"name": name, "team": e["team"], "w": e["w"], "l": e["l"], "q": e["w"] / n,
                             "avg": sum(e["opp"]) / len(e["opp"]) if e["opp"] else 999})
        rows.sort(key=lambda x: (-x["q"], -x["w"], x["avg"], x["name"]))
        if rows:
            out[k] = rows
    return out




def monthly_titles(players):
    """Spieler -> Liste von Monatsnamen, in denen er Spieler des Monats war (nur abgeschlossene Monate)."""
    cur = (today().year, today().month)
    titles = defaultdict(list)
    for k, rows in sorted(potm_ranking(players).items()):
        if k >= cur:
            continue
        top = rows[0]
        for r in rows:
            if (r["q"], r["w"], round(r["avg"], 1)) == (top["q"], top["w"], round(top["avg"], 1)):
                titles[r["name"]].append(f"{MONTHS[k[1] - 1]} {k[0]}")
    return titles


def player_awards(p, titles):
    """Abzeichen als Liste von (Name, Erklärung). Nur was wirklich erreicht wurde."""
    rows = p["rows"]
    out = []
    for t in titles.get(p["name"], []):
        out.append((f"Spieler des Monats {t}", "Beste Siegquote im Einzel in diesem Monat (mindestens 5 Einzel)"))
    # Serien
    best = cur = 0
    for r in rows:
        cur = cur + 1 if r["won"] else 0
        best = max(best, cur)
    now = 0
    for r in reversed(rows):
        if not r["won"]:
            break
        now += 1
    if now >= 3:
        out.append((f"Siegesserie {now}", f"Die letzten {now} Einzel in Folge gewonnen"))
    if best >= 4 and best > now:
        out.append((f"Beste Serie {best}", f"Längste Siegesserie der Saison: {best} Einzel in Folge gewonnen"))
    # Giganten
    gk = sum(1 for r in rows if r["won"] and r["opp_rank"] and r["opp_rank"] <= TOP)
    if gk:
        out.append((f"Favoritenschreck ×{gk}" if gk > 1 else "Favoritenschreck", f"Einzel gegen einen Spieler der Top {TOP} gewonnen"))
    # Start
    r1 = [r for r in rows if r.get("round") == 1]
    if len(r1) >= 4 and sum(r["won"] for r in r1) / len(r1) >= 0.7:
        out.append(("Starker Starter", f"Mindestens 70 % der Einzel in Runde 1 gewonnen (aktuell {sum(r['won'] for r in r1)}:{len(r1) - sum(r['won'] for r in r1)})"))
    # perfekte Abende
    day = defaultdict(list)
    for r in rows:
        day[r["date"]].append(r["won"])
    perfect = [d for d, w in day.items() if len(w) >= 3 and all(w)]
    if perfect:
        out.append((f"Weisse Weste ×{len(perfect)}" if len(perfect) > 1 else "Weisse Weste",
                    "Alle Einzel eines Spieltags gewonnen (mindestens 3 Einzel gespielt)"))
    return out
