"""Hand-made zine toolkit for the profile README (stdlib only).

Paper scraps, tape, stickers, ransom-note letters, doodles and pen marks,
all as plain SVG. Fonts + glyph metrics come from zine-fonts.json, written
once by build_cover.py.

Perf rules for animated <img> SVGs: no filters or masks, only a handful of
transform/opacity loops per page, and everything readable on frame one.
"""
import json
import math
import random
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent

PAPER, PAPER_W, KRAFT = "#f4efe4", "#fffdf7", "#dcc6a0"
INK, PENCIL, RULE = "#1b1b1b", "#6b655c", "#a9c8e6"
YELLOW, PINK, LILAC, MINT, RED, TAPE = "#ffd84d", "#ff9fc6", "#b9a8ff", "#8fe3bf", "#e5484d", "#f1e2a4"
PASTELS = [YELLOW, PINK, LILAC, MINT]

_fonts = json.loads((ROOT / "zine-fonts.json").read_text(encoding="utf-8"))
METRICS = _fonts["metrics"]
ICONS = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))

FONT_FACES = _fonts["css"]
CSS = """
.tw{font-family:Type,'Courier New',monospace}
.hand{font-family:Hand,'Comic Sans MS',cursive}
.blk{font-family:Block,Impact,sans-serif}
.wob{transform-box:fill-box;transform-origin:center;animation:wob 3.6s ease-in-out infinite}
@keyframes wob{0%,100%{transform:rotate(-2.5deg)}50%{transform:rotate(2.5deg) translateY(-2px)}}
.bob{animation:bob 1.8s ease-in-out infinite}
@keyframes bob{50%{transform:translateY(7px)}}
.spin{transform-box:fill-box;transform-origin:center;animation:spin 16s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.blink{animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.eyes{animation:eyes 4s steps(1) infinite}.eyes2{animation:eyes2 4s steps(1) infinite}
@keyframes eyes{0%,90%{opacity:1}92%,100%{opacity:0}}@keyframes eyes2{0%,90%{opacity:0}92%,100%{opacity:1}}
.pen{stroke-dasharray:100;animation:pen 6s ease-in-out infinite}
@keyframes pen{0%,62%{stroke-dashoffset:0}78%{stroke-dashoffset:-100}78.01%{stroke-dashoffset:100}100%{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def text_w(text, family, size):
    m = METRICS[family]
    return sum(m.get(ch, m[" "]) for ch in text) * size


def doc(w, h, label, body, extra_css="", seed=0, fonts=("Type", "Hand", "Block")):
    """Transparent canvas so torn paper edges sit on GitHub's own background.

    Only the font families a page uses get embedded.
    """
    faces = "".join(FONT_FACES[f] for f in fonts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{faces}{CSS}{extra_css}</style>'
            f'<defs>{grain(seed)}</defs>{body}</svg>')


def grain(seed):
    rng = random.Random(seed)
    specks = "".join(f'<circle cx="{rng.uniform(0, 131):.1f}" cy="{rng.uniform(0, 127):.1f}" r="{rng.uniform(.3, 1.1):.2f}"/>' for _ in range(70))
    fibers = []
    for _ in range(9):
        x, y = rng.uniform(0, 131), rng.uniform(0, 127)
        fibers.append(f'<path d="M{x:.1f},{y:.1f} q{rng.uniform(-6, 6):.1f},{rng.uniform(-3, 3):.1f} {rng.uniform(-14, 14):.1f},{rng.uniform(-4, 4):.1f}"/>')
    return (f'<pattern id="grain" width="131" height="127" patternUnits="userSpaceOnUse">'
            f'<g fill="{INK}" opacity=".07">{specks}</g><g stroke="{INK}" stroke-width=".6" fill="none" opacity=".06">{"".join(fibers)}</g></pattern>')


# ------------------------------------------------------------------ paper & tape
def _edge(x0, y0, x1, y1, step, amp, rng):
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) // step))
    nx, ny = -(y1 - y0), (x1 - x0)
    ln = math.hypot(nx, ny) or 1
    pts = []
    for i in range(n):
        t, j = i / n, rng.uniform(-amp, amp)
        pts.append((x0 + (x1 - x0) * t + nx / ln * j, y0 + (y1 - y0) * t + ny / ln * j))
    return pts


def paper(x, y, w, h, seed, color=PAPER, rot=0, torn=(True, False, True, False), shadow=True, extra=""):
    """Paper scrap; torn=(top, right, bottom, left) picks jagged edges. `extra` is drawn on the paper."""
    rng = random.Random(seed)
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    pts = []
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
        pts += _edge(ax, ay, bx, by, 13 if torn[i] else 60, 3.2 if torn[i] else .8, rng)
    poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    cx, cy = x + w / 2, y + h / 2
    sh = f'<polygon points="{poly}" fill="#000" opacity=".38" transform="translate(7,9)"/>' if shadow else ""
    return (f'<g transform="rotate({rot} {cx:.0f} {cy:.0f})">{sh}'
            f'<polygon points="{poly}" fill="{color}"/><polygon points="{poly}" fill="url(#grain)"/>{extra}</g>')


def tape(cx, cy, w, rot, color=TAPE):
    rng = random.Random(int(cx * 7 + cy))
    h = 34
    left = [(-w / 2 + rng.uniform(-3, 3), -h / 2 + i * h / 5) for i in range(6)]
    right = [(w / 2 + rng.uniform(-3, 3), h / 2 - i * h / 5) for i in range(6)]
    poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in left + right)
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot})">'
            f'<polygon points="{poly}" fill="{color}" opacity=".8"/>'
            f'<line x1="{-w / 2 + 6:.0f}" y1="-6" x2="{w / 2 - 6:.0f}" y2="-6" stroke="#fff" stroke-opacity=".35" stroke-width="3"/></g>')


# ------------------------------------------------------------------ stickers
def _anim(cls, delay):
    style = f' style="animation-delay:{delay:.1f}s"' if delay else ""
    return f'class="{cls}"{style}'


def sticker(cx, cy, w, h, color, rot=0, rx=16, content="", cls="", delay=0):
    """Thick ink outline + hard offset shadow, centred on (cx, cy)."""
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot})"><g {_anim(cls, delay)}>'
            f'<rect x="{-w / 2 + 5:.0f}" y="{-h / 2 + 6:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx:.0f}" fill="{INK}"/>'
            f'<rect x="{-w / 2:.0f}" y="{-h / 2:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx:.0f}" fill="{color}" stroke="{INK}" stroke-width="3"/>'
            f'{content}</g></g>')


def label_sticker(cx, cy, text, color, rot=0, size=20, cls="", delay=0, pad=24):
    w = text_w(text, "Block", size) + pad * 2
    h = size * 2.3
    fg = PAPER_W if color == INK else INK
    body = f'<text x="0" y="{size * .36:.1f}" text-anchor="middle" class="blk" font-size="{size}" fill="{fg}">{escape(text)}</text>'
    return sticker(cx, cy, w, h, color, rot, rx=h / 2, content=body, cls=cls, delay=delay)


def circle_sticker(cx, cy, r, color, lines, rot=0, size=20, cls="", delay=0):
    fg = PAPER_W if color == INK else INK
    lh = size * 1.05
    top = -lh * (len(lines) - 1) / 2 + size * .36
    txt = "".join(f'<text x="0" y="{top + i * lh:.1f}" text-anchor="middle" class="blk" font-size="{size}" fill="{fg}">{escape(t)}</text>'
                  for i, t in enumerate(lines))
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot})"><g {_anim(cls, delay)}>'
            f'<circle cx="5" cy="6" r="{r}" fill="{INK}"/><circle r="{r}" fill="{color}" stroke="{INK}" stroke-width="3"/>{txt}</g></g>')


def starburst(cx, cy, r_out, r_in, points, color, content="", rot=0, cls=""):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi * i / points
        pts.append(f"{r * math.cos(a):.1f},{r * math.sin(a):.1f}")
    poly = " ".join(pts)
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot})"><g class="{cls}">'
            f'<polygon points="{poly}" fill="{INK}" transform="translate(6,7)"/>'
            f'<polygon points="{poly}" fill="{color}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>{content}</g></g>')


def ransom(text, x, y, size, seed, palette=None):
    """Cut-out letters: each glyph on its own scrap with its own font and tilt. Returns (svg, width)."""
    rng = random.Random(seed)
    palette = palette or [INK, PAPER_W, YELLOW, PAPER_W, PINK, INK, LILAC, PAPER_W, MINT]
    out, cx = [], x
    for i, ch in enumerate(text):
        if ch == " ":
            cx += size * .42
            continue
        fam = rng.choice(["Block", "Block", "Type", "Hand"])
        fs = size * {"Block": .78, "Type": .9, "Hand": 1.08}[fam]
        bg = palette[(i + rng.randrange(len(palette))) % len(palette)]
        fg = PAPER_W if bg == INK else INK
        bw, bh = text_w(ch, fam, fs) + size * .34, size * 1.08
        rot, dy = rng.uniform(-8, 8), rng.uniform(-6, 6)
        cls = {"Block": "blk", "Type": "tw", "Hand": "hand"}[fam]
        out.append(
            f'<g transform="translate({cx + bw / 2:.1f},{y + dy:.1f}) rotate({rot:.1f})">'
            f'<rect x="{-bw / 2 + 3:.1f}" y="{-bh / 2 + 4:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="#000" opacity=".3"/>'
            f'<rect x="{-bw / 2:.1f}" y="{-bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{bg}"{"" if bg == INK else f' stroke="{INK}" stroke-width="1.5"'}/>'
            f'<text x="0" y="{fs * .36:.1f}" text-anchor="middle" class="{cls}" font-size="{fs:.1f}" fill="{fg}">{escape(ch)}</text></g>')
        cx += bw + size * .06
    return "".join(out), cx - x


# ------------------------------------------------------------------ doodles
def arrow(x0, y0, x1, y1, bend=40, color=INK, width=3, cls=""):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1
    qx, qy = mx - dy / ln * bend, my + dx / ln * bend
    ang = math.atan2(y1 - qy, x1 - qx)
    h = 16
    a1 = (x1 - h * math.cos(ang - .45), y1 - h * math.sin(ang - .45))
    a2 = (x1 - h * math.cos(ang + .45), y1 - h * math.sin(ang + .45))
    return (f'<g class="{cls}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M{x0:.0f},{y0:.0f} Q{qx:.0f},{qy:.0f} {x1:.0f},{y1:.0f}"/>'
            f'<path d="M{a1[0]:.1f},{a1[1]:.1f} L{x1:.0f},{y1:.0f} L{a2[0]:.1f},{a2[1]:.1f}"/></g>')


def star(cx, cy, r, color=YELLOW, cls="spin", rot=0):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * .45
        a = -math.pi / 2 + math.pi * i / 5
        pts.append(f"{rr * math.cos(a):.1f},{rr * math.sin(a):.1f}")
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot})"><g class="{cls}">'
            f'<polygon points="{" ".join(pts)}" fill="{color}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/></g></g>')


def scribble_circle(cx, cy, rx, ry, seed, color=RED, width=3.2, cls="pen"):
    rng = random.Random(seed)
    pts = []
    for i in range(41):
        a = -2.2 + i / 40 * math.pi * 2 * 1.18
        j = rng.uniform(.94, 1.06)
        pts.append((cx + rx * j * math.cos(a), cy + ry * j * math.sin(a)))
    d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    return f'<path d="{d}" pathLength="100" class="{cls}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def squiggle(x, y, w, color=RED, width=3, cls="pen"):
    d = f"M{x:.0f},{y:.0f}" + "".join(f" q{w / 16:.1f},{-7 if i % 2 else 7} {w / 8:.1f},0" for i in range(8))
    return f'<path d="{d}" pathLength="100" class="{cls}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'


def highlight(x, y, w, h=26, color=YELLOW, rot=-1.2):
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h}" fill="{color}" opacity=".8" transform="rotate({rot} {x:.0f} {y:.0f})" rx="3"/>'


def stamp(cx, cy, r, top, big, rot=-12, color=RED, cls=""):
    pid = f"stamp{int(cx)}x{int(cy)}"
    rr = r - 22
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot})" opacity=".9"><g class="{cls}">'
            f'<path id="{pid}" d="M{-rr},0 a{rr},{rr} 0 1,1 {2 * rr},0 a{rr},{rr} 0 1,1 {-2 * rr},0" fill="none"/>'
            f'<circle r="{r}" fill="none" stroke="{color}" stroke-width="4"/><circle r="{r - 9}" fill="none" stroke="{color}" stroke-width="1.6"/>'
            f'<text class="tw" font-size="13" letter-spacing="2.5" fill="{color}"><textPath href="#{pid}" xlink:href="#{pid}">{escape(top)}</textPath></text>'
            f'<text y="{r * .2:.0f}" text-anchor="middle" class="blk" font-size="{r * .58:.0f}" fill="{color}">{escape(big)}</text></g></g>')


def typed_cat(x, y, size=18, color=INK, accent=PINK):
    lh = size * 1.1
    return (f'<g transform="translate({x:.0f},{y:.0f})" class="tw" font-size="{size}" style="white-space:pre">'
            f'<text fill="{color}"> /\\_/\\</text>'
            f'<text y="{lh:.0f}" fill="{color}" class="eyes">( o.o )</text>'
            f'<text y="{lh:.0f}" fill="{color}" class="eyes2">( -.- )</text>'
            f'<text y="{lh * 2:.0f}" fill="{accent}"> &gt; ^ &lt;</text></g>')


def icon(slug, x, y, size, color=INK):
    return f'<path transform="translate({x:.1f},{y:.1f}) scale({size / 24:.3f})" d="{ICONS[slug]}" fill="{color}"/>'
