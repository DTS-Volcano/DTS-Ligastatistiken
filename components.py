"""Wiederverwendbare HTML-Bausteine: Form-Punkte, Kurven, Report- und Team-Fenster."""
from collections import defaultdict

from config import FORM_N, TEAM
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
