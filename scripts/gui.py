"""Minecraft GUI pieces drawn in SVG: windows with notched corners, sunken
slots, tooltips, buttons and text with the game's offset drop shadow.

Panels come in two widths. FULL panels span the README; HALF panels are laid
out in pairs (two <img width="49%"> on one line), so each pair shares a height.
"""
from html import escape

from theme import MONO, SANS, esc, pixel_text, pixel_width  # noqa: F401  (re-exported)

W = 1200
HALF = 590

GUI = "#C6C6C6"        # the game's GUI grey
GUI_HI = "#FFFFFF"
GUI_LO = "#555555"
SLOT = "#8B8B8B"
SLOT_HI = "#FFFFFF"
SLOT_LO = "#373737"
LABEL = "#404040"      # GUI caption colour; the game draws it without a shadow
TIP_BG = "#100010"
TIP_HI = "#5000FF"
TIP_LO = "#28007F"
YELLOW = "#FFFF55"
GREEN = "#80FF20"
GOLD = "#FFAA00"
AQUA = "#55FFFF"
RED = "#FF5555"
GRAY = "#AAAAAA"
DARK = "#3F3F3F"

BASE_CSS = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(w, h, body, label="", css="", defs=""):
    lab = escape(label or "profile panel")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"'
            f' role="img" aria-label="{lab}"><title>{lab}</title>'
            + (f"<defs>{defs}</defs>" if defs else "")
            + f"<style>{css}{BASE_CSS}</style>{body}</svg>")


def rect(x, y, w, h, fill, op=None, extra=""):
    o = f' opacity="{op}"' if op is not None else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{o}{extra}/>'


def text(x, y, s, size=14, fill="#FFFFFF", anchor="start", weight=400, font=MONO, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" font-weight="{weight}"'
            f' fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def shadow_of(c):
    """The game's text shadow: the same colour at a quarter brightness."""
    c = c.lstrip("#")
    return "#%02X%02X%02X" % tuple(int(c[i:i + 2], 16) // 4 for i in (0, 2, 4))


def mc_text(x, y, s, size=14, fill="#FFFFFF", anchor="start", weight=400, font=MONO, extra=""):
    d = max(1.0, size / 9)
    return (text(x + d, y + d, s, size, shadow_of(fill), anchor, weight, font)
            + text(x, y, s, size, fill, anchor, weight, font, extra))


def mc_pixel(s, x, y, px, fill="#FFFFFF", shadow=True):
    return pixel_text(s, x, y, px, fill, shadow=shadow_of(fill) if shadow else None, shadow_op=1)


def label(x, y, s, size=15, fill=LABEL, anchor="start", weight=700):
    return text(x, y, s, size, fill, anchor, weight)


# ------------------------------------------------------------------------ frames
def window(x, y, w, h, b=4):
    """The game's GUI window: grey face, white/dark bevel, black outline with the
    corner pixels knocked out so it reads as rounded at a distance."""
    k = b / 2
    out = [
        f'<path d="M{x + 2 * k} {y}H{x + w - 2 * k}V{y + k}H{x + w - k}V{y + 2 * k}H{x + w}V{y + h - 2 * k}'
        f'H{x + w - k}V{y + h - k}H{x + w - 2 * k}V{y + h}H{x + 2 * k}V{y + h - k}H{x + k}V{y + h - 2 * k}'
        f'H{x}V{y + 2 * k}H{x + k}V{y + k}H{x + 2 * k}Z" fill="#000000"/>',
        rect(x + k, y + k, w - 2 * k, h - 2 * k, GUI),
        rect(x + k, y + k, w - 2 * k - b, b, GUI_HI), rect(x + k, y + k, b, h - 2 * k - b, GUI_HI),
        rect(x + 2 * k + b - k, y + h - k - b, w - 2 * k - b, b, GUI_LO),
        rect(x + w - k - b, y + 2 * k + b - k, b, h - 2 * k - b, GUI_LO),
    ]
    return "".join(out)


def card_frame(w, h):
    return window(2, 2, w - 4, h - 4)


def slot(x, y, s, fill=SLOT):
    return (rect(x, y, s, s, fill) + rect(x, y, s - 2, 2, SLOT_LO) + rect(x, y, 2, s - 2, SLOT_LO)
            + rect(x + 2, y + s - 2, s - 2, 2, SLOT_HI) + rect(x + s - 2, y + 2, 2, s - 2, SLOT_HI))


def inset(x, y, w, h, fill="#000000"):
    """A sunken area (map, chat, preview) inside a GUI window."""
    return (rect(x, y, w, h, fill) + rect(x, y, w, 2, SLOT_LO) + rect(x, y, 2, h, SLOT_LO)
            + rect(x, y + h - 2, w, 2, SLOT_HI) + rect(x + w - 2, y, 2, h, SLOT_HI))


def tooltip(x, y, w, h):
    """The purple-edged item tooltip."""
    return (rect(x + 2, y, w - 4, h, TIP_BG, .96) + rect(x, y + 2, w, h - 4, TIP_BG, .96)
            + rect(x + 2, y + 2, w - 4, 2, TIP_HI) + rect(x + 2, y + h - 4, w - 4, 2, TIP_LO)
            + f'<rect x="{x + 2}" y="{y + 4}" width="2" height="{h - 8}" fill="{TIP_HI}"/>'
            + f'<rect x="{x + w - 4}" y="{y + 4}" width="2" height="{h - 8}" fill="{TIP_LO}"/>')


def chip(cx, y, s, colour=YELLOW, size=13):
    w = len(s) * size * .61 + 20
    return tooltip(cx - w / 2, y - size - 8, w, size + 18) + mc_text(cx, y + 2, s, size, colour, "middle", 700)


def selector(x, y, s, colour="#FFFFFF"):
    d = (f"M{x - 4} {y - 4}h{s + 8}v{s + 8}h{-(s + 8)}Z"
         f"M{x} {y}v{s}h{s}v{-s}Z")
    return f'<path d="{d}" fill="{colour}" fill-rule="evenodd"/>'


def heart(x, y, k, full=True):
    rows = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    out = [f'<rect x="{x + c * k:.1f}" y="{y + r * k:.1f}" width="{k}" height="{k}"/>'
           for r, row in enumerate(rows) for c, v in enumerate(row) if v == "1"]
    body = "".join(out)
    outline = "".join(f'<rect x="{x + c * k - k * .5:.1f}" y="{y + r * k - k * .5:.1f}" width="{k * 2}"'
                      f' height="{k * 2}"/>' for r, row in enumerate(rows) for c, v in enumerate(row) if v == "1")
    if not full:
        return f'<g fill="#1A1A1A">{outline}</g><g fill="#3A3A3A">{body}</g>'
    return (f'<g fill="#1A1A1A">{outline}</g><g fill="#D81E1E">{body}</g>'
            f'<rect x="{x + k:.1f}" y="{y + k:.1f}" width="{k}" height="{k}" fill="#FFFFFF" opacity=".85"/>'
            f'<rect x="{x:.1f}" y="{y + 3 * k:.1f}" width="{k * 7}" height="{k * .9}" fill="#000000" opacity=".18"/>')


SPLASH_CSS = ("@keyframes splash{0%,100%{transform:scale(1)}50%{transform:scale(1.09)}}"
              ".splash{animation:splash .5s ease-in-out infinite alternate;transform-box:fill-box;"
              "transform-origin:center}")


def splash(x, y, s, size=18, rot=-20):
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot})"><g class="splash">'
            f'{mc_text(0, 0, s, size, YELLOW, "middle", 700)}</g></g>')
