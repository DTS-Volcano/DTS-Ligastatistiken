"""Kleine Hilfsfunktionen für Text, Datum und Zahlen."""
import html
import re
import unicodedata
from datetime import datetime, timedelta


_MOJI = re.compile("[ÃÂ][\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013\u2014"
                   "\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20ac\u2122]")


def _unmoji(m):
    for enc in ("latin-1", "cp1252"):
        try:
            return m.group().encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return m.group()


def fix(s):
    """Repariert doppelt kodierte Umlaute (z. B. 'MÃ¼ller' -> 'Müller', 'Ã\x84' -> 'Ä'), auch in gemischten Texten."""
    if "Ã" in s or "Â" in s:
        s = _MOJI.sub(_unmoji, s)
    return unicodedata.normalize("NFC", s)


def clean(s):
    return re.sub(r"\s+", " ", fix(s)).strip()


def pname(s):
    return re.sub(r"\s+Steeldart$", "", clean(s))


def dkey(d):
    for f in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(d, f)
        except (ValueError, TypeError):
            pass
    return datetime.min


def swap(score):
    a, b = score.split(":")
    return f"{b}:{a}"


esc = html.escape


def pct(w, l):
    return f"{100 * w / (w + l):.1f} %" if w + l else "–"


def short(name):
    parts = name.split()
    return f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else name


def fmt_date(d):
    """'02.12.26' oder '02.12.2026' -> '02.12.2026'."""
    dt = dkey(d)
    return dt.strftime("%d.%m.%Y") if dt != datetime.min else d
