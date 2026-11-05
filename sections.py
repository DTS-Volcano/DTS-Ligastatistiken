"""Die Bereiche der Seite (nächstes Spiel, Tabelle, Form, Rangverlauf)."""
from collections import defaultdict
from datetime import datetime, timedelta

from components import avatar, dots, spark
from config import FORM_N, TEAM, today
from stats import quote_series
from textutil import dkey, esc, fmt_date, pct, short


def section_next(data, matches):
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
        for r in roster:
            enc = vs_us.get(r["name"], [])
            chips = "".join(
                f"<span class='chip {'win' if won else 'loss'}'>{esc(short(n))} <b>{esc(sets)}</b></span>"
                for n, sets, won in enc)
            meet = (f"<p class='meet'><small>Gegen euch:</small> {chips}</p>" if chips
                    else "<p class='meet'><small>Noch nicht gegen euch gespielt</small></p>")
            cards += (f"<li class='pc'><span class='rk'>{r['rank'] or '–'}</span>"
                      f"<div class='pn'><b>{esc(r['name'])}</b><small>{r['w']}:{r['n'] - r['w']} · {pct(r['w'], r['n'] - r['w'])}</small></div>"
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


def section_league(data):
    if not data["league"]:
        return ("<section><h2>Tabelle</h2><p class='hint'>Die Tabelle konnte von vfc.ch gerade nicht gelesen werden. "
                "Der nächste automatische Lauf versucht es erneut.</p>")
    me = TEAM.lower()
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


MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
MIN_EINZEL = 5     # so viele Einzel braucht es im Monat, um zu zählen


def potm_ranking(players):
    """Monat (Jahr, Monat) -> Spieler nach Quote, Siegen und Stärke der Gegner sortiert."""
    mon = defaultdict(lambda: defaultdict(lambda: {"w": 0, "l": 0, "opp": []}))
    for p in players:
        for r in p["rows"]:
            d = dkey(r["date"])
            if d.year < 2000:
                continue
            e = mon[(d.year, d.month)][p["name"]]
            e["w" if r["won"] else "l"] += 1
            if r["opp_rank"]:
                e["opp"].append(r["opp_rank"])
    out = {}
    for k, pl in mon.items():
        rows = []
        for name, e in pl.items():
            n = e["w"] + e["l"]
            if n >= MIN_EINZEL:
                rows.append({"name": name, "w": e["w"], "l": e["l"], "q": e["w"] / n,
                             "avg": sum(e["opp"]) / len(e["opp"]) if e["opp"] else 999})
        rows.sort(key=lambda x: (-x["q"], -x["w"], x["avg"], x["name"]))
        if rows:
            out[k] = rows
    return out


def section_potm(players, pidx):
    rk = potm_ranking(players)
    if not rk:
        return ""
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
