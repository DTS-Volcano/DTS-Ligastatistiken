"""Setzt die ganze Seite zusammen (Reiter, Kennzahlen, Bereiche, Fenster)."""
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from components import RESULT, bar, match_dialog, player_dialog, team_dialog
from config import OUT, today, AUTHOR, GROUP, LOGO, MID, TEAM, TOP, VFC_LOGO
from hof import section_hof
from uebersicht import home_block, team_head
from verlauf import section_verlauf
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
    logo = f'<img class="logo" src="logo{LOGO.suffix.lower()}" alt="Vereinslogo" width="96" height="96">' if LOGO else ""
    vfc = (f'<a class="vfc" href="https://vfc.ch" target="_blank" rel="noopener"><img src="vfc-logo{VFC_LOGO.suffix.lower()}" '
           'alt="VFC Dartverband" height="40"></a>') if VFC_LOGO else ""
    icon = f'<link rel="icon" href="logo{LOGO.suffix.lower()}">' if LOGO else ""
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
    ha_team, ha_players = section_homeaway(matches, players)
    liga_opts, liga_blocks, ana_blocks = "", "", ""
    tf = data.get("team_full", {})
    order_t = [t["team"] for t in data["league"]] or [TEAM]
    order_t.sort(key=lambda n: (n.lower() != TEAM.lower(), n.lower()))
    hof_players = list(players) + [x for _, _, pls, _ in others_pl for x in pls]
    for ti, name in enumerate(order_t):
        own_t = name.lower() == TEAM.lower()
        tm = matches if own_t else tf.get(name.lower(), [])
        key = "own" if own_t else f"l{ti}"
        hid = "" if own_t else " hidden"
        liga_opts += f"<option value='{key}'>{esc(name)}</option>"
        liga_blocks += (f"<div class='lb' data-g='liga' data-t='{key}'{hid}>{team_head(data, name, tm, [x for x in hof_players if x['team'].lower() == name.lower()], pid, id_of)}"
                        f"{section_league(data, name)}</section>"
                        f"{section_fixtures(data, id_of, name)}</div>")
        ana_blocks += (f"<div class='lb' data-g='ana' data-t='{key}'{hid}>{section_hof(hof_players, tf, pid, id_of, name)}"
                       f"{section_potm(hof_players, pid, False, name)}{section_verlauf(data, name, tm)}"
                       f"{section_homeaway(tm, [], own_t)[0]}{section_rounds(tm)}</div>")
    liga_opts += "<option value='all'>Alle Vereine</option>"
    liga_blocks += (f"<div class='lb' data-g='liga' data-t='all' hidden>{section_league(data)}</section>"
                    f"{section_fixtures(data, id_of)}</div>")
    ana_blocks += (f"<div class='lb' data-g='ana' data-t='all' hidden>{section_hof(hof_players, tf, pid, id_of)}"
                   f"{section_potm(hof_players, pid)}"
                   "<section><h2>Team-Analyse</h2><p class='hint'>Für Saisonverlauf, Heim und Auswärts und Spielblöcke oben einen Verein wählen.</p></section></div>")
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
    home_html = home_block(data, id_of, pid, hof_players, tf, lambda: section_hof(hof_players, tf, pid, id_of, None, 4))
    tabs = "".join(f'<a href="#{k}">{n}</a>' for k, n in (("uebersicht", "Übersicht"), ("spieler", "Spieler"),
                                                          ("liga", "Team &amp; Liga"), ("analyse", "Analyse"), ("partien", "Partien")))

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TEAM)} – Statistik {esc(GROUP)}</title>
{icon}
<link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icon-180.png">
<meta name="theme-color" content="#17100f"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="DTS Statistik">
<style>{CSS}</style><script>document.documentElement.className='js'</script></head><body><header class="top"><div class="brand wrap">{logo}<div><h1>{esc(TEAM)}</h1>
<p class="sub">Liga {esc(GROUP)} · Stand <time id="stand" datetime="{now_iso}">{now}</time> · Rangliste jeweils aktuell</p></div>{vfc}<button type="button" id="sbtn" class="sbtn" aria-label="Suche öffnen (Taste /)">Suche</button></div></header>
<div id="stale" class="stale" role="status" hidden></div>
<main>
<nav class="tabs" aria-label="Bereiche">{tabs}</nav>

<div class="panel" id="p-uebersicht">
{home_html}
</div>

<div class="panel" id="p-spieler">
<section><h2>Spieler</h2>
<form class="filter" role="search" onsubmit="return false">
<select id="f-team" aria-label="Verein">{team_opts}</select>
<input type="search" id="f-pq" placeholder="Spieler suchen" aria-label="Spieler suchen">
</form>
<p class="hint">Es zählen nur Einzel (ohne Doppel und Sudden Death). Spaltenköpfe anklicken zum Sortieren, auf einen Spieler klicken für das Profil. Ø Gegner-Rang: kleiner = stärkere Gegner.</p>
{team_blocks}
</section>
</div>

<div class="panel" id="p-liga">
<section><h2>Team und Liga</h2>
<form class="filter" onsubmit="return false"><select class="vf" data-g="liga" aria-label="Verein">{liga_opts}</select></form></section>
{liga_blocks}
</div>

<div class="panel" id="p-analyse">
<section><h2>Analyse</h2>
<form class="filter" onsubmit="return false"><select class="vf" data-g="ana" aria-label="Verein">{liga_opts}</select></form>
<p class="hint">Alles auf dieser Seite gilt für den gewählten Verein.</p></section>
{ana_blocks}
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
