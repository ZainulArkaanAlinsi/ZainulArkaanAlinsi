"""Neo-brutalist building blocks: flat bright fills, thick black borders, hard
offset shadows, heavy type and tilted stickers. The Minecraft side of the page
(textured blocks, pixel type, hearts, XP) is layered on top of these.
"""
from html import escape

from theme import esc, pixel_text, pixel_width  # noqa: F401  (re-exported)

W, HALF = 1200, 590
CARD_H = 540

CREAM = "#FFF4E0"
INK = "#111111"
MUTED = "#4A4A4A"
WHITE = "#FFFFFF"
YELLOW = "#FFD23F"
PINK = "#FF7AB6"
BLUE = "#5AA9FF"
LIME = "#A3E635"
ORANGE = "#FF9F43"
PURPLE = "#B794F6"
RED = "#FF5A5F"
GRASS = "#5FA83A"

HEAVY = "'Arial Black','Archivo Black','Helvetica Neue',Helvetica,Arial,sans-serif"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

BW, SH = 3, 6          # border width, shadow offset

BASE_CSS = ("@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}"
            ".bob{animation:bob 2.4s ease-in-out infinite}"
            "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}.pulse{animation:pulse 1.2s steps(2) infinite}"
            "@keyframes wob{0%,100%{transform:rotate(0)}50%{transform:rotate(-3deg)}}"
            ".wob{animation:wob 3s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")


def svg(w, h, body, label="", css="", defs=""):
    lab = escape(label or "profile panel")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"'
            f' role="img" aria-label="{lab}"><title>{lab}</title>'
            + (f"<defs>{defs}</defs>" if defs else "")
            + f"<style>{BASE_CSS}{css}</style>{body}</svg>")


def rect(x, y, w, h, fill, op=None, extra=""):
    o = f' opacity="{op}"' if op is not None else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{o}{extra}/>'


def box(x, y, w, h, fill=CREAM, sh=SH, bw=BW, extra=""):
    """The brutalist card: a hard black shadow, a flat face, a thick outline."""
    return ((rect(x + sh, y + sh, w, h, INK) if sh else "")
            + f'<rect x="{x + bw / 2:.1f}" y="{y + bw / 2:.1f}" width="{w - bw:.1f}" height="{h - bw:.1f}"'
              f' fill="{fill}" stroke="{INK}" stroke-width="{bw}"{extra}/>')


def text(x, y, s, size=16, fill=INK, anchor="start", weight=400, font=SANS, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" font-weight="{weight}"'
            f' fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def heavy(x, y, s, size=40, fill=INK, anchor="start", extra=""):
    return text(x, y, s, size, fill, anchor, 900, HEAVY, extra + ' letter-spacing="-0.5"')


def heavy_w(s, size):
    """Rough advance of the heavy face, wide enough for the fallbacks."""
    return len(s) * size * .72


def mono(x, y, s, size=13, fill=INK, anchor="start", weight=700):
    return text(x, y, s, size, fill, anchor, weight, MONO)


def sticker(cx, cy, s, fill=YELLOW, rot=-6, size=15, fg=INK, cls=""):
    w = len(s) * size * .66 + 26
    h = size + 18
    c = f' class="{cls}"' if cls else ""
    return (f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot})"><g{c}>'
            + box(-w / 2, -h / 2, w, h, fill, sh=4)
            + text(0, size * .36, s, size, fg, "middle", 900, HEAVY)
            + "</g></g>")


def tab(x, y, s, fill=INK, fg=WHITE, px=3):
    """A section tab: a black slab with the title in Minecraft pixel type."""
    w = pixel_width(s, px) + 28
    h = 7 * px + 20
    return box(x, y, w, h, fill, sh=0) + pixel_text(s, x + 14, y + 10, px, fg), w, h


def card(w, h, fill=CREAM):
    """Full panel: card inset so its shadow stays inside the canvas."""
    return box(2, 2, w - SH - 4, h - SH - 4, fill)


def chip(x, y, s, fill, size=12):
    w = len(s) * size * .66 + 16
    return box(x, y, w, size + 12, fill, sh=2, bw=2) + text(x + w / 2, y + size + 3, s, size, INK, "middle", 900,
                                                             HEAVY), w
