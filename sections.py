"""Die Bereiche der Seite (nächstes Spiel, Tabelle, Form, Rangverlauf)."""
from collections import defaultdict
from datetime import datetime, timedelta

from components import avatar, bar, dots, spark
from config import FORM_N, MID, TEAM, TOP, today
from stats import quote_series
from textutil import dkey, esc, fmt_date, pct, short


def section_next(data, matches, pid=None):
    me = TEAM.lower()
    fx = sorted((f for f in data["schedule"] if not f["played"] and me in (f["home"].lower(), f["guest"].lower())),
                key=lambda f: (dkey(f["date"]), f["nr"]))
    if not fx:
        return "", ""
    league = {t["team"].lower(): t for t in data["league"]}
    nxt = fx[0]
    home = nxt["home"].lower() == me
    opp = nxt["guest"] if home else nxt["home"]
    ol = opp.lower()
    overdue = dkey(nxt["date"]).date() < today()
    t = league.get(ol)
    meta = [f"{fmt_date(nxt['date'])}{' (Termin offen / nachzuholen)' if overdue else ''}",
            "Heimspiel" if home else "Auswärtsspiel"]
    if nxt["place"]:
        meta.append(esc(nxt["place"]))
    lines = [" · ".join(meta)]
    if t:
        lines.append(f"{esc(opp)} steht auf Platz {t['rank']} mit {t['pp']} Punkten aus {t['played']} Partien "
                     f"(Spiele {t['gp']}:{t['gm']}).")
    earlier = [m for m in matches if m["opp"].lower() == ol]
    if earlier:
        lines.append("Bisher gegen sie: " + ", ".join(
            f"{m['points']} ({m['date'][:6]}, {'Heim' if m['home'] else 'Auswärts'}, Spiele {m['games']})" for m in earlier) + ".")
    else:
        lines.append("Gegen dieses Team habt ihr in dieser Saison noch nicht gespielt.")

    tidx = next((k for k, x in enumerate(data["league"]) if x["team"].lower() == ol), None)

    # Gegner-Kader
    vs_us = defaultdict(list)     # Gegner -> [(unser Spieler, Sätze aus unserer Sicht, gewonnen)]
    for p in data["players"]:
        for r in p["rows"]:
            if r["opp_team"].lower() == ol:
                vs_us[r["opp"]].append((p["name"], r["sets"], r["won"]))
    roster = []
    for name, rows in data["team_games"].get(ol, {}).items():
        w = sum(r["won"] for r in rows)
        roster.append({"name": name, "rank": data["ranks"].get(name), "n": len(rows), "w": w, "rows": rows})
    roster.sort(key=lambda r: (r["rank"] or 999, -r["n"]))
    if roster:
        cards = ""

        def plink(name):
            d = (pid or {}).get((ol, name))
            return f"<button class='tl' data-open='{d}'>{esc(name)}</button>" if d else esc(name)

        for r in roster:
            enc = vs_us.get(r["name"], [])
            chips = "".join(
                f"<span class='chip {'win' if won else 'loss'}'>{esc(short(n))} <b>{esc(sets)}</b></span>"
                for n, sets, won in enc)
            meet = (f"<p class='meet'><small>Gegen euch:</small> {chips}</p>" if chips
                    else "<p class='meet'><small>Noch nicht gegen euch gespielt</small></p>")
            cards += (f"<li class='pc'><span class='rk'>{r['rank'] or '–'}</span>"
                      f"<div class='pn'><b>{plink(r['name'])}</b><small>{r['w']}:{r['n'] - r['w']} · {pct(r['w'], r['n'] - r['w'])}</small></div>"
                      f"<span class='pf'>{dots(r['rows'])}</span>{meet}</li>")
        table = ("<h3>Kader des Gegners</h3><p class='hint'>Rang in der Einzelrangliste, Bilanz und Form (S/N). "
                 "«Gegen euch» zeigt das Satzergebnis aus eurer Sicht, grün = ihr habt gewonnen.</p>"
                 f"<ul class='pcs'>{cards}</ul>")
    else:
        table = "<p class='hint'>Von diesem Team sind noch keine Einzel bekannt.</p>"

    nxt_html = (f"<section class='next'><h2>Nächstes Spiel: {esc(opp)}</h2>"
                + "".join(f"<p class='sub'>{l}</p>" for l in lines)
                + (f"<p><button class='rb' data-open='t{tidx}'>Team {esc(opp)} ansehen</button></p>" if tidx is not None else "")
                + table + "</section>")

    rows = ""
    for i, f in enumerate(fx):
        h = f["home"].lower() == me
        o = f["guest"] if h else f["home"]
        ot = league.get(o.lower())
        rows += (f"<tr{' class=hl' if i == 0 else ''}><td>{fmt_date(f['date'])}</td><td>{esc(o)}</td>"
                 f"<td class='num'>{ot['rank'] if ot else '–'}</td><td>{'Heim' if h else 'Auswärts'}</td>"
                 f"<td>{esc(f['place'])}</td></tr>")
    open_html = ("<h2>Ausstehende Spiele</h2><div class='scroll'><table class='cards up'><thead><tr><th>Datum</th><th>Gegner</th>"
                 f"<th>Platz</th><th>Ort</th><th>Spielort</th></tr></thead><tbody>{rows}</tbody></table></div>")
    return nxt_html, open_html


def section_league(data, hl=None):
    if not data["league"]:
        return ("<section><h2>Tabelle</h2><p class='hint'>Die Tabelle konnte von vfc.ch gerade nicht gelesen werden. "
                "Der nächste automatische Lauf versucht es erneut.</p>")
    me = (hl or TEAM).lower()
    rows = "".join(
        f"<tr class='click{' hl' if t['team'].lower() == me else ''}' data-open='t{i}'><td class='num'>{t['rank']}</td>"
        f"<td><button class='tl' data-open='t{i}'>{esc(t['team'])}</button></td>"
        f"<td class='num'>{t['played']}</td><td class='num'>{t['pp']}:{t['pm']}</td>"
        f"<td class='num'>{t['gp']}:{t['gm']}</td><td class='num'>{t['sp']}:{t['sm']}</td></tr>" for i, t in enumerate(data["league"]))
    return ("<section><h2>Tabelle</h2><p class='hint'>Auf ein Team klicken, um dessen Partien und Spieler zu sehen.</p><div class='scroll'><table><thead><tr><th>Platz</th><th>Team</th><th>Partien</th>"
            f"<th>Punkte</th><th>Spiele</th><th>Sätze</th></tr></thead><tbody>{rows}</tbody></table></div>")


def section_form(players):
    def score(p):
        last = p["rows"][-FORM_N:]
        return (-(sum(r["won"] for r in last) / len(last)), -len(last))
    body = ""
    for p in sorted(players, key=score):
        last = p["rows"][-FORM_N:]
        lw = sum(r["won"] for r in last)
        q_all = 100 * p["w"] / p["n"]
        q_last = 100 * lw / len(last)
        diff = q_last - q_all
        trend = "▲" if diff >= 10 else "▼" if diff <= -10 else "–"
        cls = "up" if trend == "▲" else "down" if trend == "▼" else ""
        body += (f"<tr><td>{esc(p['name'])}</td><td>{dots(p['rows'])}</td>"
                 f"<td class='num'>{lw}:{len(last) - lw}</td><td class='num'>{q_all:.0f} %</td>"
                 f"<td class='num {cls}'>{trend}</td>"
                 f"<td>{spark(quote_series(p['rows']), 'Verlauf der Siegquote von ' + p['name'], 0, 100)}</td></tr>")
    return ("<section><h2>Form</h2><p class='hint'>Letzte Einzel von links (älter) nach rechts (neuer). S = Sieg, N = Niederlage. "
            "Trend: ▲ letzte Einzel mindestens 10 Prozentpunkte besser als die Gesamtquote, ▼ mindestens 10 schlechter. "
            "Die Kurve zeigt die Siegquote nach jedem Einzel.</p><div class='scroll'><table class='sticky'><thead><tr><th>Spieler</th>"
            f"<th>Letzte {FORM_N}</th><th>Bilanz</th><th>Quote gesamt</th><th>Trend</th><th>Verlauf</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div></section>")


def section_rank_history(players, hist):
    days = sorted(hist)
    if not days:
        return ""
    t = today().isoformat()
    prior = [d for d in days if d < t]
    limit = (today() - timedelta(days=7)).isoformat()
    older = [d for d in prior if d <= limit]
    base = older[-1] if older else (prior[0] if prior else None)
    first = datetime.strptime(days[0], "%Y-%m-%d").strftime("%d.%m.%Y")
    body = ""
    for p in sorted(players, key=lambda p: (p["rank"] or 999, p["name"])):
        series = [hist[d][p["name"]] for d in days if p["name"] in hist[d]]
        cur = p["rank"]
        change = "–"
        if base and cur and p["name"] in hist[base]:
            d = hist[base][p["name"]] - cur
            change = f'<span class="up">▲ {d}</span>' if d > 0 else f'<span class="down">▼ {-d}</span>' if d < 0 else "0"
        body += (f"<tr><td>{esc(p['name'])}</td><td class='num'>{cur or '–'}</td><td class='num'>{change}</td>"
                 f"<td>{spark(series, 'Rangverlauf von ' + p['name'], invert=True)}</td></tr>")
    if base:
        since = datetime.strptime(base, "%Y-%m-%d").strftime("%d.%m.%Y")
        note = (f"Veränderung seit {since} (▲ besser, ▼ schlechter). Die Aufzeichnung läuft seit {first}. "
                "Die Kurve zeigt den Rang, oben ist Rang 1.")
    else:
        note = (f"Die Aufzeichnung hat am {first} begonnen. Veränderung und Verlauf erscheinen, "
                "sobald ein weiterer Tag gespeichert ist.")
    return (f"<section><h2>Rangverlauf</h2><p class='hint'>{note}</p><div class='scroll'><table class='sticky'><thead><tr><th>Spieler</th>"
            f"<th>Rang heute</th><th>Veränderung</th><th>Verlauf</th></tr></thead><tbody>{body}</tbody></table></div></section>")


def section_rounds(matches):
    """Einzel pro Spielblock (Runde 1–4): starten wir stark oder kommen wir später auf?"""
    tot = defaultdict(lambda: [0, 0])
    grid = []
    for m in matches:
        cells = {}
        for rnd, pairs in m["rounds"].items():
            if not rnd:
                continue
            w = sum(p["won"] for p in pairs)
            cells[rnd] = (w, len(pairs) - w)
            tot[rnd][0] += w
            tot[rnd][1] += len(pairs) - w
        if cells:
            grid.append((m, cells))
    rounds = sorted(tot)
    if not rounds:
        return ""
    cards = ""
    for r in rounds:
        w, l = tot[r]
        q = 100 * w / (w + l) if w + l else 0
        cards += (f"<div><dt>Runde {r}</dt><dd>{w}:{l}</dd>"
                  f"<span class='bar'><i style='width:{q:.0f}%'></i></span> {q:.0f} %</div>")
    verdict = ""
    if len(rounds) >= 4:
        half = len(rounds) // 2
        a = [tot[r] for r in rounds[:half]]
        b = [tot[r] for r in rounds[half:]]
        wa, la = sum(x[0] for x in a), sum(x[1] for x in a)
        wb, lb = sum(x[0] for x in b), sum(x[1] for x in b)
        if min(wa + la, wb + lb) >= 8:
            qa, qb = 100 * wa / (wa + la), 100 * wb / (wb + lb)
            d = qb - qa
            lab = f"Runden {rounds[0]}–{rounds[half - 1]} ({qa:.0f} %) gegen Runden {rounds[half]}–{rounds[-1]} ({qb:.0f} %)"
            if d <= -10:
                verdict = f"<p><b>Tendenz: starker Start, dann Nachlassen.</b> {lab}.</p>"
            elif d >= 10:
                verdict = f"<p><b>Tendenz: Steigerung im Verlauf der Partie.</b> {lab}.</p>"
            else:
                verdict = f"<p><b>Tendenz: gleichmässig über die Partie.</b> {lab}.</p>"
        else:
            verdict = "<p class='hint'>Für eine Tendenz sind noch zu wenige Einzel gespielt.</p>"
    head = "".join(f"<th class='num'>R{r}</th>" for r in rounds)
    rows = ""
    for m, cells in reversed(grid):
        tds = ""
        for r in rounds:
            if r in cells:
                w, l = cells[r]
                cls = "win" if w > l else "loss" if w < l else ""
                tds += f"<td class='num {cls}'>{w}:{l}</td>"
            else:
                tds += "<td class='num'>–</td>"
        rows += f"<tr><td>{m['date'][:6]} {esc(m['opp'])}</td>{tds}</tr>"
    return ("<section><h2>Spielblöcke</h2><p class='hint'>Einzel pro Runde (Runde 1 bis 4, je 4 Spiele), ohne Doppel "
            f"und Sudden Death.</p><dl class='kpi rk'>{cards}</dl>{verdict}"
            f"<div class='scroll'><table><thead><tr><th>Partie</th>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>")


from awards import MIN_EINZEL, MONTHS, potm_ranking


def section_potm(players, pidx):
    rk = potm_ranking(players)
    if not rk:
        t = today()
        return (f"<section><h2>Spieler des Monats</h2><p class='hint'>Noch niemand mit mindestens {MIN_EINZEL} Einzeln im "
                f"{MONTHS[t.month - 1]} {t.year}. Sobald jemand die Mindestzahl erreicht, erscheint hier der Zwischenstand.</p></section>")
    months = sorted(rk, reverse=True)
    cur = (today().year, today().month)
    k = months[0]
    live = k == cur
    top = rk[k][0]
    winners = [r for r in rk[k] if (r["q"], r["w"], round(r["avg"], 1)) == (top["q"], top["w"], round(top["avg"], 1))]
    label = f"{MONTHS[k[1] - 1]} {k[0]}"

    def link(name):
        return f"<button class='tl' data-open='p{pidx[name]}'>{esc(name)}</button>" if name in pidx else esc(name)

    cards = ""
    for w in winners:
        avg = f" · Ø Gegner-Rang {w['avg']:.0f}" if w["avg"] < 999 else ""
        cards += (f"<div class='potm'>{avatar(w['name'], 96)}<div><p class='sub'>{'Zwischenstand ' if live else ''}{label}</p>"
                  f"<h3 class='vs'>{link(w['name'])}</h3>"
                  f"<p class='sub'>{w['w']}:{w['l']} Einzel · {100 * w['q']:.0f} %{avg}</p></div></div>")
    hall = ""
    for m in months[1:]:
        t = rk[m][0]
        hall += (f"<li><span>{MONTHS[m[1] - 1]} {m[0]}</span>{link(t['name'])} <b>{t['w']}:{t['l']}</b></li>")
    hall = f"<h4>Frühere Monate</h4><ul class='hof'>{hall}</ul>" if hall else ""
    return (f"<section><h2>Spieler des Monats</h2>{cards}"
            f"<p class='hint'>Wertung: beste Siegquote im Einzel (mindestens {MIN_EINZEL} Einzel im Monat), dann mehr Siege, "
            f"dann die stärkeren Gegner. Doppel und Sudden Death zählen nicht.{' Der laufende Monat ist ein Zwischenstand.' if live else ''}</p>"
            f"{hall}</section>")


def section_homeaway(matches, players, own=True):
    """Gibt (Team-Teil, Spieler-Teil) zurück."""
    """Heim gegen Auswärts: Partien, Punkte und Einzel für das Team und pro Spieler."""
    if not matches:
        return "", ""
    team = {h: {"m": 0, "mw": 0, "pts": 0, "w": 0, "l": 0} for h in (True, False)}
    per = defaultdict(lambda: {True: [0, 0], False: [0, 0]})
    for m in matches:
        t = team[m["home"]]
        pts = tuple(int(x) for x in m["points"].split(":"))
        t["m"] += 1
        t["mw"] += pts[0] > pts[1]
        t["pts"] += pts[0]
        for pairs in m["rounds"].values():
            for p in pairs:
                t["w" if p["won"] else "l"] += 1
                per[p["mine"]][m["home"]][0 if p["won"] else 1] += 1

    def q(w, l):
        return f"{100 * w / (w + l):.0f} %" if w + l else "–"

    rows = ""
    for h, lab in ((True, "Heim"), (False, "Auswärts")):
        t = team[h]
        rows += (f"<tr><td>{lab}</td><td class='num'>{t['m']}</td><td class='num'>{t['mw']}:{t['m'] - t['mw']}</td>"
                 f"<td class='num'>{t['pts']}</td><td class='num'>{t['w']}:{t['l']}</td><td class='num'>{q(t['w'], t['l'])}</td></tr>")
    prow = ""
    for p in players:
        d = per.get(p["name"])
        if not d:
            continue
        (hw, hl), (aw, al) = d[True], d[False]
        prow += (f"<tr><td>{esc(p['name'])}</td><td class='num'>{hw}:{hl}</td><td class='num'>{aw}:{al}</td></tr>")
    team_html = (f"<section><h2>Heim und Auswärts</h2><p class='hint'>{'Unser Team' if own else 'Das Team'} daheim gegen auswärts. Einzel ohne Doppel und Sudden Death.</p>"
                 "<div class='scroll'><table><thead><tr><th></th><th class='num'>Partien</th><th class='num'>Siege:Niederl.</th>"
                 f"<th class='num'>Punkte</th><th class='num'>Einzel</th><th class='num'>Quote</th></tr></thead><tbody>{rows}</tbody></table></div></section>")
    player_html = ("<section><h2>Heim und Auswärts</h2><p class='hint'>Einzelbilanz pro Spieler (Siege:Niederlagen).</p>"
                   "<div class='scroll'><table class='sticky'><thead><tr><th>Spieler</th><th class='num'>Heim</th>"
                   f"<th class='num'>Auswärts</th></tr></thead><tbody>{prow}</tbody></table></div></section>")
    return team_html, player_html


def section_fixtures(data, id_of, team=None):
    """Alle Spiele der Liga: Ergebnisse (anklickbar, falls der Report vorliegt) und kommende Spiele."""
    sched = data["schedule"]
    if not sched:
        return ""
    me = (team or TEAM).lower()
    if team:
        sched = [f for f in sched if me in (f["home"].lower(), f["guest"].lower())]
    score = {}
    for m in data["matches"]:
        h, g = (TEAM, m["opp"]) if m["home"] else (m["opp"], TEAM)
        score[m["nr"]] = m["points"] if m["home"] else ":".join(reversed(m["points"].split(":")))
    for nr, m in data["others"].items():
        score[nr] = m["points"]

    def rows(items):
        out = ""
        for f in items:
            mine = not team and me in (f["home"].lower(), f["guest"].lower())
            sc = score.get(f["nr"], "")
            dom = id_of.get(f["nr"])
            attr = f" data-open='{dom}'" if dom and sc else ""
            out += (f"<tr class='{'click ' if attr else ''}{'hl' if mine else ''}'{attr}><td>{f['date'][:6]}</td>"
                    f"<td class='fxm'>{esc(f['home'])}<br>{esc(f['guest'])}</td>"
                    f"<td class='num'>{sc or '–'}</td></tr>")
        return out

    def table(items, head):
        return (f"<div class='scroll'><table class='fx'><thead><tr><th>Datum</th><th>Begegnung</th><th class='num'>{head}</th></tr></thead>"
                f"<tbody>{rows(items)}</tbody></table></div>")

    played = sorted((f for f in sched if f["played"]), key=lambda f: dkey(f["date"]), reverse=True)
    todo = sorted((f for f in sched if not f["played"]), key=lambda f: dkey(f["date"]))
    N = 10

    def block(items, head):
        if not items:
            return "<p class='hint'>Keine.</p>"
        html = table(items[:N], head)
        if len(items) > N:
            html += f"<details><summary>Weitere {len(items) - N} anzeigen</summary>{table(items[N:], head)}</details>"
        return html

    if team:
        return (f"<section><h2>Ergebnisse</h2><p class='hint'>Alle Partien von {esc(team)}, neueste zuerst. Auf eine Zeile klicken für den Report.</p>"
                f"{block(played, 'Punkte')}</section><section><h2>Kommende Spiele</h2>{block(todo, '')}</section>")
    return ("<section><h2>Ergebnisse der Liga</h2><p class='hint'>Alle Partien der Gruppe, neueste zuerst. "
            "Auf eine Zeile klicken für den Report, unsere Spiele sind hervorgehoben.</p>"
            f"{block(played, 'Punkte')}</section>"
            f"<section><h2>Kommende Spiele der Liga</h2>{block(todo, '')}</section>")


def player_table(pls, pid, all_view=False):
    """Spielertabelle (sortierbar). all_view: mit Spalte Verein, ohne Summenzeile."""
    body = ""
    for p in pls:
        b = p["brackets"]
        d = pid.get((p["team"].lower(), p["name"]))
        avg = f"{p['avg_opp']:.1f}" if p["avg_opp"] else "–"
        team_td = f"<td data-v='{esc(p['team'])}'>{esc(p['team'])}</td>" if all_view else ""
        body += (f"<tr class='click' data-open='{d}' data-q='{esc((p['name'] + ' ' + p['team']).lower())}'>"
                 f"<td data-v='{esc(p['name'])}'><button class='tl' data-open='{d}'>{esc(p['name'])}</button></td>{team_td}"
                 f"<td class='num' data-v='{p['rank'] or 9999}'>{p['rank'] or '–'}</td>"
                 f"<td class='num' data-v='{p['n']}'>{p['n']}</td>"
                 f"<td class='num' data-v='{p['w']}'>{p['w']}:{p['l']}</td>"
                 f"<td data-v='{p['w'] / p['n']:.3f}'>{bar(p['w'], p['l'])}<span class='q'>{pct(p['w'], p['l'])}</span></td>"
                 f"<td class='num' data-v='{p['avg_opp'] or 9999}'>{avg}</td>"
                 + "".join(f"<td class='num' data-v='{b[k][0] - b[k][1]}'>{b[k][0]}:{b[k][1]}</td>" for k in ("top", "mid", "low"))
                 + "</tr>")
    vcol = "<th>Verein</th>" if all_view else ""
    foot = ""
    if not all_view and pls:
        W, L = sum(p["w"] for p in pls), sum(p["l"] for p in pls)
        allr = [r["opp_rank"] for p in pls for r in p["rows"] if r["opp_rank"]]
        tb = {k: [sum(p["brackets"][k][i] for p in pls) for i in (0, 1)] for k in ("top", "mid", "low")}
        foot = (f"<tfoot><tr><td>Team</td><td></td><td class='num'>{W + L}</td><td class='num'>{W}:{L}</td><td>{pct(W, L)}</td>"
                f"<td class='num'>{(sum(allr) / len(allr)) if allr else 0:.1f}</td>"
                f"<td class='num'>{tb['top'][0]}:{tb['top'][1]}</td><td class='num'>{tb['mid'][0]}:{tb['mid'][1]}</td>"
                f"<td class='num'>{tb['low'][0]}:{tb['low'][1]}</td></tr></tfoot>")
    return (f"<div class='scroll'><table class='sortable sticky'><thead><tr><th>Spieler</th>{vcol}<th>Rang</th><th>Spiele</th><th>Bilanz</th>"
            f"<th>Quote</th><th>Ø Gegner</th><th>Rang 1–{TOP}</th><th>{TOP + 1}–{MID}</th><th>{MID + 1}+</th></tr></thead>"
            f"<tbody>{body}</tbody>{foot}</table></div>")


def section_homeaway_players(pls):
    """Heim und Auswärts pro Spieler (Einzelbilanz), für beliebige Spielerlisten mit Feld 'home' in den Einzeln."""
    body = ""
    for p in pls:
        h = [0, 0]
        a = [0, 0]
        for r in p["rows"]:
            if "home" not in r:
                continue
            (h if r["home"] else a)[0 if r["won"] else 1] += 1
        if h[0] + h[1] + a[0] + a[1]:
            body += (f"<tr><td>{esc(p['name'])}</td><td class='num'>{h[0]}:{h[1]}</td><td class='num'>{a[0]}:{a[1]}</td></tr>")
    if not body:
        return ""
    return ("<section><h2>Heim und Auswärts</h2><p class='hint'>Einzelbilanz pro Spieler (Siege:Niederlagen).</p>"
            "<div class='scroll'><table class='sticky'><thead><tr><th>Spieler</th><th class='num'>Heim</th>"
            f"<th class='num'>Auswärts</th></tr></thead><tbody>{body}</tbody></table></div></section>")
