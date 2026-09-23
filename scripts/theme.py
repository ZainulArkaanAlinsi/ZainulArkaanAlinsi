"""Shared design system for the profile assets.

Three visual languages, one grammar:

  liquid glass  translucent panels lit from behind by a blurred colour field
  computer UI   window chrome, monospace, corner ticks, status bars
  Minecraft     hard 2px bevels, voxel blocks, 5x7 pixel type with a drop shadow

Rules: five accents, flat fills only, no gradients. Every tint used anywhere is
derived from one of those five (or from the ink) by mixing toward the canvas, so
the palette never quietly grows.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# --------------------------------------------------------------------- palette
THEMES = {
    "dark": {
        "bg": "#0A0A0A", "line": "#262B33", "ink": "#E8EDF2", "muted": "#8A93A1",
        "blue": "#6E9BE8", "green": "#5BC98D", "amber": "#DFA94A", "red": "#DE6B7C", "violet": "#A88AE4",
        "glass": "#FFFFFF", "shadow": "#000000", "pane": "#FFFFFF", "pane_op": .045,
        "glass_rim": .10, "spec": .26, "glow": .12, "grid": .05, "px_shadow": .45,
        "ramp": (.45, 1.00),
    },
    "light": {
        "bg": "#FFFFFF", "line": "#D9DEE5", "ink": "#1B1F24", "muted": "#5A626E",
        "blue": "#3A6ED0", "green": "#1F9E63", "amber": "#B37D14", "red": "#C94357", "violet": "#7A52C7",
        "glass": "#FFFFFF", "shadow": "#1B1F24", "pane": "#1B1F24", "pane_op": .035,
        "glass_rim": .55, "spec": .95, "glow": .10, "grid": .06, "px_shadow": .16,
        "ramp": (.80, 1.55),
    },
}
ACCENTS = ("blue", "green", "amber", "red", "violet")

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


# ---------------------------------------------------------------- liquid glass
def glass(uid, x, y, w, h, t, r=16, glows=(), rim=True):
    """A frosted pane: blurred colour field clipped behind a translucent sheet.

    glows: (fx, fy, radius, colour) in 0..1 panel coordinates.
    """
    out = [f'<clipPath id="{uid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}"/></clipPath>']
    out.append(rect(x, y, w, h, fill=t["bg"], r=r))
    if glows:
        out.append(f'<g clip-path="url(#{uid})" filter="url(#blur)">')
        for fx, fy, fr, col in glows:
            out.append(f'<circle cx="{x + w * fx:.1f}" cy="{y + h * fy:.1f}" r="{fr:.1f}"'
                       f' fill="{t[col] if col in t else col}" opacity="{t["glow"]}"/>')
        out.append("</g>")
    out.append(rect(x, y, w, h, fill=t["pane"], r=r, op=t["pane_op"]))
    if rim:
        out.append(rect(x + .5, y + .5, w - 1, h - 1, r=r, stroke=t["glass"], op=t["glass_rim"]))
        out.append(rect(x + .5, y + .5, w - 1, h - 1, r=r, stroke=t["line"], op=.9))
        # specular sliver along the top edge
        out.append(f'<path d="M{x + r:.1f} {y + .8:.1f} H{x + w - r:.1f}" stroke="{t["glass"]}"'
                   f' stroke-width="1.2" opacity="{t["spec"]}" fill="none" stroke-linecap="round"/>')
    return "".join(out)


BLUR_DEF = '<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="62"/></filter>'


# ------------------------------------------------------------------ registration
def ticks(x, y, w, h, colour, size=9, sw=1.2, op=.55):
    """Corner registration marks — the hero's motif, carried down the page."""
    d = (f"M{x} {y + size}V{y}H{x + size} M{x + w - size} {y}H{x + w}V{y + size} "
         f"M{x + w} {y + h - size}V{y + h}H{x + w - size} M{x + size} {y + h}H{x}V{y + h - size}")
    return f'<path d="{d}" stroke="{colour}" stroke-width="{sw}" fill="none" opacity="{op}"/>'


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
def svg_doc(w, h, body, defs="", label="", css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"'
            f' role="img" aria-label="{escape(label or "profile panel")}">'
            f'<title>{escape(label or "profile panel")}</title>'
            f'<defs>{BLUR_DEF}{defs}</defs>'
            + (f"<style>{css}</style>" if css else "")
            + body + "</svg>")


# ---------------------------------------------------------------------- output
def write(name, dark_body, light_body=None):
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / f"{name}-dark.svg").write_text(dark_body, encoding="utf-8")
    if light_body is not None:
        (ASSETS / f"{name}-light.svg").write_text(light_body, encoding="utf-8")


def each_theme(fn):
    """Render fn(theme_name, tokens) once per colour scheme and write both files."""
    return {name: fn(name, tokens) for name, tokens in THEMES.items()}


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
