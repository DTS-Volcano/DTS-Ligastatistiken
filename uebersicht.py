"""Übersicht: Kopfkarten, Kennzahlen, nächstes Spiel, letzte Ergebnisse – für jeden Verein und für die ganze Liga."""
from components import RESULT
from config import TEAM, today
from sections import section_next, section_potm
from textutil import dkey, esc, fmt_date

JUMP = (("spieler", "Spieler", "Tabelle, Form, Profile"), ("liga", "Team &amp; Liga", "Tabelle und Spielplan"),
        ("analyse", "Analyse", "Hall of Fame, Verlauf, Spielblöcke"), ("partien", "Partien", "Alle Reports"))


def jump_nav():
    return ("<nav class='jump' aria-label='Weitere Bereiche'>"
            + "".join(f"<a class='jt' href='#{k}'><b>{t}</b><span>{s}</span></a>" for k, t, s in JUMP) + "</nav>")


def _pts(m):
    return tuple(int(x) for x in m["points"].split(":"))


def _results(items, id_of, title, with_team=False):
    """items: [(Datum, Titel, Untertitel, Resultat, Gewonnen|None, Dialog-ID)]"""
    if not items:
        return ""
    rows = ""
    for d, t, sub, sc, win, dom, mn in items:
        cls = "" if win is None else (" win" if win else " loss")
        attr = f" data-open='{dom}'" if dom else ""
        tag = "button" if dom else "div"
        rows += (f"<li{' class=mn' if mn else ''}><{tag} class='resrow'{attr}><span class='rd'>{d}</span><span class='ro'>{t}<small>{sub}</small></span>"
                 f"<b class='sc{cls}'>{sc}</b></{tag}></li>")
    return f"<section><h2>{title}</h2><ul class='res'>{rows}</ul></section>"


def team_head(data, name, tm, players, pid, id_of):
    me = name.lower()
    # Kopfkarten
    nxt = sorted((f for f in data["schedule"] if not f["played"] and me in (f["home"].lower(), f["guest"].lower())),
                 key=lambda f: (dkey(f["date"]), f["nr"]))
    hero = ""
    if nxt:
        f = nxt[0]
        home = f["home"].lower() == me
        opp = f["guest"] if home else f["home"]
        d = dkey(f["date"])
        days = (d.date() - today()).days
        stat = "heute" if days == 0 else "morgen" if days == 1 else f"in {days} Tagen" if days > 1 else f"seit {-days} Tagen offen"
        hero += (f"<div class='hc'><p class='sub'>Nächstes Spiel</p><b class='big cd' data-d='{d.strftime('%Y-%m-%d')}'>{stat}</b>"
                 f"<p>{esc(opp)}<small>{d.strftime('%d.%m.%Y')} · {'Heimspiel' if home else 'Auswärts'}"
                 f"{(' · ' + esc(f['place'])) if f.get('place') else ''}</small></p></div>")
    if tm:
        m = tm[-1]
        pt = _pts(m)
        dom = id_of.get(m["nr"])
        tag, close = (f"button class='hc hcb' data-open='{dom}'", "button") if dom else ("div class='hc'", "div")
        hero += (f"<{tag}><span class='sub'>Letztes Resultat</span>"
                 f"<b class='big {'win' if pt[0] > pt[1] else 'loss'}'>{m['points']}</b>"
                 f"<span>{esc(m['opp'])}<small>{m['date'][:6]} · {RESULT.get(pt, '')}</small></span></{close}>")
        last5 = tm[-5:]
        wins5 = [_pts(x)[0] > _pts(x)[1] for x in last5]
        dots_ = "".join(f"<span class='dot {'w' if w else 'l'}'>{'S' if w else 'N'}</span>" for w in wins5)
        hero += (f"<div class='hc'><p class='sub'>Teamform</p><span class='dots'>{dots_}</span>"
                 f"<p>{sum(wins5)} Siege aus {len(last5)} Partien<small>letzte {len(last5)} Partien, ältere links</small></p></div>")
    hero = f"<div class='hero'>{hero}</div>" if hero else ""
    # Kennzahlen
    mp = [_pts(m) for m in tm]
    t = next((x for x in data["league"] if x["team"].lower() == me), None)
    kp = []
    if t:
        kp.append(("Platz", t["rank"]))
    kp += [("Partien", len(tm)), ("Siege", sum(p == (3, 0) for p in mp)),
           ("Siege (Sudden Death)", sum(p == (2, 1) for p in mp)), ("Niederlagen", sum(p == (0, 3) for p in mp))]
    if any(p == (1, 2) for p in mp):
        kp.append(("Niederlagen (Sudden Death)", sum(p == (1, 2) for p in mp)))
    kp.append(("Punkte", sum(p[0] for p in mp)))
    W, L = sum(p["w"] for p in players), sum(p["l"] for p in players)
    kpi = ("<dl class='kpi'>" + "".join(f"<div><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in kp)
           + f"<div><dt>Spielbilanz (Einzel)</dt><dd>{W}:{L}</dd></div></dl>")
    nxt_html, _ = section_next(data, tm, pid, name)
    return f"{hero}{kpi}{nxt_html}"


def home_block(data, id_of, pid, hof_players, tf, hof_fn):
    me = TEAM.lower()
    score = {nr: m["points"] for nr, m in data["others"].items()}
    for m in data["matches"]:
        score[m["nr"]] = m["points"] if m["home"] else ":".join(reversed(m["points"].split(":")))

    def mine(f):
        return me in (f["home"].lower(), f["guest"].lower())

    played = sorted((f for f in data["schedule"] if f["played"]), key=lambda f: dkey(f["date"]), reverse=True)[:5]
    res = [(f["date"][:6], f"{esc(f['home'])}<br>{esc(f['guest'])}", "", score.get(f["nr"], "–"), None,
            id_of.get(f["nr"]), mine(f)) for f in played]
    todo = sorted((f for f in data["schedule"] if not f["played"]), key=lambda f: dkey(f["date"]))[:5]
    nxt = [(f["date"][:6], f"{esc(f['home'])}<br>{esc(f['guest'])}", "", "", None, None, mine(f)) for f in todo]
    rows = ""
    for i, x in enumerate(data["league"]):
        rows += (f"<tr class='click{' hl' if x['team'].lower() == me else ''}' data-open='t{i}'><td class='num'>{x['rank']}</td>"
                 f"<td>{esc(x['team'])}</td><td class='num'>{x['pp']}:{x['pm']}</td></tr>")
    table = ("<section><h2>Tabelle</h2><div class='scroll'><table><thead><tr><th class='num'>Platz</th><th>Team</th>"
             f"<th class='num'>Punkte</th></tr></thead><tbody>{rows}</tbody></table></div>"
             "<p class='hint'><a href='#liga'>Team &amp; Liga: Details und Spielplan</a></p></section>") if rows else ""
    both = (f"<div class='two'>{_results(res, id_of, 'Letzte Ergebnisse')}{_results(nxt, id_of, 'Nächste Spiele')}</div>")
    return (f"{table}{both}{section_potm(hof_players, pid, True)}{hof_fn()}{jump_nav()}")
