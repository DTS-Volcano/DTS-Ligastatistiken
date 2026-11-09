"""Saisonverlauf: Tabellenplatz und Punkte nach jedem unserer Spieltage, Einzelquote pro Spieltag (als SVG)."""
from collections import defaultdict

from config import TEAM
from textutil import dkey, esc

# Zwei Geometrien: breit (Computer) und schmal (Handy). Beide werden ausgegeben, per CSS wird eine gezeigt.
WIDE = {"W": 640, "H": 240, "PL": 34, "PR": 46, "PT": 18, "PB": 32, "stride": 1, "cls": "chart-w"}
NARROW = {"W": 360, "H": 230, "PL": 28, "PR": 34, "PT": 16, "PB": 30, "stride": 2, "cls": "chart-n"}


def standings_history(data, team=None, matches=None):
    """Je eigenem Spieltag: Tabelle aus allen bis dahin gespielten Partien der Liga (Punkte, dann Spiele- und Satzdifferenz)."""
    me = (team or TEAM).lower()
    matches = data["matches"] if matches is None else matches
    res = []     # (Datum, Heim, Gast, Punkte Heim, Punkte Gast, Spiele-Diff Heim, Sätze-Diff Heim)
    mine = {m["nr"]: m for m in data["matches"]}
    for f in data["schedule"]:
        if not f["played"]:
            continue
        nr = f["nr"]
        if nr in mine:
            m = mine[nr]
            pts, games, sets = m["points"], m["games"], m.get("sets", "0:0")
            if not m["home"]:
                pts, games, sets = (":".join(reversed(x.split(":"))) for x in (pts, games, sets))
        elif nr in data["others"]:
            o = data["others"][nr]
            pts, games, sets = o["points"], o["games"], o.get("sets", "0:0")
        else:
            continue
        a = [int(x) for x in pts.split(":")]
        g = [int(x) for x in games.split(":")]
        s = [int(x) for x in sets.split(":")] if ":" in sets else [0, 0]
        res.append((dkey(f["date"]), f["home"], f["guest"], a[0], a[1], g[0] - g[1], s[0] - s[1]))
    res.sort(key=lambda r: r[0])
    days = sorted({dkey(m["date"]) for m in matches})
    out = []
    for day in days:
        tab = defaultdict(lambda: [0, 0, 0, 0])      # Punkte, Spiele-Diff, Sätze-Diff, Partien
        for d, h, g, ph, pg, gd, sd in res:
            if d > day:
                break
            for t, p, gg, ss in ((h, ph, gd, sd), (g, pg, -gd, -sd)):
                x = tab[t]
                x[0] += p
                x[1] += gg
                x[2] += ss
                x[3] += 1
        if not any(k.lower() == me for k in tab):
            continue
        order = sorted(tab, key=lambda t: (-tab[t][0], -tab[t][1], -tab[t][2], t))
        mt = next(k for k in tab if k.lower() == me)
        out.append({"date": day, "rank": order.index(mt) + 1, "pts": tab[mt][0], "lead": tab[order[0]][0],
                    "teams": len(order), "played": tab[mt][3]})
    return out


def _x(G, i, n):
    return G["PL"] + (G["W"] - G["PL"] - G["PR"]) / n * (i + 0.5)


def _ymap(G, v, lo, hi, invert=False):
    f = (v - lo) / (hi - lo) if hi != lo else 0.5
    f = f if invert else 1 - f
    return G["PT"] + (G["H"] - G["PT"] - G["PB"]) * f


def _frame(G, labels, yt, lo, hi, invert=False):
    s = ""
    n = len(labels)
    for v in yt:
        y = _ymap(G, v, lo, hi, invert)
        s += (f"<line class='ch-grid' x1='{G['PL']}' x2='{G['W'] - G['PR']}' y1='{y:.1f}' y2='{y:.1f}'/>"
              f"<text class='ch-t' x='{G['PL'] - 6}' y='{y + 4:.1f}' text-anchor='end'>{v}</text>")
    for i, lab in enumerate(labels):
        if (n - 1 - i) % G["stride"] == 0:
            s += f"<text class='ch-t' x='{_x(G, i, n):.1f}' y='{G['H'] - 9}' text-anchor='middle'>{esc(lab)}</text>"
    return s


def _wrap(G, body, title):
    return f"<svg class='chart {G['cls']}' viewBox='0 0 {G['W']} {G['H']}' role='img' aria-label='{esc(title)}'>{body}</svg>"


def line_chart(G, labels, series, yt, lo, hi, title, invert=False):
    """series: [{'name', 'vals', 'me': bool}] – eigene Reihe kräftig mit Punkten, Vergleichsreihe grau gestrichelt."""
    n = len(labels)
    s = _frame(G, labels, yt, lo, hi, invert)
    for ser in sorted(series, key=lambda x: x["me"]):
        pts = " ".join(f"{_x(G, i, n):.1f},{_ymap(G, v, lo, hi, invert):.1f}" for i, v in enumerate(ser["vals"]))
        s += f"<polyline class='{'ch-me' if ser['me'] else 'ch-ref'}' points='{pts}' fill='none'/>"
        if ser["me"]:
            for i, v in enumerate(ser["vals"]):
                s += (f"<circle class='ch-dot' cx='{_x(G, i, n):.1f}' cy='{_ymap(G, v, lo, hi, invert):.1f}' r='4'>"
                      f"<title>{esc(labels[i])}: {esc(ser['name'])} {v}</title></circle>")
        v = ser["vals"][-1]
        s += (f"<text class='ch-l{' me' if ser['me'] else ''}' x='{_x(G, n - 1, n) + 9:.1f}' "
              f"y='{_ymap(G, v, lo, hi, invert) + 4:.1f}'>{v}</text>")
    return _wrap(G, s, title)


def bar_chart(G, labels, vals, tips, avg, title):
    """Balken 0–100 % pro Spieltag mit gestricheltem Gesamtschnitt."""
    n = len(labels)
    s = _frame(G, labels, (0, 25, 50, 75, 100), 0, 100)
    ya = _ymap(G, avg, 0, 100)
    bw = min(30, (G["W"] - G["PL"] - G["PR"]) / n * 0.6)
    y0 = _ymap(G, 0, 0, 100)
    for i, v in enumerate(vals):
        x, y = _x(G, i, n), _ymap(G, v, 0, 100)
        h = max(2, y0 - y)
        s += (f"<rect class='ch-bar' x='{x - bw / 2:.1f}' y='{y0 - h:.1f}' width='{bw:.1f}' height='{h:.1f}' rx='3'>"
              f"<title>{esc(tips[i])}</title></rect>"
              f"<text class='ch-v' x='{x:.1f}' y='{y0 - h - 5:.1f}' text-anchor='middle'>{v:.0f}</text>")
    s += f"<line class='ch-avg' x1='{G['PL']}' x2='{G['W'] - G['PR']}' y1='{ya:.1f}' y2='{ya:.1f}'/>"
    s += f"<text class='ch-l me' x='{G['W'] - G['PR'] + 6}' y='{ya + 4:.1f}'>Ø {avg:.0f}</text>"
    return _wrap(G, s, title)


def both(fn, *a, **k):
    return fn(WIDE, *a, **k) + fn(NARROW, *a, **k)


def legend(items):
    return "<p class='lg'>" + "".join(f"<span><i class='k {c}'></i>{esc(t)}</span>" for c, t in items) + "</p>"


def section_verlauf(data, team=None, matches=None):
    team = team or TEAM
    matches = data["matches"] if matches is None else matches
    hist = standings_history(data, team, matches)
    if len(hist) < 2:
        return ""
    labels = [h["date"].strftime("%d.%m.") for h in hist]
    n_teams = max(h["teams"] for h in hist)
    c1 = both(line_chart, labels, [{"name": "Platz", "vals": [h["rank"] for h in hist], "me": True}],
              list(range(1, n_teams + 1)), 1, n_teams, "Tabellenplatz nach jedem Spieltag", invert=True)
    pmax = max(max(h["lead"] for h in hist), 3)
    step = 3 if pmax <= 18 else 6 if pmax <= 36 else 9
    top = -(-pmax // step) * step
    c2 = both(line_chart, labels, [{"name": "Tabellenführer", "vals": [h["lead"] for h in hist], "me": False},
                                   {"name": "Team", "vals": [h["pts"] for h in hist], "me": True}],
              list(range(0, top + 1, step)), 0, top, "Punkte nach jedem Spieltag, wir und der Tabellenführer")
    # Einzelquote pro Spieltag
    vals, tips, tot_w, tot_l, avg = [], [], 0, 0, []
    for m in sorted(matches, key=lambda m: dkey(m["date"])):
        w = l = 0
        for pairs in m["rounds"].values():
            for p in pairs:
                w += p["won"]
                l += not p["won"]
        if w + l:
            vals.append(100 * w / (w + l))
            tips.append(f"{m['date'][:6]} gegen {m['opp']}: {w}:{l} Einzel")
            tot_w, tot_l = tot_w + w, tot_l + l
            avg.append(100 * tot_w / (tot_w + tot_l))
    ml = [dkey(m["date"]).strftime("%d.%m.") for m in sorted(matches, key=lambda m: dkey(m["date"]))
          if any(m["rounds"].values())]
    c3 = both(bar_chart, ml, vals, tips, avg[-1], "Einzelquote pro Spieltag mit Gesamtschnitt") if len(vals) >= 2 else ""
    rows = "".join(f"<tr><td>{labels[i]}</td><td class='num'>{h['rank']}</td><td class='num'>{h['pts']}</td>"
                   f"<td class='num'>{h['lead']}</td></tr>" for i, h in enumerate(hist))
    table = ("<details><summary>Werte als Tabelle<span></span></summary><div class='scroll'><table><thead><tr><th>Spieltag</th>"
             "<th class='num'>Platz</th><th class='num'>Punkte</th><th class='num'>Tabellenführer</th></tr></thead>"
             f"<tbody>{rows}</tbody></table></div></details>")
    return ("<section><h2>Saisonverlauf</h2><p class='hint'>Stand der Liga nach jedem Spieltag dieses Teams, berechnet aus allen "
            "bis dahin gespielten Partien der Gruppe.</p>"
            f"<h3>Tabellenplatz</h3>{c1}<h3>Punkte</h3>{legend([('me', team), ('ref', 'Tabellenführer')])}{c2}"
            + (f"<h3>Siegquote pro Spieltag</h3>{legend([('bar', 'Gewonnene Einzel in %'), ('avg', 'Saisonschnitt')])}{c3}" if c3 else "")
            + table + "</section>")
