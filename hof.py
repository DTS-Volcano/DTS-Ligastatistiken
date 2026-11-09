"""Hall of Fame: Bestwerte der Saison, ligaweit (alle Spieler und Vereine)."""
from awards import MIN_EINZEL
from config import TEAM
from textutil import dkey, esc


def section_hof(players, team_full, pid, id_of):
    """players: Spieler aller Vereine (Feld 'team'), team_full: Team (klein) -> Partien aus Sicht des Teams."""
    cards = []
    me = TEAM.lower()

    def plink(p):
        d = pid.get((p["team"].lower(), p["name"]))
        nm = f"<button class='tl' data-open='{d}'>{esc(p['name'])}</button>" if d else esc(p["name"])
        return f"{nm}<small>{esc(p['team'])}</small>"

    def mark(p):
        return " mine" if p["team"].lower() == me else ""

    best = (0, None)
    for p in players:
        cur = 0
        for r in p["rows"]:
            cur = cur + 1 if r["won"] else 0
            if cur > best[0]:
                best = (cur, p)
    if best[0] >= 3:
        cards.append(("Längste Siegesserie", f"{best[0]} Einzel", plink(best[1]), "in Folge gewonnen", mark(best[1])))
    top = max(players, key=lambda p: (p["w"], -p["l"]), default=None)
    if top and top["w"]:
        cards.append(("Meiste Einzelsiege", f"{top['w']} Siege", plink(top), f"bei {top['n']} Einzeln", mark(top)))
    q = [p for p in players if p["n"] >= MIN_EINZEL]
    if q:
        b = max(q, key=lambda p: (p["w"] / p["n"], p["w"]))
        cards.append(("Beste Siegquote", f"{100 * b['w'] / b['n']:.0f} %", plink(b),
                      f"{b['w']}:{b['l']}, mindestens {MIN_EINZEL} Einzel", mark(b)))
    gk = None
    for p in players:
        for r in p["rows"]:
            if r["won"] and r["opp_rank"] and (gk is None or r["opp_rank"] < gk[0]):
                gk = (r["opp_rank"], p, r["opp"], r["opp_team"])
    if gk:
        cards.append(("Stärkster bezwungener Gegner", f"Rang {gk[0]}", plink(gk[1]),
                      f"gegen {esc(gk[2])} ({esc(gk[3])})", mark(gk[1])))
    # höchster Sieg (Spiele-Differenz), Heimperspektive genügt
    bm = None
    for tl, ms in team_full.items():
        for m in ms:
            if not m["home"]:
                continue
            a, b2 = (int(x) for x in m["games"].split(":"))
            if a > b2 and (bm is None or a - b2 > bm[0]):
                bm = (a - b2, tl, m, a, b2)
    if bm:
        _, tl, m, a, b2 = bm
        home_n = next((n for n in {p["team"] for p in players} if n.lower() == tl), tl)
        dom = id_of.get(m["nr"])
        who = f"<button class='tl' data-open='{dom}'>{esc(home_n)} gegen {esc(m['opp'])}</button>" if dom else esc(home_n)
        cards.append(("Höchster Sieg", f"{a}:{b2} Spiele", who, m["date"][:6], " mine" if me in (tl, m["opp"].lower()) else ""))
    # beste Teamquote im Einzel
    tq = {}
    for p in players:
        t = tq.setdefault(p["team"], [0, 0])
        t[0] += p["w"]
        t[1] += p["l"]
    tq = {k: v for k, v in tq.items() if sum(v) >= 2 * MIN_EINZEL}
    if tq:
        k = max(tq, key=lambda k: (tq[k][0] / sum(tq[k]), tq[k][0]))
        w, l = tq[k]
        cards.append(("Beste Teamquote", f"{100 * w / (w + l):.0f} %", esc(k), f"Einzelbilanz {w}:{l}", " mine" if k.lower() == me else ""))
    # längste Siegesserie eines Teams
    bs = (0, None)
    for tl, ms in team_full.items():
        cur = 0
        for m in ms:
            a, b2 = (int(x) for x in m["points"].split(":"))
            cur = cur + 1 if a > b2 else 0
            if cur > bs[0]:
                bs = (cur, tl)
    if bs[0] >= 2:
        n = next((p["team"] for p in players if p["team"].lower() == bs[1]), bs[1])
        cards.append(("Längste Teamserie", f"{bs[0]} Partien", esc(n), "in Folge gewonnen", " mine" if bs[1] == me else ""))
    if not cards:
        return ""
    html = "".join(f"<div class='hf{c}'><p class='sub'>{esc(lab)}</p><b class='big'>{val}</b><p>{who}</p><small>{note}</small></div>"
                   for lab, val, who, note, c in cards)
    return ("<section><h2>Hall of Fame</h2><p class='hint'>Bestwerte der ganzen Liga, nur Einzel ohne Doppel und Sudden Death. "
            f"Rot umrandet: {esc(TEAM)}.</p><div class='hof-g'>{html}</div></section>")
