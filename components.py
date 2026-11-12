"""Wiederverwendbare HTML-Bausteine: Form-Punkte, Kurven, Report- und Team-Fenster."""
import json
from collections import defaultdict

from datetime import datetime

from awards import player_awards
from config import FORM_N, TEAM, find_photo, slug
from stats import quote_series
from textutil import dkey, einzel_punkte, esc, fmt_date, pct, ranglistenwert, short


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


def player_dialog(idx, p, total, hist, titles=None, dom_id=None, prev_id=None, next_id=None, team=None, back=None, pid=None):
    """Spielerprofil als Fenster: Bild, Kennzahlen, Form, Rangverlauf, Runden, Lieblings-/Angstgegner, alle Einzel."""
    name = p["name"]
    team = team or TEAM
    dom_id = dom_id or f"p{idx}"
    if dom_id.startswith("p") and dom_id[1:].isdigit():     # eigenes Team: blättern in der Rangliste
        prev_id = f"p{idx - 1}" if idx > 0 else None
        next_id = f"p{idx + 1}" if idx < total - 1 else None
    pic = avatar(name)
    rows = p["rows"]
    quote = pct(p["w"], p["l"])
    avg = f"{p['avg_opp']:.1f}" if p["avg_opp"] else "–"
    pk = einzel_punkte(rows)
    kp = (f"<div><dt>Rang</dt><dd>{p['rank'] or '–'}</dd></div><div><dt>Bilanz</dt><dd>{p['w']}:{p['l']}</dd></div>"
          f"<div><dt>Punkte</dt><dd>{pk}</dd></div><div><dt>Ranglistenwert</dt><dd>{ranglistenwert(pk, len(rows)):.1f}</dd></div>"
          f"<div><dt>Quote</dt><dd>{quote}</dd></div><div><dt>Ø Gegner</dt><dd>{avg}</dd></div>")
    # Form und Quotenverlauf
    key = f"{(p.get('team') or '').lower()}|{name}"
    calc = (f"<details class='calc' data-n='{len(rows)}' data-p='{pk}' data-key='{esc(key)}'><summary>Ranglistenwert-Rechner</summary>"
            "<p class='hint'>Was passiert, wenn noch weitere Einzel dazukommen? Die anderen Spieler bleiben dabei unverändert.</p><div class='cg'>"
            + "".join(f"<label><span>{lab}</span><input type='number' inputmode='numeric' min='0' max='40' value='0' data-pt='{v}'></label>"
                      for lab, v in (("2:0 gewonnen (4 Punkte)", 4), ("2:1 gewonnen (3 Punkte)", 3),
                                     ("1:2 verloren (1 Punkt)", 1), ("0:2 verloren (0 Punkte)", 0)))
            + "</div><p class='cr' aria-live='polite'></p></details>")
    form = (f"<h4>Form</h4><p class='prow'>{dots(rows, 10)} {spark(quote_series(rows), 'Siegquote nach jedem Einzel', 0, 100)}</p>"
            if rows else "")
    # Rangverlauf
    days = sorted(hist)
    series = [hist[d][name] for d in days if name in hist[d]]
    rv = ""
    if len(series) >= 2:
        d = series[0] - series[-1]
        ch = f' <span class="{"up" if d > 0 else "down"}">{"▲" if d > 0 else "▼"} {abs(d)}</span>' if d else ""
        rv = (f"<h4>Rangverlauf</h4><p class='prow'>Rang {series[-1]}{ch} {spark(series, 'Rangverlauf', invert=True)}</p>")
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
    # Heim und Auswärts
    ha = {True: [0, 0], False: [0, 0]}
    for r in rows:
        if "home" in r:
            ha[r["home"]][0 if r["won"] else 1] += 1
    if any(sum(v) for v in ha.values()):
        cells = "".join(f"<div><dt>{lab}</dt><dd class='{'win' if v[0] > v[1] else 'loss' if v[0] < v[1] else ''}'>{v[0]}:{v[1]}</dd></div>"
                        for lab, v in (("Heim", ha[True]), ("Auswärts", ha[False])))
        rcells += f"<h4>Heim und Auswärts</h4><dl class='kpi rk'>{cells}</dl>"
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
    def olink(opp, oteam):
        d = (pid or {}).get((oteam.lower(), opp))
        return f"<button class='tl' data-open='{d}'>{esc(opp)}</button>" if d else esc(opp)

    body = ""
    for opp, rs in sorted(by_opp.items(), key=lambda kv: (kv[1][0]["opp_rank"] or 999, kv[0])):
        w = sum(r["won"] for r in rs)
        sets = ", ".join(f'<span class="{"win" if r["won"] else "loss"}">{r["sets"]}</span>' for r in rs)
        body += (f"<tr><td class='num'>{rs[0]['opp_rank'] or '–'}</td><td>{olink(opp, rs[0]['opp_team'])}</td><td>{esc(rs[0]['opp_team'])}</td>"
                 f"<td class='num'>{w}:{len(rs) - w}</td><td>{sets}</td></tr>")
    table = ("<h4>Alle Einzel</h4><div class='scroll'><table><thead><tr><th>Rang</th><th>Gegner</th><th>Team</th><th>Bilanz</th>"
             f"<th>Sätze</th></tr></thead><tbody>{body}</tbody></table></div>")
    aw = player_awards(p, titles or {})
    badges = ("<p class='badges'>" + "".join(f"<button type='button' class='badge{' pm' if n.startswith('Spieler des Monats') else ''}' data-tip='{esc(h)}'>{esc(n)}</button>" for n, h in aw) + "</p>") if aw else ""
    share = [f"{name} – Rang {p['rank'] or '–'} ({team})",
             f"Einzel {p['w']}:{p['l']} ({quote}) · Form " + " ".join("S" if r["won"] else "N" for r in rows[-5:])]
    if aw:
        share.append("Auszeichnungen: " + ", ".join(n for n, _ in aw))
    if fav:
        share.append("Lieblingsgegner: " + ", ".join(f"{o} {w}:{l}" for o, _, w, l in fav[:2]))
    if fear:
        share.append("Angstgegner: " + ", ".join(f"{o} {w}:{l}" for o, _, w, l in fear[:2]))
    copy = (f'<p class="acts"><button class="rb" data-copy="{esc(chr(10).join(share)).replace(chr(10), "&#10;")}">Zusammenfassung kopieren</button> <button class="rb" data-link>Link kopieren</button></p>')
    nav = (f'<div class="nav"><button class="rb nb-prev" data-go="{prev_id}"{"" if prev_id else " disabled"}>‹ Vorheriger</button>'
           f'<button class="rb nb-next" data-go="{next_id}"{"" if next_id else " disabled"}>Nächster ›</button></div>')
    if back:
        nav = f'<p><button class="rb" data-open="{back[0]}">‹ Team {esc(back[1])}</button></p>' + nav
    sid = "s-" + (slug(name) if team == TEAM else f"{slug(team)}-{slug(name)}")
    return (f'<dialog id="{dom_id}" data-s="{sid}" data-k="Spieler" data-n="{esc(name)}" data-sub="{esc(team)}" '
            f'aria-label="Spielerprofil {esc(name)}"><div class="dlg">'
            f'<button class="x" data-close aria-label="Schliessen">✕</button>'
            f'<div class="head">{pic}<div><p class="sub">Spielerprofil</p><h3 class="vs">{esc(name)}</h3>'
            f'<p class="sub">{(esc(team) + " · ") if team != TEAM else ""}{p["n"]} Einzel · Rang {p["rank"] or "–"}</p></div></div>'
            f'<dl class="kpi rk">{kp}</dl>{badges}{calc}{form}{rv}{rcells}{ff}{table}{copy}{nav}</div></dialog>')


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
    st = {}
    for pairs in m["rounds"].values():
        for p in pairs:
            for nm, tm_, w in ((p["mine"], m.get("team", TEAM), p["won"]), (p["opp"], m["opp"], not p["won"])):
                e = st.setdefault(nm, [0, 0, tm_])
                e[0 if w else 1] += 1
    best = sorted(st.items(), key=lambda kv: (-kv[1][0], kv[1][1]))
    mvp = [(n, f"{v[0]}:{v[1]}", v[2]) for n, v in best if best and (v[0], v[1]) == (best[0][1][0], best[0][1][1])][:2]
    img = json.dumps({"home": m.get("team", TEAM), "guest": m["opp"], "pts": m["points"], "games": m["games"],
                      "sets": m.get("sets", ""), "date": fmt_date(m["date"]), "mvp": mvp,
                      "mine": m.get("team", TEAM).lower() == TEAM.lower() or m["opp"].lower() == TEAM.lower()},
                     ensure_ascii=False)
    link = (f'<p class="hint"><a href="{esc(m["url"])}" target="_blank" rel="noopener">Originalreport auf vfc.ch</a></p>'
            if m.get("url") else "")
    return (f'<dialog id="{dom_id}" data-s="r{m["nr"]}" aria-label="Spielreport {esc(m["opp"])}"><div class="dlg">'
            f'<button class="x" data-close aria-label="Schliessen">✕</button>'
            f'<p class="sub">{fmt_date(m["date"])} · {"Heimspiel" if m["home"] else "Auswärtsspiel"}</p>'
            f'<h3 class="vs">{esc(m.get("team", TEAM))} <span class="sc {"win" if won_match else "loss"}">{m["points"]}</span> {esc(m["opp"])}</h3>'
            f'<p class="sub">{RESULT.get(pts, "")} · Spiele {m["games"]} · Sätze {m.get("sets", "–")}</p>'
            f'<div class="rounds">{cards}</div>{link}'
            f'<p class="acts"><button class="rb" data-copy="{esc(share_text(m)).replace(chr(10), "&#10;")}">Zusammenfassung kopieren</button> <button class="rb" data-link>Link kopieren</button> <button class="rb" data-img="{esc(img)}">Ergebnis als Bild</button></p>'
            + (f'<div class="nav"><button class="rb nb-prev" data-go="m{i - 1}"{"" if i > 0 else " disabled"}>‹ Vorherige Partie</button>'
               f'<button class="rb nb-next" data-go="m{i + 1}"{"" if i < total - 1 else " disabled"}>Nächste Partie ›</button></div>'
               if total else "") + '</div></dialog>')


def team_dialog(idx, t, data, id_of, pid=None):
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
    def plink(name):
        d = (pid or {}).get((tl, name))
        return f"<button class='tl' data-open='{d}'>{esc(name)}</button>" if d else esc(name)

    prow = "".join(
        f"<tr><td class='num'>{p['rank'] or '–'}</td><td>{plink(p['name'])}</td><td class='num'>{p['n']}</td>"
        f"<td class='num'>{p['w']}:{p['n'] - p['w']}</td><td class='num'>{pct(p['w'], p['n'] - p['w'])}</td>"
        f"<td>{dots(p['rows'])}</td></tr>" for p in pls)
    ti = (data.get("teaminfo") or {}).get(tl) or {}
    rows_i = []
    if ti.get("lokal"):
        rows_i.append(("Lokal", esc(ti["lokal"])))
    adr = ", ".join(x for x in (ti.get("strasse"), ti.get("ort")) if x)
    if adr:
        kl = f" · <a href='{esc(ti['karte'])}' target='_blank' rel='noopener'>Karte</a>" if ti.get("karte") else ""
        rows_i.append(("Adresse", esc(adr) + kl))
    if ti.get("captain"):
        rows_i.append(("Captain", esc(ti["captain"])))
    info_html = ("<dl class='info'>" + "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in rows_i) + "</dl>") if rows_i else ""
    return (f'<dialog id="t{idx}" data-s="v-{slug(t["team"])}" data-k="Verein" data-n="{esc(t["team"])}" data-sub="Platz {t["rank"]}" '
            f'aria-label="Team {esc(t["team"])}"><div class="dlg">'
            f'<button class="x" data-close aria-label="Schliessen">✕</button>'
            f'<p class="sub">Platz {t["rank"]} in der Tabelle</p><h3 class="vs">{esc(t["team"])}</h3>'
            f'<p class="sub">{t["pp"]}:{t["pm"]} Punkte · Spiele {t["gp"]}:{t["gm"]} · Sätze {t["sp"]}:{t["sm"]} · {t["played"]} Partien</p>{info_html}'
            f'<h4>Partien</h4><div class="scroll"><table class="cards"><thead><tr><th>Datum</th><th>Gegner</th><th>Ort</th><th>Punkte</th>'
            f'<th>Spiele</th><th></th></tr></thead><tbody>{mrows}</tbody></table></div>'
            f'<p class="acts"><button class="rb" data-link>Link kopieren</button></p>'
            f'<h4>Spieler</h4><div class="scroll"><table><thead><tr><th>Rang</th><th>Spieler</th><th>Spiele</th><th>Bilanz</th>'
            f'<th>Quote</th><th>Form (letzte {FORM_N})</th></tr></thead><tbody>{prow}</tbody></table></div>'
            f'</div></dialog>')
