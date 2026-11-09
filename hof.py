"""Hall of Fame: Bestwerte der Saison."""
from collections import defaultdict

from awards import MIN_EINZEL, MONTHS
from config import TEAM
from textutil import dkey, esc


def section_hof(players, matches, pid):
    me = TEAM.lower()
    cards = []

    def plink(name):
        d = pid.get((me, name))
        return f"<button class='tl' data-open='{d}'>{esc(name)}</button>" if d else esc(name)

    # längste Siegesserie (Einzel)
    best = (0, None)
    for p in players:
        cur = 0
        for r in p["rows"]:
            cur = cur + 1 if r["won"] else 0
            if cur > best[0]:
                best = (cur, p["name"])
    if best[0] >= 3:
        cards.append(("Längste Siegesserie", f"{best[0]} Einzel", plink(best[1]), "in Folge gewonnen"))
    # meiste Siege
    top = max(players, key=lambda p: (p["w"], -p["l"]), default=None)
    if top and top["w"]:
        cards.append(("Meiste Einzelsiege", f"{top['w']} Siege", plink(top["name"]), f"bei {top['n']} Einzeln"))
    # beste Quote
    q = [p for p in players if p["n"] >= MIN_EINZEL]
    if q:
        b = max(q, key=lambda p: (p["w"] / p["n"], p["w"]))
        cards.append(("Beste Siegquote", f"{100 * b['w'] / b['n']:.0f} %", plink(b["name"]), f"{b['w']}:{b['l']}, mindestens {MIN_EINZEL} Einzel"))
    # stärkster bezwungener Gegner
    gk = None
    for p in players:
        for r in p["rows"]:
            if r["won"] and r["opp_rank"] and (gk is None or r["opp_rank"] < gk[0]):
                gk = (r["opp_rank"], p["name"], r["opp"], r["opp_team"])
    if gk:
        cards.append(("Stärkster bezwungener Gegner", f"Rang {gk[0]}", plink(gk[1]), f"gegen {esc(gk[2])} ({esc(gk[3])})"))
    # höchster Sieg (Spiele-Differenz)
    bm = None
    for i, m in enumerate(matches):
        a, b2 = (int(x) for x in m["games"].split(":"))
        if a > b2 and (bm is None or a - b2 > bm[0]):
            bm = (a - b2, i, m, a, b2)
    if bm:
        _, i, m, a, b2 = bm
        cards.append(("Höchster Sieg", f"{a}:{b2} Spiele",
                      f"<button class='tl' data-open='m{i}'>gegen {esc(m['opp'])}</button>", m["date"][:6]))
    # bester Monat (Team-Einzelquote)
    mon = defaultdict(lambda: [0, 0])
    for p in players:
        for r in p["rows"]:
            d = dkey(r["date"])
            if d.year > 2000:
                mon[(d.year, d.month)][0 if r["won"] else 1] += 1
    mon = {k: v for k, v in mon.items() if sum(v) >= 2 * MIN_EINZEL}
    if mon:
        k = max(mon, key=lambda k: (mon[k][0] / sum(mon[k]), mon[k][0]))
        w, l = mon[k]
        cards.append(("Bester Monat", f"{100 * w / (w + l):.0f} %", f"{MONTHS[k[1] - 1]} {k[0]}", f"Einzelbilanz {w}:{l}"))
    # längste Siegesserie des Teams (Partien)
    cur = best_t = 0
    for m in matches:
        a, b2 = (int(x) for x in m["points"].split(":"))
        cur = cur + 1 if a > b2 else 0
        best_t = max(best_t, cur)
    if best_t >= 2:
        cards.append(("Längste Teamserie", f"{best_t} Partien", "ohne Niederlage", "in Folge gewonnen"))
    if not cards:
        return ""
    html = "".join(f"<div class='hf'><p class='sub'>{esc(lab)}</p><b class='big'>{val}</b><p>{who}</p><small>{note}</small></div>"
                   for lab, val, who, note in cards)
    return f"<section><h2>Hall of Fame</h2><p class='hint'>Bestwerte der Saison, nur Einzel ohne Doppel und Sudden Death.</p><div class='hof-g'>{html}</div></section>"
