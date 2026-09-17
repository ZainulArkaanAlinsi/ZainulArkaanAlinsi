"""Monochrome editorial assets for the GitHub profile README.

  hero.svg          ASCII portrait (B&W) + editorial name card, animated
  section-*.svg     numbered section headers
  footer.svg        closing ticker

Fonts are subset + embedded so the ASCII grid and typography render identically
everywhere GitHub shows the images. Motion is CSS/SMIL only (no JS in READMEs),
and every element is visible without animation support.
"""
import base64
import io
import random
import sys
from html import escape
from pathlib import Path

import numpy as np
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "cutout.png"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "out"
FONTS = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "fonts"
OUT.mkdir(parents=True, exist_ok=True)

BG, INK, MUTED, DIM, LINE = "#0a0a0a", "#fafafa", "#a3a3a3", "#525252", "#262626"
CHARSET = "".join(chr(c) for c in range(32, 127)) + "—·•×№°’“”"


# ---------------------------------------------------------------- fonts
def load_font(path, wght=None):
    font = TTFont(path)
    if wght is not None:
        font = instantiateVariableFont(font, {"wght": wght})
    return font


def _save(font):
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def embed(font, family):
    opts = Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga"]
    sub = Subsetter(opts)
    sub.populate(text=CHARSET)
    f = TTFont(io.BytesIO(_save(font)))
    sub.subset(f)
    f.flavor = "woff"
    data = base64.b64encode(_save(f)).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{data}) format('woff');}}"


def measure(font, text, size):
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(ch), cmap[32])][0] for ch in text) * size / upm


serif = load_font(FONTS / "InstrumentSerif-Regular.ttf")
serif_i = load_font(FONTS / "InstrumentSerif-Italic.ttf")
mono = load_font(FONTS / "JetBrainsMono[wght].ttf", wght=500)
MONO_ADV = mono["hmtx"]["zero"][0] / mono["head"].unitsPerEm  # 0.6em

mono_b = load_font(FONTS / "JetBrainsMono[wght].ttf", wght=800)
FONT_CSS = embed(serif, "Serif") + embed(serif_i, "SerifI") + embed(mono, "Mono")
BASE_CSS = f"""{FONT_CSS}
.m{{font-family:Mono,ui-monospace,Consolas,monospace}}
.s{{font-family:Serif,Georgia,serif}}
.si{{font-family:SerifI,Georgia,serif;font-style:italic}}
.cap{{font-family:Mono,ui-monospace,monospace;font-size:11px;letter-spacing:2.6px;fill:{MUTED}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""

# ---------------------------------------------------------------- ascii portrait
RAMP = " .:-=+*#%@"
A_FONT = 7.2
CELL_W, CELL_H = A_FONT * MONO_ADV, A_FONT
CARD_X, CARD_Y, CARD_W, CARD_H = 40, 40, 520, 590
COLS, ROWS = int(CARD_W // CELL_W), int(CARD_H // CELL_H)
GRID_W, GRID_H = COLS * CELL_W, ROWS * CELL_H
GX, GY = CARD_X + (CARD_W - GRID_W) / 2, CARD_Y + (CARD_H - GRID_H) / 2
GRAYS = ["#262626", "#4a4a4a", "#6b6b6b", "#8c8c8c", "#adadad", "#cccccc", "#e8e8e8", "#ffffff"]


def portrait_field():
    im = Image.open(SRC).convert("RGBA")
    # cover-fit on the face: sunglasses sit ~1/3 from the top of the frame
    aspect = GRID_W / GRID_H
    cw = int(im.width * 0.50)
    ch = int(cw / aspect)
    alpha_rows = np.where(np.asarray(im.getchannel("A")).max(axis=1) > 200)[0]
    top = max(0, int(alpha_rows[0]) - 26) if len(alpha_rows) else 0
    cx = im.width * 0.495
    im = im.crop((int(cx - cw / 2), top, int(cx + cw / 2), min(im.height, top + ch)))

    rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=1))
    mask = im.getchannel("A")
    gray = rgb.convert("L")
    solid = mask.point(lambda v: 255 if v > 128 else 0)
    vals = np.asarray(gray)[np.asarray(solid) > 0]
    lo, hi = np.percentile(vals, 2), np.percentile(vals, 99)
    gray = gray.point(lambda v: int(max(0, min(255, (v - lo) / (hi - lo) * 255))))
    size = (COLS, ROWS)
    lum = np.asarray(gray.resize(size, Image.LANCZOS), dtype=np.float32) / 255
    # local contrast (masked, CLAHE-like): pulls facial features out of darker skin tones
    m = (np.asarray(solid.resize(size, Image.LANCZOS), dtype=np.float32) / 255)
    def blur(arr, r):
        img = Image.fromarray((arr * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
        return np.asarray(img, dtype=np.float32) / 255
    mean = blur(lum * m, 6) / np.maximum(blur(m, 6), 1e-3)
    sq = blur(lum * lum * m, 6) / np.maximum(blur(m, 6), 1e-3)
    std = np.sqrt(np.maximum(sq - mean ** 2, 1e-4))
    local = np.clip(0.55 + (lum - mean) / (3.2 * std + 0.04), 0, 1)
    lum = local * 0.6 + lum * 0.4
    a = np.asarray(mask.resize(size, Image.LANCZOS), dtype=np.float32) / 255
    edge = np.asarray(gray.filter(ImageFilter.FIND_EDGES).resize(size, Image.LANCZOS), dtype=np.float32) / 255

    lum = np.clip(0.16 + lum * 0.9 + edge * 0.1, 0, 1) * a

    # atmosphere: faint dotted halo behind the head so the card reads as one solid block
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    halo = np.exp(-(((xx - COLS * 0.5) / (COLS * 0.55)) ** 2 + ((yy - ROWS * 0.32) / (ROWS * 0.5)) ** 2))
    bg = halo * 0.2 * (0.55 + rng.random((ROWS, COLS)) * 0.45)
    return np.where(a > 0.35, lum, np.maximum(lum, bg)), a


def ascii_image(field, alpha, scale=2):
    """Rasterise the glyph grid once (2x for retina).

    ~10k live <text> glyphs inside an animated <img> SVG get repainted every
    frame; a single bitmap keeps scrolling and the loops at 60fps.
    """
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype(io.BytesIO(_save(mono_b)), size=round(A_FONT * scale))
    cw, chh = CELL_W * scale, CELL_H * scale
    img = Image.new("L", (round(GRID_W * scale), round(GRID_H * scale)), 13)
    draw = ImageDraw.Draw(img)
    shades = [int(g[1:3], 16) for g in GRAYS]
    for y in range(ROWS):
        for x in range(COLS):
            v = float(field[y, x])
            ch = RAMP[min(len(RAMP) - 1, int(v * (len(RAMP) - 1)))]
            if ch == " ":
                continue
            level = 0 if alpha[y, x] <= 0.35 else max(1, min(len(GRAYS) - 1, int(v * len(GRAYS))))
            draw.text((x * cw, y * chh + chh * 0.78), ch, font=font, fill=shades[level], anchor="ls")
    img = img.quantize(colors=24, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- hero
def fit_size(font, text, max_w, start):
    size = start
    while measure(font, text, size) > max_w:
        size -= 1
    return size


def hero():
    W, H = 1200, 720
    field, alpha = portrait_field()
    png = ascii_image(field, alpha)
    ascii_svg = f'<image href="data:image/png;base64,{png}" x="{GX:.2f}" y="{GY:.2f}" width="{GRID_W:.2f}" height="{GRID_H:.2f}"/>'

    RX, RW = 620, 540
    s1 = fit_size(serif, "Zainul Arkaan", RW - 70, 104)
    name1_y, name2_y = 222, 222 + s1 * 0.95

    desc = [
        "Crafting efficient, thoughtful web and mobile",
        "experiences with Laravel, Next.js and Flutter —",
        "turning clean code into real-world impact.",
    ]
    desc_svg = "".join(
        f'<text x="{RX}" y="{428 + i * 30}" class="s" font-size="24" fill="{MUTED}">{escape(t)}</text>'
        for i, t in enumerate(desc)
    )

    cols = [("FOCUS", "Full-stack web"), ("MOBILE", "Flutter"), ("BASED IN", "Indonesia")]
    grid = "".join(
        f'<g class="">'
        f'<text x="{RX + i * 180}" y="552" class="cap">{k}</text>'
        f'<text x="{RX + i * 180}" y="586" class="s" font-size="27" fill="{INK}">{escape(v)}</text></g>'
        for i, (k, v) in enumerate(cols)
    )

    ring_text = "OPEN FOR COLLABORATION · 2026 · "
    ticker_items = ["PHP", "LARAVEL", "NEXT.JS", "TAILWIND CSS", "FLUTTER", "TYPESCRIPT", "REACT", "DART", "MYSQL", "FIREBASE"]
    ticker = "   ·   ".join(ticker_items) + "   ·   "
    tick_w = measure(mono, ticker, 12) + len(ticker) * 2.2  # includes letter-spacing
    tick_line = f'<text class="m" font-size="12" letter-spacing="2.2" fill="{MUTED}" style="white-space:pre">{escape(ticker * 3)}</text>'

    glitch_defs, glitch_use = [], []
    for i, (fy, hrows, cls) in enumerate([(0.30, 9, "g1"), (0.62, 7, "g2")]):
        y = GY + int(ROWS * fy) * CELL_H
        glitch_defs.append(f'<clipPath id="gc{i}"><rect x="{CARD_X}" y="{y:.1f}" width="{CARD_W}" height="{hrows * CELL_H:.1f}"/></clipPath>')
        glitch_use.append(
            f'<g clip-path="url(#gc{i})"><g class="{cls}"><rect x="{CARD_X - 40}" y="{y:.1f}" width="{CARD_W + 80}" height="{hrows * CELL_H:.1f}" fill="#0d0d0d"/>'
            f'<use href="#ascii"/></g></g>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Zainul Arkaan Alinsi — Full-Stack Developer">
<title>Zainul Arkaan Alinsi — Full-Stack Developer</title>
<style>{BASE_CSS}
.draw{{stroke-dasharray:120 400;animation:draw 5s cubic-bezier(.6,0,.3,1) infinite}}
@keyframes draw{{from{{stroke-dashoffset:520}}to{{stroke-dashoffset:0}}}}
.shine{{animation:shine 6s ease-in-out infinite}}
@keyframes shine{{0%,100%{{fill:#fafafa}}50%{{fill:#8a8a8a}}}}
.sweep{{animation:sweep 7s cubic-bezier(.45,0,.2,1) infinite}}
@keyframes sweep{{0%{{transform:translateY(-260px)}}60%,100%{{transform:translateY({CARD_H + 260}px)}}}}
.g1{{animation:gl 7s steps(1) 3s infinite}}.g2{{animation:gl 9s steps(1) 5.4s infinite}}
@keyframes gl{{0%,91%,100%{{transform:none}}92%{{transform:translateX(-22px)}}93.5%{{transform:translateX(14px)}}95%{{transform:translateX(-5px)}}96.5%{{transform:none}}}}
.spin{{transform-origin:1106px 70px;animation:spin 24s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.tick{{animation:tick 38s linear infinite}}
@keyframes tick{{to{{transform:translateX(-{tick_w:.1f}px)}}}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
@keyframes pulse{{50%{{opacity:.2}}}}
</style>
<defs>
  <g id="ascii">{ascii_svg}</g>
  <clipPath id="card"><rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}" rx="4"/></clipPath>
  <clipPath id="intro"><rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}"/></clipPath>
  <linearGradient id="band" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="vig" x1="0" y1="0" x2="0" y2="1">
    <stop offset=".72" stop-color="#0d0d0d" stop-opacity="0"/><stop offset="1" stop-color="#0d0d0d" stop-opacity=".96"/>
  </linearGradient>
  <clipPath id="n1"><rect x="{RX - 10}" y="{name1_y - s1}" width="{RW + 40}" height="{s1 * 1.12:.0f}"/></clipPath>
  <clipPath id="n2"><rect x="{RX - 10}" y="{name2_y - s1:.0f}" width="{RW + 40}" height="{s1 * 1.18:.0f}"/></clipPath>
  <clipPath id="tk"><rect x="0" y="{H - 52}" width="{W}" height="52"/></clipPath>
  <path id="ring" d="M1106,70 m-40,0 a40,40 0 1,1 80,0 a40,40 0 1,1 -80,0"/>
  {"".join(glitch_defs)}
</defs>

<rect width="{W}" height="{H}" fill="{BG}"/>

<!-- ============ portrait card ============ -->
<rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}" rx="4" fill="#0d0d0d" stroke="{LINE}"/>
<g clip-path="url(#card)">
  <g clip-path="url(#intro)">
    <use href="#ascii"/>
    {"".join(glitch_use)}
  </g>
  <rect class="sweep" x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="200" fill="url(#band)" opacity=".08"/>
  <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}" fill="url(#vig)"/>
  <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="1.5" fill="{INK}" opacity=".3" class="sweep line"/>
</g>
<g stroke="{INK}" stroke-width="1.2" fill="none">
  <path d="M{CARD_X - 12},{CARD_Y} h8 M{CARD_X},{CARD_Y - 12} v8"/>
  <path d="M{CARD_X + CARD_W + 12},{CARD_Y} h-8 M{CARD_X + CARD_W},{CARD_Y - 12} v8"/>
  <path d="M{CARD_X - 12},{CARD_Y + CARD_H} h8 M{CARD_X},{CARD_Y + CARD_H + 12} v-8"/>
  <path d="M{CARD_X + CARD_W + 12},{CARD_Y + CARD_H} h-8 M{CARD_X + CARD_W},{CARD_Y + CARD_H + 12} v-8"/>
</g>
<text x="{CARD_X + 18}" y="{CARD_Y + 28}" class="cap" fill="{INK}">FIG. 01</text>
<text x="{CARD_X + CARD_W - 18}" y="{CARD_Y + 28}" class="cap" text-anchor="end">ASCII · B/W · {COLS}×{ROWS}</text>
<g transform="translate({CARD_X + 18},{CARD_Y + CARD_H - 22})">
  <circle cx="4" cy="-4" r="3.5" fill="{INK}" class="pulse"/>
  <text x="16" y="0" class="cap" fill="{INK}">LIVE RENDER</text>
</g>
<text x="{CARD_X + CARD_W - 18}" y="{CARD_Y + CARD_H - 22}" class="cap" text-anchor="end">ZAINUL / 2026</text>

<!-- ============ editorial side ============ -->
<g >
  <text x="{RX}" y="66" class="cap" fill="{INK}">PORTFOLIO — VOL. 2026</text>
  <text x="{RX + 330}" y="66" class="cap">N° 001</text>
</g>
<line x1="{RX}" y1="88" x2="{RX + 400}" y2="88" stroke="{LINE}"/>
<line x1="{RX}" y1="88" x2="{RX + 400}" y2="88" stroke="{INK}" class="draw"/>

<g >
  <circle cx="1106" cy="70" r="52" fill="{BG}" stroke="{LINE}"/>
  <g class="spin"><text class="m" font-size="7.4" letter-spacing="1.25" fill="{MUTED}"><textPath href="#ring" xlink:href="#ring">{ring_text}</textPath></text></g>
  <text x="1106" y="80" text-anchor="middle" class="si" font-size="28" fill="{INK}">za</text>
</g>

<g clip-path="url(#n1)"><text x="{RX - 4}" y="{name1_y}" class="s" font-size="{s1}" fill="{INK}" letter-spacing="-1.5">Zainul Arkaan</text></g>
<g clip-path="url(#n2)"><text x="{RX - 2}" y="{name2_y:.0f}" class="si" font-size="{s1}" fill="{INK}" letter-spacing="-1">Alinsi<tspan fill="{DIM}" class="shine">.</tspan></text></g>

<g >
  <text x="{RX}" y="378" class="m" font-size="13" letter-spacing="3" fill="{INK}">FULL-STACK DEVELOPER</text>
  <text x="{RX + 262}" y="378" class="m" font-size="13" letter-spacing="3" fill="{DIM}">—  STUDENT @ IDN</text>
</g>
{desc_svg}
<line x1="{RX}" y1="522" x2="{RX + RW}" y2="522" stroke="{LINE}"/>
{grid}

<!-- ============ ticker ============ -->
<line x1="0" y1="{H - 52}" x2="{W}" y2="{H - 52}" stroke="{LINE}"/>
<g clip-path="url(#tk)"><g transform="translate(0,{H - 21})"><g class="tick">{tick_line}</g></g></g>
</svg>
'''
    (OUT / "hero.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- section headers
def section(slug, num, word, italic, label):
    W, H, size = 1200, 132, 60
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(word + ' ' + italic)}">
<style>{BASE_CSS}
.draw{{stroke-dasharray:180 {W};animation:draw 6s cubic-bezier(.6,0,.3,1) infinite}}
@keyframes draw{{from{{stroke-dashoffset:180}}to{{stroke-dashoffset:-{W}}}}}
.dot{{animation:run 6s cubic-bezier(.6,0,.3,1) infinite}}
@keyframes run{{50%{{transform:translateX({W - 8}px)}}}}
</style>
<rect width="{W}" height="{H}" fill="{BG}"/>
<text x="4" y="30" class="cap" fill="{INK}">{num}</text>
<text x="{W - 4}" y="30" class="cap" text-anchor="end">{escape(label)}</text>
<g>
  <text x="0" y="98" class="s" font-size="{size}" fill="{INK}" letter-spacing="-1" style="white-space:pre">{escape(word)}  <tspan class="si" fill="{MUTED}">{escape(italic)}</tspan></text>
</g>
<line x1="0" y1="{H - 10}" x2="{W}" y2="{H - 10}" stroke="{LINE}"/>
<line x1="0" y1="{H - 10}" x2="{W}" y2="{H - 10}" stroke="{INK}" stroke-opacity=".5" class="draw"/>
<circle cx="4" cy="{H - 10}" r="3.5" fill="{INK}" class="dot"/>
</svg>
'''
    (OUT / f"section-{slug}.svg").write_text(svg, encoding="utf-8")


def footer():
    W, H = 1200, 220
    line = "THANKS FOR SCROLLING   ·   LET'S BUILD SOMETHING   ·   "
    lw = measure(mono, line, 12) + len(line) * 2.2
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Thanks for visiting">
<style>{BASE_CSS}
.tick{{animation:tick 22s linear infinite}}
@keyframes tick{{to{{transform:translateX(-{lw:.1f}px)}}}}
.blink{{animation:b 1.1s steps(1) infinite}}@keyframes b{{50%{{opacity:0}}}}
</style>
<rect width="{W}" height="{H}" fill="{BG}"/>
<line x1="0" y1="1" x2="{W}" y2="1" stroke="{LINE}"/>
<text x="{W / 2}" y="104" text-anchor="middle" class="s" font-size="58" fill="{INK}" letter-spacing="-1">Thanks for <tspan class="si" fill="{MUTED}">visiting</tspan><tspan class="blink">_</tspan></text>
<text x="{W / 2}" y="142" text-anchor="middle" class="cap">© 2026 ZAINUL ARKAAN ALINSI — MADE IN INDONESIA</text>
<line x1="0" y1="{H - 44}" x2="{W}" y2="{H - 44}" stroke="{LINE}"/>
<g transform="translate(0,{H - 16})"><g class="tick"><text class="m" font-size="12" letter-spacing="2.2" fill="{DIM}" style="white-space:pre">{escape(line * 5)}</text></g></g>
</svg>
'''
    (OUT / "footer.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    hero()
    section("about", "01 / 04", "About", "me", "WHO I AM")
    section("stack", "02 / 04", "Tech", "stack", "TOOLS I BUILD WITH")
    section("activity", "03 / 04", "GitHub", "activity", "STATS · STREAK · LANGUAGES")
    section("snake", "04 / 04", "Contribution", "graph", "EVERY COMMIT COUNTS")
    footer()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name}: {p.stat().st_size / 1024:.1f} KB")
    print(f"grid {COLS}x{ROWS}")
