"""Setzt die ganze Seite zusammen (Reiter, Kennzahlen, Bereiche, Fenster)."""
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from components import RESULT, bar, match_dialog, player_dialog, team_dialog
from config import AUTHOR, GROUP, LOGO, MID, TEAM, TOP
from sections import section_form, section_homeaway, section_league, section_rounds, section_next, section_potm, section_rank_history
from textutil import esc, pct


CSS = (Path(__file__).with_name("style.css")).read_text(encoding="utf-8")
JS = (Path(__file__).with_name("app.js")).read_text(encoding="utf-8")


def render(data, hist):
    matches = data["matches"]
    players = sorted(data["players"], key=lambda p: (p["rank"] or 9999, p["name"]))   # Standard: nach Rang
    now = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%d.%m.%Y %H:%M")
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

    mrows = "".join(
        f"<tr class='click' data-open='m{i}'><td>{m['date'][:6]}</td><td>{esc(m['opp'])}</td><td>{'Heim' if m['home'] else 'Auswärts'}</td>"
        f"<td class='num'>{m['points']}</td><td class='num'>{m['games']}</td>"
        f"<td><button class='rb' data-open='m{i}'>Report</button></td></tr>" for i, m in enumerate(matches))
    id_of = {m["nr"]: f"m{i}" for i, m in enumerate(matches)}
    id_of.update({nr: f"o{nr}" for nr in data["others"]})
    dialogs = "".join(match_dialog(f"m{i}", m, data["ranks"], len(matches), i) for i, m in enumerate(matches))
    dialogs += "".join(match_dialog(f"o{nr}", m, data["ranks"]) for nr, m in data["others"].items())
    dialogs += "".join(player_dialog(i, pl, len(players), hist) for i, pl in enumerate(players))
    dialogs += "".join(team_dialog(i, t, data, id_of) for i, t in enumerate(data["league"]))

    prow = ""
    for pi, p in enumerate(players):
        b = p["brackets"]
        avg = f"{p['avg_opp']:.1f}" if p["avg_opp"] else "–"
        prow += (f"<tr class='click' data-open='p{pi}'><td data-v='{esc(p['name'])}'><button class='tl' data-open='p{pi}'>{esc(p['name'])}</button></td>"
                 f"<td class='num' data-v='{p['rank'] or 9999}'>{p['rank'] or '–'}</td>"
                 f"<td class='num' data-v='{p['n']}'>{p['n']}</td>"
                 f"<td class='num' data-v='{p['w']}'>{p['w']}:{p['l']}</td>"
                 f"<td data-v='{p['w'] / p['n']:.3f}'>{bar(p['w'], p['l'])}<span class='q'>{pct(p['w'], p['l'])}</span></td>"
                 f"<td class='num' data-v='{p['avg_opp'] or 9999}'>{avg}</td>"
                 + "".join(f"<td class='num' data-v='{b[k][0] - b[k][1]}'>{b[k][0]}:{b[k][1]}</td>" for k in ("top", "mid", "low"))
                 + "</tr>")

    ha_team, ha_players = section_homeaway(matches, players)
    next_html, open_html = section_next(data, matches)
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
<p class="sub">Liga {esc(GROUP)} · Stand {now} · Rangliste jeweils aktuell</p></div></div></header>
<main>
<nav class="tabs" aria-label="Bereiche">{tabs}</nav>

<div class="panel" id="p-uebersicht">
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
<p class="hint">Nur Einzel, ohne Doppel und Sudden Death. Spaltenköpfe anklicken zum Sortieren, auf einen Spieler klicken für das Profil. Ø Gegner-Rang: kleiner = stärkere Gegner.</p>
<div class="scroll"><table class="sortable sticky"><thead><tr><th>Spieler</th><th>Rang</th><th>Spiele</th><th>Bilanz</th>
<th>Quote</th><th>Ø Gegner</th><th>Rang 1–{TOP}</th><th>{TOP + 1}–{MID}</th><th>{MID + 1}+</th></tr></thead>
<tbody>{prow}</tbody>
<tfoot><tr><td>Team</td><td></td><td class="num">{W + L}</td><td class="num">{W}:{L}</td><td>{pct(W, L)}</td>
<td class="num">{(sum(allr) / len(allr)) if allr else 0:.1f}</td>
<td class="num">{tb['top'][0]}:{tb['top'][1]}</td><td class="num">{tb['mid'][0]}:{tb['mid'][1]}</td><td class="num">{tb['low'][0]}:{tb['low'][1]}</td></tr></tfoot>
</table></div></section>

{ha_players}

{section_form(players)}

{section_rank_history(players, hist)}

</div>

<div class="panel" id="p-liga">
{league_html}
{ha_team}
{section_rounds(matches)}
</div>

<div class="panel" id="p-partien">
<section><h2>Partien</h2>
<p class="hint">Auf eine Partie klicken, um den Spielreport zu öffnen.</p>
<div class="scroll"><table class="cards"><thead><tr><th>Datum</th><th>Gegner</th><th>Ort</th><th>Punkte</th><th>Spiele</th><th></th></tr></thead>
<tbody>{mrows}</tbody></table></div></section>

</div>
<footer>Quelle: vfc.ch · täglich automatisch aktualisiert · Made by {AUTHOR}</footer>
</main>{dialogs}<script>{JS}</script></body></html>"""
