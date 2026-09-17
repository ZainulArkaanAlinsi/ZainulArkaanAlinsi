"""Port of <AsciiEffect/> to a static-but-animated SVG for a GitHub profile README.

Pipeline mirrors the React component: sample -> luminance -> contrast -> brightness
-> threshold -> Floyd-Steinberg posterize -> char ramp -> gradient color.
Motion (flow wave, glitch bands, radial reveal, scanline) is baked in as CSS/SMIL.
"""
import sys
from html import escape

import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "cutout.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "hero.svg"

CHARS = " .:-=+*#%@"
COLS = 118
MAX_ROWS = 78        # keeps the portrait inside the 640px frame
CROP_BOTTOM = 0.70
CROP_SIDES = 0.09     # trims the outstretched hands so the face gets more cells
GAMMA = 0.85
CELL_W = 4.0
CELL_H = 6.6
FONT = 6.5
BRIGHTNESS = 1.15
CONTRAST = 1.15
THRESHOLD = 0.06
POSTERIZE = 32
DITHER = 0.8
# dim -> bright (flow palette extended with a deep indigo base)
COLORS = ["#3730a3", "#818cf8", "#67e8f9", "#e2e8f0"]
BG = "#07090d"


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def gradient(amount, steps=10):
    q = round(amount * (steps - 1)) / (steps - 1)
    pos = q * (len(COLORS) - 1)
    i = min(int(pos), len(COLORS) - 2)
    t = pos - i
    a, b = hex_rgb(COLORS[i]), hex_rgb(COLORS[i + 1])
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


# ---------- sample ----------
from PIL import ImageFilter, ImageOps
im = Image.open(SRC).convert("RGBA")
solid = im.getchannel("A").point(lambda v: 255 if v > 160 else 0).filter(ImageFilter.MinFilter(5))
x0, y0, x1, y1 = solid.getbbox()                 # erosion drops stray matte pixels
y1 = y0 + int((y1 - y0) * CROP_BOTTOM)           # head + upper body is the hero
trim = int((x1 - x0) * CROP_SIDES)
x0, x1 = x0 + trim, x1 - trim
pad = int((x1 - x0) * 0.03)
im = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), y1))
rows = round(im.height / im.width * COLS * CELL_W / CELL_H)
if rows > MAX_ROWS:
    COLS = round(MAX_ROWS * im.width / im.height * CELL_H / CELL_W)
    rows = MAX_ROWS

# local detail: sharpen + equalize luminance only inside the subject mask
rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=3, percent=160, threshold=2))
mask = im.getchannel("A")
gray = ImageOps.equalize(rgb.convert("L"), mask=mask.point(lambda v: 255 if v > 128 else 0))
gray = gray.resize((COLS, rows), Image.LANCZOS)
src_rgb = np.asarray(rgb.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255
alpha = np.asarray(mask.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255

lum = np.asarray(gray, dtype=np.float32) / 255
lum = lum ** GAMMA
lum = np.clip((lum - 0.5) * CONTRAST + 0.5, 0, 1)
lum = np.clip(lum * BRIGHTNESS * alpha, 0, 1)
lum = np.where(lum <= THRESHOLD, 0, (lum - THRESHOLD) / (1 - THRESHOLD))

# ---------- floyd-steinberg ----------
steps = POSTERIZE
f = lum.copy()
for y in range(rows):
    for x in range(COLS):
        old = min(1, max(0, f[y, x]))
        qv = round(old * (steps - 1)) / (steps - 1)
        val = old + (qv - old) * DITHER
        err = old - val
        f[y, x] = val
        if x + 1 < COLS:
            f[y, x + 1] += err * 7 / 16
        if y + 1 < rows:
            if x > 0:
                f[y + 1, x - 1] += err * 3 / 16
            f[y + 1, x] += err * 5 / 16
            if x + 1 < COLS:
                f[y + 1, x + 1] += err / 16
f = np.clip(f, 0, 1)

# ---------- layout ----------
W, H = 1000, 640
PW, PH = COLS * CELL_W, rows * CELL_H
PX, PY = 34, 52 + (H - 52 - PH) / 2 - 10   # portrait origin, vertically centred
cx, cy = PX + PW / 2, PY + PH / 2
GLITCH_ROWS = {rows * 0.22: "g1", rows * 0.47: "g2", rows * 0.71: "g3"}
glitch_of = {}
for anchor, cls in GLITCH_ROWS.items():
    for k in range(int(anchor), int(anchor) + 3):
        glitch_of[k] = cls

portrait = []
for y in range(rows):
    spans, cur_col, cur_txt = [], None, ""
    for x in range(COLS):
        v = f[y, x]
        ch = CHARS[min(len(CHARS) - 1, int(v * (len(CHARS) - 1)))]
        col = gradient(v) if ch != " " else cur_col
        if col != cur_col and cur_txt:
            spans.append((cur_col, cur_txt))
            cur_txt = ""
        cur_col = col
        cur_txt += ch
    if cur_txt:
        spans.append((cur_col, cur_txt))
    if not "".join(t for _, t in spans).strip():
        continue
    tsp = "".join(
        f'<tspan fill="{c}">{escape(t)}</tspan>' if c and t.strip() else escape(t)
        for c, t in spans
    )
    line = (f'<text y="{PY + y * CELL_H:.1f}" x="{PX}" textLength="{PW:.1f}" '
            f'lengthAdjust="spacing">{tsp}</text>')
    delay = (y * 0.09) % 4
    if y in glitch_of:
        line = f'<g class="{glitch_of[y]}">{line}</g>'
    portrait.append(f'<g class="fl" style="animation-delay:{-delay:.2f}s">{line}</g>')

# ---------- right panel ----------
RX = 540
info = [
    ("stack", "Laravel · Next.js · Tailwind CSS"),
    ("mobile", "Flutter · React Native"),
    ("langs", "PHP · TypeScript · Dart · Java"),
    ("school", "IDN Boarding School"),
    ("based", "Indonesia"),
    ("status", "building things that matter"),
]
kv = []
for i, (k, v) in enumerate(info):
    y = 356 + i * 30
    kv.append(
        f'<g class="in" style="animation-delay:{1.9 + i * 0.16:.2f}s">'
        f'<text x="{RX}" y="{y}" class="k">{k}</text>'
        f'<text x="{RX + 86}" y="{y}" class="d">::</text>'
        f'<text x="{RX + 112}" y="{y}" class="v">{escape(v)}</text></g>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Zainul Arkaan Alinsi — ASCII portrait">
<title>Zainul Arkaan Alinsi</title>
<defs>
  <radialGradient id="glow" cx="30%" cy="45%" r="55%">
    <stop offset="0" stop-color="#4f46e5" stop-opacity=".22"/>
    <stop offset="1" stop-color="#4f46e5" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="name" x1="0" x2="1">
    <stop offset="0" stop-color="#e2e8f0"/><stop offset=".55" stop-color="#67e8f9"/><stop offset="1" stop-color="#818cf8"/>
  </linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#67e8f9" stop-opacity="0"/><stop offset=".5" stop-color="#67e8f9" stop-opacity=".16"/><stop offset="1" stop-color="#67e8f9" stop-opacity="0"/>
  </linearGradient>
  <pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="#1e293b"/></pattern>
  <clipPath id="pclip"><rect x="{PX - 12}" y="{PY:.0f}" width="{PW + 24:.0f}" height="{PH:.0f}"/></clipPath>
  <clipPath id="frame"><rect x="18" y="52" width="{W - 36}" height="{H - 70}" rx="14"/></clipPath>
  <linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="0" y1="{PY + PH * 0.72:.0f}" x2="0" y2="{PY + PH:.0f}">
    <stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/>
  </linearGradient>
  <mask id="reveal">
    <circle cx="{cx:.0f}" cy="{cy:.0f}" r="0" fill="url(#fade)">
      <animate attributeName="r" from="0" to="{max(PW, PH):.0f}" dur="1.6s" begin="0s" fill="freeze" calcMode="spline" keySplines=".2 .7 .2 1" keyTimes="0;1"/>
    </circle>
  </mask>
</defs>
<style>
  text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; white-space: pre; }}
  .p text {{ font-size: {FONT}px; dominant-baseline: hanging; }}
  .fl {{ animation: flow 4s ease-in-out infinite; }}
  @keyframes flow {{ 0%,100% {{ transform: translateX(-2.2px) }} 50% {{ transform: translateX(2.2px) }} }}
  .g1 {{ animation: gl 5.2s steps(1) infinite; }}
  .g2 {{ animation: gl 6.8s steps(1) infinite 1.7s; }}
  .g3 {{ animation: gl 4.4s steps(1) infinite 3.1s; }}
  @keyframes gl {{
    0%,88%,100% {{ transform: translateX(0); filter: none; }}
    90% {{ transform: translateX(-26px); filter: hue-rotate(-120deg) saturate(2); }}
    92% {{ transform: translateX(18px); }}
    94% {{ transform: translateX(-8px); filter: hue-rotate(-120deg) saturate(2); }}
    96% {{ transform: translateX(0); filter: none; }}
  }}
  .scan {{ animation: scan 5s linear infinite; }}
  @keyframes scan {{ from {{ transform: translateY(-120px) }} to {{ transform: translateY({PH + 40:.0f}px) }} }}
  .blink {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0 }} }}
  .pulse {{ animation: pulse 1.6s ease-in-out infinite; }}
  @keyframes pulse {{ 50% {{ opacity: .25 }} }}
  .in {{ opacity: 0; animation: in .6s ease-out forwards; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(8px) }} to {{ opacity: 1; transform: none }} }}
  .k {{ fill: #67e8f9; font-size: 14px; }}
  .d {{ fill: #334155; font-size: 14px; }}
  .v {{ fill: #cbd5e1; font-size: 14px; }}
  .mut {{ fill: #64748b; font-size: 12px; letter-spacing: 2px; }}
  @media (prefers-reduced-motion: reduce) {{ .fl,.g1,.g2,.g3,.scan,.blink,.pulse {{ animation: none }} .in {{ opacity: 1; animation: none }} }}
</style>

<rect width="{W}" height="{H}" rx="18" fill="{BG}"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="#1e293b"/>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
</g>

<!-- window chrome -->
<circle cx="36" cy="27" r="5.5" fill="#ff5f57"/><circle cx="54" cy="27" r="5.5" fill="#febc2e"/><circle cx="72" cy="27" r="5.5" fill="#28c840"/>
<text x="{W / 2}" y="31" text-anchor="middle" fill="#64748b" font-size="12">zainul@idn: ~/profile — ascii.render --variant=flow</text>
<line x1="18" y1="50" x2="{W - 18}" y2="50" stroke="#1e293b"/>

<!-- portrait -->
<g class="p" mask="url(#reveal)">
  {"".join(portrait)}
</g>
<g clip-path="url(#pclip)"><rect class="scan" x="{PX - 10}" y="{PY:.0f}" width="{PW + 20:.0f}" height="90" fill="url(#scan)"/></g>
<g transform="translate({PX + 2},{H - 40})">
  <rect width="176" height="26" rx="13" fill="#0f141c" stroke="#1e293b"/>
  <circle cx="16" cy="13" r="4" fill="#a3e635" class="pulse"/>
  <text x="28" y="17.5" class="mut" style="font-size:11px">RENDER / LIVE</text>
</g>

<!-- right panel -->
<g class="in" style="animation-delay:.6s">
  <text x="{RX}" y="118" fill="#a3e635" font-size="15">❯ <tspan fill="#e2e8f0">whoami</tspan><tspan class="blink" fill="#67e8f9">▌</tspan></text>
</g>
<g class="in" style="animation-delay:1s">
  <text x="{RX - 3}" y="190" font-size="50" font-weight="800" fill="url(#name)" letter-spacing="-1">ZAINUL</text>
  <text x="{RX - 3}" y="244" font-size="50" font-weight="800" fill="url(#name)" letter-spacing="-1">ARKAAN ALINSI</text>
</g>
<g class="in" style="animation-delay:1.4s">
  <text x="{RX}" y="284" fill="#94a3b8" font-size="16">Full-Stack Developer <tspan fill="#334155">/</tspan> Student</text>
  <line x1="{RX}" y1="312" x2="{W - 50}" y2="312" stroke="#1e293b" stroke-dasharray="3 5"/>
</g>
{"".join(kv)}
<g class="in" style="animation-delay:3s">
  <text x="{W - 50}" y="{H - 22}" text-anchor="end" class="mut">v2026 · EOF</text>
</g>
</svg>
'''
open(OUT, "w", encoding="utf-8").write(svg)
print(f"{OUT}: {len(svg) / 1024:.1f} KB, grid {COLS}x{rows}, portrait {PW:.0f}x{PH:.0f}px")
