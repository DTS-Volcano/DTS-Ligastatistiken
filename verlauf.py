"""Saisonverlauf: Tabellenplatz und Punkte nach jedem unserer Spieltage, Einzelquote pro Spieltag (als SVG)."""
from collections import defaultdict

from config import TEAM
from textutil import dkey, esc

W, H = 520, 210
PAD_L, PAD_R, PAD_T, PAD_B = 28, 76, 16, 30


def standings_history(data):
    """Je eigenem Spieltag: Tabelle aus allen bis dahin gespielten Partien der Liga (Punkte, dann Spiele- und Satzdifferenz)."""
    me = TEAM.lower()
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
    days = sorted({dkey(m["date"]) for m in data["matches"]})
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


def _x(i, n):
    return PAD_L + (W - PAD_L - PAD_R) * (i / (n - 1) if n > 1 else 0.5)


def _frame(labels, yt, ymap, fmt=str):
    s = ""
    for v in yt:
        y = ymap(v)
        s += (f"<line class='ch-grid' x1='{PAD_L}' x2='{W - PAD_R}' y1='{y:.1f}' y2='{y:.1f}'/>"
              f"<text class='ch-t' x='{PAD_L - 6}' y='{y + 4:.1f}' text-anchor='end'>{fmt(v)}</text>")
    n = len(labels)
    for i, lab in enumerate(labels):
        s += f"<text class='ch-t' x='{_x(i, n):.1f}' y='{H - 8}' text-anchor='middle'>{esc(lab)}</text>"
    return s


def line_chart(labels, series, yt, ymin, ymax, title, invert=False, fmt=str):
    """series: [{'name', 'vals', 'me': bool}] – eigene Reihe kräftig, Vergleichsreihe grau und dünn."""
    n = len(labels)

    def ymap(v):
        f = (v - ymin) / (ymax - ymin) if ymax != ymin else 0.5
        f = f if invert else 1 - f
        return PAD_T + (H - PAD_T - PAD_B) * f

    s = _frame(labels, yt, ymap, fmt)
    for ser in sorted(series, key=lambda x: x["me"]):
        cls = "ch-me" if ser["me"] else "ch-ref"
        pts = " ".join(f"{_x(i, n):.1f},{ymap(v):.1f}" for i, v in enumerate(ser["vals"]))
        s += f"<polyline class='{cls}' points='{pts}' fill='none'/>"
        if ser["me"]:
            for i, v in enumerate(ser["vals"]):
                s += (f"<circle class='ch-dot' cx='{_x(i, n):.1f}' cy='{ymap(v):.1f}' r='4.5'>"
                      f"<title>{esc(labels[i])}: {esc(ser['name'])} {fmt(v)}</title></circle>")
        i, v = n - 1, ser["vals"][-1]
        s += (f"<text class='ch-l{' me' if ser['me'] else ''}' x='{_x(i, n) + 9:.1f}' y='{ymap(v) + 4:.1f}'>"
              f"{esc(ser['name'])} {fmt(v)}</text>")
    return f"<svg class='chart' viewBox='0 0 {W} {H}' role='img' aria-label='{esc(title)}'>{s}</svg>"


def bar_chart(labels, vals, tips, avg, title):
    """Balken 0–100 % pro Spieltag, gestrichelte 50-%-Linie, gleitender Gesamtschnitt als Linie."""
    n = len(labels)

    def ymap(v):
        return PAD_T + (H - PAD_T - PAD_B) * (1 - v / 100)

    s = _frame(labels, (0, 25, 50, 75, 100), ymap, lambda v: f"{v}")
    s += f"<line class='ch-half' x1='{PAD_L}' x2='{W - PAD_R}' y1='{ymap(50):.1f}' y2='{ymap(50):.1f}'/>"
    bw = min(34, (W - PAD_L - PAD_R) / max(n, 1) * 0.55)
    for i, v in enumerate(vals):
        x, y = _x(i, n), ymap(v)
        h = max(2, ymap(0) - y)
        s += (f"<rect class='ch-bar' x='{x - bw / 2:.1f}' y='{ymap(0) - h:.1f}' width='{bw:.1f}' height='{h:.1f}' rx='3'>"
              f"<title>{esc(tips[i])}</title></rect>"
              f"<text class='ch-v' x='{x:.1f}' y='{ymap(0) - h - 5:.1f}' text-anchor='middle'>{v:.0f}</text>")
    pts = " ".join(f"{_x(i, n):.1f},{ymap(v):.1f}" for i, v in enumerate(avg))
    s += f"<polyline class='ch-me' points='{pts}' fill='none'/>"
    s += f"<text class='ch-l me' x='{_x(n - 1, n) + bw / 2 + 6:.1f}' y='{ymap(avg[-1]) + 4:.1f}'>Ø {avg[-1]:.0f} %</text>"
    return f"<svg class='chart' viewBox='0 0 {W} {H}' role='img' aria-label='{esc(title)}'>{s}</svg>"


def section_verlauf(data):
    hist = standings_history(data)
    if len(hist) < 2:
        return ""
    labels = [h["date"].strftime("%d.%m.") for h in hist]
    n_teams = max(h["teams"] for h in hist)
    c1 = line_chart(labels, [{"name": "Platz", "vals": [h["rank"] for h in hist], "me": True}],
                    list(range(1, n_teams + 1)), 1, n_teams, "Tabellenplatz nach jedem Spieltag", invert=True)
    pmax = max(max(h["lead"] for h in hist), 3)
    step = 3 if pmax <= 18 else 6 if pmax <= 36 else 9
    c2 = line_chart(labels, [{"name": "Führer", "vals": [h["lead"] for h in hist], "me": False},
                             {"name": "Wir", "vals": [h["pts"] for h in hist], "me": True}],
                    list(range(0, pmax + step, step)), 0, pmax + (step - pmax % step) % step or pmax,
                    "Punkte nach jedem Spieltag, wir und der Tabellenführer")
    # Einzelquote pro Spieltag
    vals, tips, tot_w, tot_l, avg = [], [], 0, 0, []
    for m in sorted(data["matches"], key=lambda m: dkey(m["date"])):
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
    ml = [dkey(m["date"]).strftime("%d.%m.") for m in sorted(data["matches"], key=lambda m: dkey(m["date"]))
          if any(m["rounds"].values())]
    c3 = bar_chart(ml, vals, tips, avg, "Einzelquote pro Spieltag mit Gesamtschnitt") if len(vals) >= 2 else ""
    rows = "".join(f"<tr><td>{labels[i]}</td><td class='num'>{h['rank']}</td><td class='num'>{h['pts']}</td>"
                   f"<td class='num'>{h['lead']}</td></tr>" for i, h in enumerate(hist))
    table = ("<details><summary>Werte als Tabelle<span></span></summary><div class='scroll'><table><thead><tr><th>Spieltag</th>"
             "<th class='num'>Platz</th><th class='num'>Punkte</th><th class='num'>Tabellenführer</th></tr></thead>"
             f"<tbody>{rows}</tbody></table></div></details>")
    return ("<section><h2>Saisonverlauf</h2><p class='hint'>Stand der Liga nach jedem unserer Spieltage, berechnet aus allen "
            "bis dahin gespielten Partien der Gruppe.</p>"
            f"<h3>Tabellenplatz</h3>{c1}<h3>Punkte</h3>{c2}"
            + (f"<h3>Einzelquote pro Spieltag</h3><p class='hint'>Anteil gewonnener Einzel pro Partie (Balken), "
               f"gestrichelt 50 %, Linie: Schnitt über alle bisherigen Spieltage. Ohne Doppel und Sudden Death.</p>{c3}" if c3 else "")
            + table + "</section>")
