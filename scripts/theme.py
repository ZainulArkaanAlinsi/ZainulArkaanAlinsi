"""Pixel Terminal: the shared design system for every profile asset.

One grammar, three sources:

  terminal     monospace captions, prompts, status lines, hairline grids
  Minecraft    hard square bevels, inventory slots, hotbar, XP bar, 5x7 pixel type
  voxel world  isometric blocks under one light: top lit, left half shade, right dark

Rules: no rounded corners, no gradients, no blur. Every surface is a flat fill with a
1px black outline and a 3px bevel (light edge top-left, dark edge bottom-right).
Accents are a fixed set of six; every tint is mixed from them or from the ink, so
the palette never quietly grows. Outside the panels the canvas is transparent, so
GitHub's own page colour shows through and the panels read as windows on it.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# --------------------------------------------------------------------- palette
# bg = the panel surface everything is drawn on (and mixed toward).
THEMES = {
    "dark": {
        "bg": "#16181D", "hi": "#2E323B", "lo": "#07080A", "edge": "#000000",
        "slot": "#0D0E11", "slot_hi": "#262931", "slot_lo": "#030304",
        "line": "#2A2E36", "ink": "#EEF0F3", "muted": "#9AA2AE",
        "green": "#62D26F", "blue": "#5C9BFF", "gold": "#F2C14E", "red": "#E9566A",
        "violet": "#B48CFF", "diamond": "#4FE0D2", "amber": "#F2C14E",
        "xp": "#7CE04A", "splash": "#FFFF55",
        "shadow": "#000000", "px_shadow": .55, "grid": .06,
        "ramp": (.45, 1.00), "dark": True,
    },
    "light": {
        "bg": "#C6C6C6", "hi": "#FFFFFF", "lo": "#555555", "edge": "#000000",
        "slot": "#DCDCDC", "slot_hi": "#FFFFFF", "slot_lo": "#373737",
        "line": "#A4A4A4", "ink": "#262626", "muted": "#454545",
        "green": "#2C8A3A", "blue": "#2F5FC2", "gold": "#9A6A00", "red": "#B3263A",
        "violet": "#6B43B8", "diamond": "#137F76", "amber": "#9A6A00",
        "xp": "#3E9E1B", "splash": "#7A6A00",
        "shadow": "#3F3F3F", "px_shadow": .30, "grid": .10,
        "ramp": (.70, 1.45), "dark": False,
    },
}
ACCENTS = ("green", "blue", "gold", "red", "violet", "diamond")

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


# ----------------------------------------------------------------- colour math
def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def hexa(t):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in t)


def mix(a, b, t):
    """a blended t of the way toward b."""
    return hexa([x + (y - x) * t for x, y in zip(rgb(a), rgb(b))])


def shade(c, k):
    return hexa([v * k for v in rgb(c)])


def step(t, key, k):
    """k below 1 mixes the accent toward the canvas; above 1 pushes past it, away
    from the canvas. One hue either way, so the ladder stays sequential."""
    base, bg = t[key], t["bg"]
    if k <= 1:
        return mix(bg, base, k)
    away = "#FFFFFF" if sum(rgb(bg)) < 384 else "#000000"     # push away from the canvas
    return mix(base, away, (k - 1) * .55)


def ramp(t, key="green", steps=4):
    """Contribution ladder: one accent, monotone lightness, and a faint end that
    still clears 2:1 on the surface it sits on — checked, not eyeballed."""
    lo, hi = t["ramp"]
    return [mix(t["bg"], t["line"], .55)] + [
        step(t, key, lo + (hi - lo) * (i / (steps - 1))) for i in range(steps)]


# ------------------------------------------------------------------ primitives
def esc(s):
    return escape(str(s), quote=False)


def text(x, y, s, size=13, fill="#000", anchor="start", weight=400, font=MONO, extra="", ls=None):
    sp = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" font-weight="{weight}"'
            f' fill="{fill}" text-anchor="{anchor}"{sp}{extra}>{esc(s)}</text>')


def rect(x, y, w, h, fill="none", r=0, op=None, stroke=None, sw=1, extra=""):
    o = f' opacity="{op}"' if op is not None else ""
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    rr = f' rx="{r}"' if r else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{rr} fill="{fill}"{st}{o}{extra}/>'


def poly(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="{fill}"{extra}/>'


def line(x1, y1, x2, y2, stroke, sw=1, op=None, extra=""):
    o = f' opacity="{op}"' if op is not None else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
            f' stroke="{stroke}" stroke-width="{sw}"{o}{extra}/>')


# ------------------------------------------------------------- Minecraft GUI
def bevel(x, y, w, h, t, b=3, hi=None, lo=None):
    """The two L-shaped edges that make a flat rect read as raised (or, with hi
    and lo swapped, sunken)."""
    hi, lo = hi or t["hi"], lo or t["lo"]
    return (f'<path d="M{x} {y + h}V{y}H{x + w}v{b}H{x + b}V{y + h}Z" fill="{hi}"/>'
            f'<path d="M{x + w} {y}V{y + h}H{x}v{-b}H{x + w - b}V{y}Z" fill="{lo}"/>')


def panel(x, y, w, h, t, fill=None, b=3, outline=True):
    """A raised GUI window: black outline, bevel, flat face."""
    out = []
    if outline:
        out.append(rect(x - 2, y - 2, w + 4, h + 4, fill=t["edge"]))
    out.append(rect(x, y, w, h, fill=fill or t["bg"]))
    out.append(bevel(x, y, w, h, t, b))
    return "".join(out)


def slot(x, y, w, h, t, fill=None, b=2):
    """An inventory slot: sunken, darker than the panel."""
    return (rect(x, y, w, h, fill=fill or t["slot"])
            + bevel(x, y, w, h, t, b, hi=t["slot_lo"], lo=t["slot_hi"]))


def selector(x, y, s, colour="#FFFFFF", op=1.0, extra=""):
    """The hotbar selection frame: a 3px square ring sitting 3px outside a slot."""
    o = f' opacity="{op}"' if op < 1 else ""
    d = (f"M{x - 4} {y - 4}h{s + 8}v{s + 8}h{-(s + 8)}Z"
         f"M{x - 1} {y - 1}v{s + 2}h{s + 2}v{-(s + 2)}Z")
    return f'<path d="{d}" fill="{colour}" fill-rule="evenodd"{o}{extra}/>'


def titlebar(x, y, w, t, title, right="", accent="green"):
    """The window's top strip: three pixel lamps, a prompt-style path, a status."""
    out = [rect(x + 3, y + 3, w - 6, 26, fill=mix(t["bg"], t["lo"], .35))]
    for i, c in enumerate(("red", "gold", "green")):
        out.append(rect(x + 14 + i * 14, y + 12, 8, 8, fill=t[c]))
        out.append(rect(x + 14 + i * 14, y + 12, 8, 2, fill="#FFFFFF", op=.35))
    out.append(text(x + 66, y + 20.5, title, 11.5, t["muted"]))
    if right:
        out.append(text(x + w - 14, y + 20.5, right, 11.5, t["muted"], anchor="end"))
    out.append(rect(x + 3, y + 29, w - 6, 2, fill=t["lo"], op=.8))
    return "".join(out)


def window(x, y, w, h, t, title, right="", accent="green"):
    return panel(x, y, w, h, t) + titlebar(x, y, w, t, title, right, accent) + dither(x + 3, y + 31, w - 6, h - 34, t)


def dither(x, y, w, h, t, step=6):
    """A faint pixel grid on the panel face — the terminal's hairline grid, made
    of dots so it reads as texture rather than lines."""
    pid = f"dt{int(x)}{int(y)}{int(w)}"
    c = t["ink"]
    return (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse"'
            f' x="{x}" y="{y}"><rect width="1" height="1" fill="{c}"/></pattern>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})" opacity="{t["grid"] * .6:.3f}"/>')


def splash(x, y, s, t, size=15, rot=-18):
    """Minecraft's title-screen splash: yellow, tilted, gently pulsing."""
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot})">'
            f'<g class="splash">'
            f'{text(1.5, 1.5, s, size, mix(t["splash"], "#000000", .75), anchor="middle", weight=700)}'
            f'{text(0, 0, s, size, t["splash"], anchor="middle", weight=700)}'
            f'</g></g>')


SPLASH_CSS = ("@keyframes splash{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}"
              ".splash{animation:splash .9s ease-in-out infinite;transform-box:fill-box;transform-origin:center}")


def heart(x, y, k, fill, t, empty=False):
    """A 9x9 pixel heart at k px per pixel."""
    rows = ["011000110", "111101111", "111111111", "111111111", "011111110",
            "001111100", "000111000", "000010000"]
    out = []
    for ry, row in enumerate(rows):
        for rx, c in enumerate(row):
            if c == "1":
                out.append(f'<rect x="{x + rx * k:.1f}" y="{y + ry * k:.1f}" width="{k}" height="{k}"/>')
    body = "".join(out)
    if empty:
        return f'<g fill="{t["slot"]}">{body}</g>'
    hl = f'<rect x="{x + 2 * k:.1f}" y="{y + 1 * k:.1f}" width="{k}" height="{k}" fill="#FFFFFF" opacity=".7"/>'
    return f'<g fill="{fill}">{body}</g>' + hl


# ------------------------------------------------------------------ pixel type
FONT5 = {
    " ": "00000 00000 00000 00000 00000 00000 00000",
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01110",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00110 01000 10000 11111",
    "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 01100 01000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00110 00100 00000 00100",
    "'": "00100 00100 00000 00000 00000 00000 00000",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "*": "00000 10101 01110 11111 01110 10101 00000",
    "<": "00010 00100 01000 10000 01000 00100 00010",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "[": "01110 01000 01000 01000 01000 01000 01110",
    "]": "01110 00010 00010 00010 00010 00010 01110",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    "·": "00000 00000 00000 01100 01100 00000 00000",
}
_MISSING = "11111 10001 10001 10001 10001 10001 11111"


def pixel_text(s, x, y, px, colour, shadow=None, track=1, op=1.0, shadow_op=.45):
    """5x7 bitmap type drawn as squares, with Minecraft's offset drop shadow."""
    out, cx = [], x
    for ch in str(s).upper():
        rows = FONT5.get(ch, _MISSING).split()
        for ry, row in enumerate(rows):
            run = 0
            for rx in range(6):
                on = rx < 5 and row[rx] == "1"
                if on:
                    run += 1
                    continue
                if run:
                    bx, by, bw = cx + (rx - run) * px, y + ry * px, run * px
                    if shadow:
                        out.append(rect(bx + px, by + px, bw, px, fill=shadow, op=shadow_op))
                    out.append(rect(bx, by, bw, px, fill=colour))
                    run = 0
        cx += (5 + track) * px
    g = "".join(out)
    return f'<g opacity="{op}">{g}</g>' if op < 1 else g


def pixel_width(s, px, track=1):
    return max(0, len(str(s)) * (5 + track) * px - track * px)


# ------------------------------------------------------------ document scaffold
BASE_CSS = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg_doc(w, h, body, defs="", label="", css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"'
            f' role="img" aria-label="{escape(label or "profile panel")}">'
            f'<title>{escape(label or "profile panel")}</title>'
            + (f'<defs>{defs}</defs>' if defs else "")
            + f"<style>{css}{BASE_CSS}</style>"
            + body + "</svg>")


# ------------------------------------------------------------------ isometric
class Iso:
    """2:1 isometric camera. u runs down-right, v runs down-left, z runs up.

    Everything 3D on the page — the about scene, the stack blocks, the
    contribution world — goes through one of these, so the light is the same
    everywhere: top faces lit, the left (+v) face in half shade, the right (+u)
    face darkest.
    """
    LIT = (1.0, .74, .54)

    def __init__(self, ox, oy, unit):
        self.ox, self.oy, self.k = ox, oy, unit

    def p(self, u, v, z=0.0):
        return (self.ox + (u - v) * self.k, self.oy + (u + v) * self.k * .5 - z * self.k)

    def box(self, u, v, z, du, dv, dz, colour, seams=None, sides=None, top=None):
        """Top, left and right faces of an axis-aligned box, flat-shaded."""
        P = self.p
        tc, lc, rc = (top or colour), shade(sides or colour, self.LIT[1]), shade(sides or colour, self.LIT[2])
        out = [
            poly([P(u, v + dv, z), P(u + du, v + dv, z), P(u + du, v + dv, z + dz), P(u, v + dv, z + dz)], lc),
            poly([P(u + du, v, z), P(u + du, v + dv, z), P(u + du, v + dv, z + dz), P(u + du, v, z + dz)], rc),
            poly([P(u, v, z + dz), P(u + du, v, z + dz), P(u + du, v + dv, z + dz), P(u, v + dv, z + dz)], tc),
        ]
        if seams:
            out.append(poly([P(u, v, z + dz), P(u + du, v, z + dz), P(u + du, v + dv, z + dz), P(u, v + dv, z + dz)],
                            "none", f' stroke="{seams}" stroke-width=".8" stroke-opacity=".35" stroke-linejoin="round"'))
        return "".join(out)

    def face_matrix(self, face, u, v, z, du, dv, dz):
        """SVG matrix mapping a unit square (x right, y down) onto one face."""
        P = self.p
        if face == "top":          # x along +u, y along +v, origin at the far corner
            o, ex, ey = P(u, v, z + dz), P(u + du, v, z + dz), P(u, v + dv, z + dz)
        elif face == "left":       # the +v face, read left to right, top to bottom
            o, ex, ey = P(u, v + dv, z + dz), P(u + du, v + dv, z + dz), P(u, v + dv, z)
        else:                      # the +u face
            o, ex, ey = P(u + du, v + dv, z + dz), P(u + du, v, z + dz), P(u + du, v + dv, z)
        a, b = ex[0] - o[0], ex[1] - o[1]
        c, d = ey[0] - o[0], ey[1] - o[1]
        return f"matrix({a:.3f},{b:.3f},{c:.3f},{d:.3f},{o[0]:.2f},{o[1]:.2f})"
