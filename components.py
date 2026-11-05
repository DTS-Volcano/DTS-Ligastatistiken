"""Wiederverwendbare HTML-Bausteine: Form-Punkte, Kurven, Report- und Team-Fenster."""
from collections import defaultdict

from datetime import datetime

from config import FORM_N, TEAM, find_photo
from stats import quote_series
from textutil import dkey, esc, fmt_date, pct, short


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


def avatar(name, size=112):
    """Spielerbild (aus spieler/) oder Initialen im Rahmen."""
    photo = find_photo(name)
    if photo:
        return f'<img class="pic" src="spieler/{esc(photo)}" alt="{esc(name)}" width="{size}" height="{size}" loading="lazy">'
    initials = "".join(w[0] for w in name.split()[:2]).upper()
    return f'<span class="pic ini" aria-hidden="true">{esc(initials)}</span>'


def player_dialog(idx, p, total, hist):
    """Spielerprofil als Fenster: Bild, Kennzahlen, Form, Rangverlauf, Runden, Lieblings-/Angstgegner, alle Einzel."""
    name = p["name"]
    pic = avatar(name)
    rows = p["rows"]
    quote = pct(p["w"], p["l"])
    avg = f"{p['avg_opp']:.1f}" if p["avg_opp"] else "–"
    kp = (f"<div><dt>Rang</dt><dd>{p['rank'] or '–'}</dd></div><div><dt>Bilanz</dt><dd>{p['w']}:{p['l']}</dd></div>"
          f"<div><dt>Quote</dt><dd>{quote}</dd></div><div><dt>Ø Gegner</dt><dd>{avg}</dd></div>")
    # Form und Quotenverlauf
    form = (f"<h4>Form</h4><p class='prow'>{dots(rows, 10)} {spark(quote_series(rows), 'Siegquote nach jedem Einzel', 0, 100)}</p>"
            if rows else "")
    # Rangverlauf
    days = sorted(hist)
    series = [hist[d][name] for d in days if name in hist[d]]
    rv = ""
    if len(series) >= 2:
        d = series[0] - series[-1]
        ch = f' <span class="{"up" if d > 0 else "down"}">{"▲" if d > 0 else "▼"} {abs(d)}</span>' if d else ""
        rv = (f"<h4>Rangverlauf</h4><p class='prow'>Rang {series[-1]}{ch} {spark(series, 'Rangverlauf', invert=True)}</p>"
              f"<p class='hint'>Seit {datetime.strptime(days[0], '%Y-%m-%d').strftime('%d.%m.%Y')}, oben ist Rang 1.</p>")
    # Runden
    rd = defaultdict(lambda: [0, 0])
    for r in rows:
        if r.get("round"):
            rd[r["round"]][0 if r["won"] else 1] += 1
    rcells = ""
    if rd:
        for k in sorted(rd):
            w, l = rd[k]
            cls = "win" if w > l else "loss" if w < l else ""
            rcells += f"<div><dt>Runde {k}</dt><dd class='{cls}'>{w}:{l}</dd></div>"
        rcells = f"<h4>Nach Spielblock</h4><dl class='kpi rk'>{rcells}</dl>"
    # Gegner
    by_opp = defaultdict(list)
    for r in rows:
        by_opp[r["opp"]].append(r)
    agg = []
    for opp, rs in by_opp.items():
        w = sum(r["won"] for r in rs)
        agg.append((opp, rs[0]["opp_rank"], w, len(rs) - w))

    def li(lst):
        return "".join(f"<li>{esc(o)}{f' <small>#{rk}</small>' if rk else ''} <b>{w}:{l}</b></li>" for o, rk, w, l in lst)
    fav = sorted((a for a in agg if a[2] > a[3]), key=lambda a: (-(a[2] - a[3]), -a[2], a[1] or 999))[:3]
    fear = sorted((a for a in agg if a[2] < a[3]), key=lambda a: (a[2] - a[3], -a[3], a[1] or 999))[:3]
    ff = ""
    if fav or fear:
        ff = ("<div class='ff'>"
              f"<div><h4>Lieblingsgegner</h4><ul>{li(fav) or '<li>–</li>'}</ul></div>"
              f"<div><h4>Angstgegner</h4><ul>{li(fear) or '<li>–</li>'}</ul></div></div>")
    # alle Einzel
    body = ""
    for opp, rs in sorted(by_opp.items(), key=lambda kv: (kv[1][0]["opp_rank"] or 999, kv[0])):
        w = sum(r["won"] for r in rs)
        sets = ", ".join(f'<span class="{"win" if r["won"] else "loss"}">{r["sets"]}</span>' for r in rs)
        body += (f"<tr><td class='num'>{rs[0]['opp_rank'] or '–'}</td><td>{esc(opp)}</td><td>{esc(rs[0]['opp_team'])}</td>"
                 f"<td class='num'>{w}:{len(rs) - w}</td><td>{sets}</td></tr>")
    table = ("<h4>Alle Einzel</h4><div class='scroll'><table><thead><tr><th>Rang</th><th>Gegner</th><th>Team</th><th>Bilanz</th>"
             f"<th>Sätze</th></tr></thead><tbody>{body}</tbody></table></div>")
    nav = (f'<div class="nav"><button class="rb nb-prev" data-go="p{idx - 1}"{"" if idx > 0 else " disabled"}>‹ Vorheriger</button>'
           f'<button class="rb nb-next" data-go="p{idx + 1}"{"" if idx < total - 1 else " disabled"}>Nächster ›</button></div>')
    return (f'<dialog id="p{idx}" aria-label="Spielerprofil {esc(name)}"><div class="dlg">'
            f'<button class="x" data-close aria-label="Schliessen">✕</button>'
            f'<div class="head">{pic}<div><p class="sub">Spielerprofil</p><h3 class="vs">{esc(name)}</h3>'
            f'<p class="sub">{p["n"]} Einzel · Rang {p["rank"] or "–"}</p></div></div>'
            f'<dl class="kpi rk">{kp}</dl>{form}{rv}{rcells}{ff}{table}{nav}</div></dialog>')


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
