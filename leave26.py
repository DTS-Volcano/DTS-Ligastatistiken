"""Dezenter Hinweis auf die eigene App Leave26 (Icon lokal, kein Google-Badge von fremden Servern)."""

URL = "https://play.google.com/store/apps/details?id=com.leave26.app&utm_source=dts-website&utm_medium=footer"
TEXT = "Darts-Zähler mit Caller, Bots und Checkout-Training – und Statistiken, die deinen Fortschritt zeigen. Kostenlos für Android."
PLAY = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><defs><linearGradient id="lp" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#00d4ff"/><stop offset=".45" stop-color="#34d27b"/><stop offset=".75" stop-color="#ffd54a"/>'
        '<stop offset="1" stop-color="#ff5a5f"/></linearGradient></defs><path d="M5 2.5v19a1 1 0 0 0 1.5.9l15-9.5a1 1 0 0 0 0-1.8L6.5 1.6A1 1 0 0 0 5 2.5z" fill="url(#lp)"/></svg>')


def leave26_card(compact=False):
    """compact=True: kleine Form für die Info-Seite."""
    btn = (f'<a class="l26-btn" href="{URL}" target="_blank" rel="noopener">{PLAY}'
           '<span><small>Jetzt bei</small><b>Google Play laden</b></span></a>')
    if compact:
        return (f'<div class="l26 small"><img src="leave26-icon.png" alt="" width="40" height="40" loading="lazy">'
                f'<div><p class="l26-k">Meine App</p><p class="l26-t"><b>Leave26</b> – Darts-Zähler für Android</p></div>'
                f'<a class="l26-btn" href="{URL}" target="_blank" rel="noopener">{PLAY}<span><b>Google Play</b></span></a></div>')
    return (f'<aside class="l26" aria-label="Meine App: Leave26"><img src="leave26-icon.png" alt="" width="64" height="64" loading="lazy">'
            f'<div><p class="l26-k">Meine App · von Kevin entwickelt</p><h3>Leave26</h3><p class="l26-t">{TEXT}</p>{btn}</div></aside>')
