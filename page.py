"""Setzt die ganze Seite zusammen (Reiter, Kennzahlen, Bereiche, Fenster)."""
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from components import RESULT, bar, match_dialog, player_dialog, team_dialog
from config import OUT, today, AUTHOR, GROUP, LOGO, MID, TEAM, TOP
from awards import MONTHS, monthly_titles
from textutil import dkey
from stats import bracket, order
from sections import player_table, section_fixtures, section_form, section_homeaway, section_homeaway_players, section_league, section_rounds, section_next, section_potm, section_rank_history
from textutil import esc, pct


CSS = (Path(__file__).with_name("style.css")).read_text(encoding="utf-8")
JS = (Path(__file__).with_name("app.js")).read_text(encoding="utf-8")


def render(data, hist):
    matches = data["matches"]
    players = sorted(data["players"], key=lambda p: (p["rank"] or 9999, p["name"]))   # Standard: nach Rang
    _n = datetime.now(ZoneInfo("Europe/Zurich"))
    now, now_iso = _n.strftime("%d.%m.%Y %H:%M"), _n.isoformat(timespec="minutes")
    mp = [tuple(int(x) for x in m["points"].split(":")) for m in matches]   # (eigene, gegnerische) Punkte
    wins = sum(p == (3, 0) for p in mp)
    sd_wins = sum(p == (2, 1) for p in mp)      # 9:9 nach regulären Spielen, Sudden Death gewonnen
    sd_losses = sum(p == (1, 2) for p in mp)    # Sudden Death verloren
    losses = sum(p == (0, 3) for p in mp)
    pts = sum(p[0] for p in mp)
    kpis = [("Partien", len(matches)), ("Siege", wins), ("Siege (Sudden Death)", sd_wins), ("Niederlagen", losses)]
    if sd_losses:
        kpis.append(("Niederlagen (Sudden Death)", sd_losses))
    kpis.append(("Punkte", pts))
    kpi_html = "".join(f"<div><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in kpis)
    logo = '<img class="logo" src="logo.svg" alt="Vereinslogo" width="96" height="96">' if LOGO else ""
    icon = '<link rel="icon" href="logo.svg" type="image/svg+xml">' if LOGO else ""
    W, L = sum(p["w"] for p in players), sum(p["l"] for p in players)
    allr = [r["opp_rank"] for p in players for r in p["rows"] if r["opp_rank"]]
    tb = {k: [sum(p["brackets"][k][i] for p in players) for i in (0, 1)] for k in ("top", "mid", "low")}

    def mon_key(d):
        x = dkey(d)
        return f"{x.year}-{x.month:02d}"

    months = sorted({mon_key(m["date"]) for m in matches}, reverse=True)
    mopts = "".join(f"<option value='{k}'>{MONTHS[int(k[5:]) - 1]} {k[:4]}</option>" for k in months)
    mrows = "".join(
        f"<tr class='click' data-open='m{i}' data-q='{esc(m['opp'].lower())}' data-mon='{mon_key(m['date'])}' "
        f"data-home='{int(m['home'])}' data-win='{int(m['points'].split(':')[0] > m['points'].split(':')[1])}'><td>{m['date'][:6]}</td><td>{esc(m['opp'])}</td><td>{'Heim' if m['home'] else 'Auswärts'}</td>"
        f"<td class='num'>{m['points']}</td><td class='num'>{m['games']}</td>"
        f"<td><button class='rb' data-open='m{i}'>Report</button></td></tr>" for i, m in enumerate(matches))
    id_of = {m["nr"]: f"m{i}" for i, m in enumerate(matches)}
    id_of.update({nr: f"o{nr}" for nr in data["others"]})
    titles = monthly_titles(players)
    # Spieler der ganzen Liga: eigene Spieler p0, p1, … (Blättern nach Rang), übrige lp<Team>_<n>
    for pl in players:
        pl["team"] = TEAM
    me = TEAM.lower()
    pid = {(me, pl["name"]): f"p{i}" for i, pl in enumerate(players)}
    others_pl = []          # (Teamindex, Team, [Spieler], [IDs])
    for ti, t in enumerate(data["league"]):
        tl = t["team"].lower()
        if tl == me:
            continue
        pls = []
        for name, rows in data["team_games"].get(tl, {}).items():
            rows = order([dict(r, opp_rank=data["ranks"].get(r["opp"])) for r in rows])
            w = sum(r["won"] for r in rows)
            known = [r["opp_rank"] for r in rows if r["opp_rank"]]
            br = {"top": [0, 0], "mid": [0, 0], "low": [0, 0]}
            for r in rows:
                bk = bracket(r["opp_rank"])
                if bk:
                    br[bk][0 if r["won"] else 1] += 1
            pls.append({"name": name, "team": t["team"], "rank": data["ranks"].get(name), "n": len(rows), "w": w,
                        "l": len(rows) - w, "avg_opp": sum(known) / len(known) if known else None, "brackets": br, "rows": rows})
        pls.sort(key=lambda x: (x["rank"] or 9999, x["name"]))
        ids = [f"lp{ti}_{k}" for k in range(len(pls))]
        for x, i_ in zip(pls, ids):
            pid[(tl, x["name"])] = i_
        others_pl.append((ti, t, pls, ids))
    dialogs = "".join(match_dialog(f"m{i}", m, data["ranks"], len(matches), i) for i, m in enumerate(matches))
    dialogs += "".join(match_dialog(f"o{nr}", m, data["ranks"]) for nr, m in data["others"].items())
    dialogs += "".join(player_dialog(i, pl, len(players), hist, titles, pid=pid) for i, pl in enumerate(players))
    for ti, t, pls, ids in others_pl:
        for k, x in enumerate(pls):
            dialogs += player_dialog(0, x, 0, hist, None, dom_id=ids[k], prev_id=ids[k - 1] if k else None,
                                     next_id=ids[k + 1] if k + 1 < len(ids) else None, team=t["team"],
                                     back=(f"t{ti}", t["team"]), pid=pid)
    dialogs += "".join(team_dialog(i, t, data, id_of, pid) for i, t in enumerate(data["league"]))

    archiv_link = ' · <a href="archiv/">Archiv früherer Saisons</a>' if (OUT / "archiv" / "index.html").exists() else ""
    fixtures_html = section_fixtures(data, id_of)
    ha_team, ha_players = section_homeaway(matches, players)
    next_html, open_html = section_next(data, matches, pid)
    league_html = section_league(data) + "</section>"
    open_html = f"<section>{open_html}</section>" if open_html else ""
    last_html = ""
    if matches:
        items = ""
        for i, m in reversed(list(enumerate(matches))[-3:]):
            pt = tuple(int(x) for x in m["points"].split(":"))
            items += (f"<li><button class='resrow' data-open='m{i}'><span class='rd'>{m['date'][:6]}</span>"
                      f"<span class='ro'>{esc(m['opp'])}<small>{RESULT.get(pt, '')} · {'Heim' if m['home'] else 'Auswärts'}</small></span>"
                      f"<b class='sc {'win' if pt[0] > pt[1] else 'loss'}'>{m['points']}</b></button></li>")
        last_html = (f"<section><h2>Letzte Ergebnisse</h2><ul class='res'>{items}</ul>"
                     "<p class='hint'><a href='#partien'>Alle Partien ansehen</a></p></section>")
    own_extra = f"{section_homeaway_players(players)}{section_form(players)}{section_rank_history(players, hist)}"
    team_blocks = f"<div class='tp' data-t='own'>{player_table(players, pid)}{own_extra}</div>"
    team_opts = f"<option value='own'>{esc(TEAM)}</option>"
    all_pl = list(players)
    for ti, t, pls, ids in others_pl:
        if not pls:
            continue
        all_pl += pls
        team_opts += f"<option value='t{ti}'>{esc(t['team'])}</option>"
        team_blocks += (f"<div class='tp' data-t='t{ti}' hidden>{player_table(pls, pid)}"
                        f"{section_homeaway_players(pls)}{section_form(pls)}{section_rank_history(pls, hist)}</div>")
    all_pl.sort(key=lambda x: (x["rank"] or 9999, x["name"]))
    team_opts += "<option value='all'>Alle Vereine</option>"
    team_blocks += f"<div class='tp' data-t='all' hidden>{player_table(all_pl, pid, True)}</div>"
    search_dlg = ('<dialog id="search" aria-label="Suche"><div class="dlg"><button class="x" data-close aria-label="Schliessen">✕</button>'
                  '<h3 class="vs">Suche</h3><input type="search" id="s-in" placeholder="Spieler oder Verein" aria-label="Suche" autocomplete="off">'
                  '<ul id="s-res" class="sres"></ul></div></dialog>')
    # Kopfkarten: nächstes Spiel mit Countdown, letztes Resultat, Teamform
    me_l = TEAM.lower()
    nxt = sorted((f for f in data["schedule"] if not f["played"] and me_l in (f["home"].lower(), f["guest"].lower())),
                 key=lambda f: dkey(f["date"]))
    hero = ""
    if nxt:
        f = nxt[0]
        home = f["home"].lower() == me_l
        opp = f["guest"] if home else f["home"]
        d = dkey(f["date"])
        days = (d.date() - today()).days
        stat = "heute" if days == 0 else "morgen" if days == 1 else f"in {days} Tagen" if days > 1 else f"seit {-days} Tagen offen"
        hero += (f"<div class='hc'><p class='sub'>Nächstes Spiel</p><b class='big cd' data-d='{d.strftime('%Y-%m-%d')}'>{stat}</b>"
                 f"<p>{esc(opp)}<small>{d.strftime('%d.%m.%Y')} · {'Heimspiel' if home else 'Auswärts'}"
                 f"{(' · ' + esc(f['place'])) if f.get('place') else ''}</small></p></div>")
    if matches:
        li = len(matches) - 1
        m = matches[li]
        pt = tuple(int(x) for x in m["points"].split(":"))
        hero += (f"<button class='hc hcb' data-open='m{li}'><span class='sub'>Letztes Resultat</span>"
                 f"<b class='big {'win' if pt[0] > pt[1] else 'loss'}'>{m['points']}</b>"
                 f"<span>{esc(m['opp'])}<small>{m['date'][:6]} · {RESULT.get(pt, '')}</small></span></button>")
        last5 = matches[-5:]
        dots_ = "".join(f"<span class='dot {'w' if int(x['points'].split(':')[0]) > int(x['points'].split(':')[1]) else 'l'}'>"
                        f"{'S' if int(x['points'].split(':')[0]) > int(x['points'].split(':')[1]) else 'N'}</span>" for x in last5)
        w5 = sum(int(x["points"].split(":")[0]) > int(x["points"].split(":")[1]) for x in last5)
        hero += (f"<div class='hc'><p class='sub'>Teamform</p><span class='dots'>{dots_}</span>"
                 f"<p>{w5} Siege aus {len(last5)} Partien<small>letzte {len(last5)} Partien, ältere links</small></p></div>")
    hero = f"<div class='hero'>{hero}</div>" if hero else ""
    tabs = "".join(f'<a href="#{k}">{n}</a>' for k, n in (("uebersicht", "Übersicht"), ("spieler", "Spieler"),
                                                          ("liga", "Team &amp; Liga"), ("partien", "Partien")))

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TEAM)} – Statistik {esc(GROUP)}</title>
{icon}
<link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icon-180.png">
<meta name="theme-color" content="#17100f"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="DTS Statistik">
<style>{CSS}</style><script>document.documentElement.className='js'</script></head><body><header class="top"><div class="brand wrap">{logo}<div><h1>{esc(TEAM)}</h1>
<p class="sub">Liga {esc(GROUP)} · Stand <time id="stand" datetime="{now_iso}">{now}</time> · Rangliste jeweils aktuell</p></div><button type="button" id="sbtn" class="sbtn" aria-label="Suche öffnen (Taste /)">Suche</button></div></header>
<div id="stale" class="stale" role="status" hidden></div>
<main>
<nav class="tabs" aria-label="Bereiche">{tabs}</nav>

<div class="panel" id="p-uebersicht">
{hero}
<dl class="kpi">{kpi_html}
<div><dt>Spielbilanz (Einzel)</dt><dd>{W}:{L}</dd></div>
</dl>
{next_html}
{last_html}
{section_potm(players, {pl["name"]: i for i, pl in enumerate(players)})}
{open_html}
</div>

<div class="panel" id="p-spieler">
<section><h2>Spieler</h2>
<form class="filter" role="search" onsubmit="return false">
<select id="f-team" aria-label="Verein">{team_opts}</select>
<input type="search" id="f-pq" placeholder="Spieler suchen" aria-label="Spieler suchen">
</form>
<p class="hint">Nur Einzel, ohne Doppel und Sudden Death. Spaltenköpfe anklicken zum Sortieren, auf einen Spieler klicken für das Profil. Ø Gegner-Rang: kleiner = stärkere Gegner.</p>
{team_blocks}
</section>
</div>

<div class="panel" id="p-liga">
{league_html}
{fixtures_html}
{ha_team}
{section_rounds(matches)}
</div>

<div class="panel" id="p-partien">
<section><h2>Partien</h2>
<p class="hint">Auf eine Partie klicken, um den Spielreport zu öffnen.</p>
<form class="filter" role="search" onsubmit="return false">
<input type="search" id="f-q" placeholder="Gegner suchen" aria-label="Gegner suchen">
<select id="f-mon" aria-label="Monat"><option value="">Alle Monate</option>{mopts}</select>
<select id="f-home" aria-label="Ort"><option value="">Heim und Auswärts</option><option value="1">Heim</option><option value="0">Auswärts</option></select>
<select id="f-win" aria-label="Ergebnis"><option value="">Alle Ergebnisse</option><option value="1">Siege</option><option value="0">Niederlagen</option></select>
</form>
<p class="hint" id="f-count" aria-live="polite"></p>
<div class="scroll"><table class="cards" id="mtable"><thead><tr><th>Datum</th><th>Gegner</th><th>Ort</th><th>Punkte</th><th>Spiele</th><th></th></tr></thead>
<tbody>{mrows}</tbody></table></div></section>

</div>
<footer>Quelle: vfc.ch · täglich automatisch aktualisiert · Made by {AUTHOR}{archiv_link}</footer>
</main>{dialogs}{search_dlg}<script>{JS}</script></body></html>"""
