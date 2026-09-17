"""Zine cover (hero) + font subsets. Local only: needs Pillow, numpy, fontTools.

    python build_cover.py <cutout.png> <fonts_dir> <out_dir>

Writes zine-fonts.json next to this file (used by zine.py / build_pages.py in CI)
and <out_dir>/cover.svg with the portrait "typed" in ink like a typewriter print.
"""
import base64
import io
import json
import sys
from html import escape
from pathlib import Path

import numpy as np
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
SRC, FONTS, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
CHARSET = "".join(chr(c) for c in range(32, 127))


def _bytes(font):
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def subset(font):
    opts = Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga", "calt"]
    sub = Subsetter(opts)
    sub.populate(text=CHARSET)
    f = TTFont(io.BytesIO(_bytes(font)))
    sub.subset(f)
    f.flavor = "woff"
    return base64.b64encode(_bytes(f)).decode()


def metrics(font):
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    return {ch: round(hmtx[cmap[ord(ch)]][0] / upm, 4) for ch in CHARSET if ord(ch) in cmap}


families = {
    "Type": TTFont(FONTS / "SpecialElite-Regular.ttf"),
    "Hand": instantiateVariableFont(TTFont(FONTS / "Caveat[wght].ttf"), {"wght": 600}),
    "Block": TTFont(FONTS / "ArchivoBlack-Regular.ttf"),
}
css = {name: f"@font-face{{font-family:'{name}';src:url(data:font/woff;base64,{subset(f)}) format('woff')}}" for name, f in families.items()}
(HERE / "zine-fonts.json").write_text(json.dumps({"css": css, "metrics": {n: metrics(f) for n, f in families.items()}}), encoding="utf-8")

import zine as z  # noqa: E402  (needs zine-fonts.json)

# ------------------------------------------------------------------ typed portrait
typewriter = TTFont(FONTS / "CourierPrime-Bold.ttf")
ADV = typewriter["hmtx"]["zero"][0] / typewriter["head"].unitsPerEm
PHOTO_W, PHOTO_H = 414, 470
FS = 7.2
CW, CH = FS * ADV, FS
COLS, ROWS = int(PHOTO_W // CW), int(PHOTO_H // CH)
RAMP = " .:-=+*#%@"


def portrait_png(scale=2):
    im = Image.open(SRC).convert("RGBA")
    aspect = (COLS * CW) / (ROWS * CH)
    cw = int(im.width * 0.5)
    chh = int(cw / aspect)
    rows_alpha = np.where(np.asarray(im.getchannel("A")).max(axis=1) > 200)[0]
    top = max(0, int(rows_alpha[0]) - 26)
    cx = im.width * .495
    im = im.crop((int(cx - cw / 2), top, int(cx + cw / 2), min(im.height, top + chh)))

    rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=1))
    mask = im.getchannel("A")
    size = (COLS, ROWS)
    lum = np.asarray(rgb.convert("L").resize(size, Image.LANCZOS), dtype=np.float32) / 255
    a = np.asarray(mask.resize(size, Image.LANCZOS), dtype=np.float32) / 255
    m = (a > .5).astype(np.float32)

    def blur(arr, r):
        img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
        return np.asarray(img, dtype=np.float32) / 255

    vals = lum[m > 0]
    lo, hi = np.percentile(vals, 2), np.percentile(vals, 98)
    lum = np.clip((lum - lo) / (hi - lo), 0, 1)
    mean = blur(lum * m, 4) / np.maximum(blur(m, 4), 1e-3)
    sq = blur(lum * lum * m, 4) / np.maximum(blur(m, 4), 1e-3)
    std = np.sqrt(np.maximum(sq - mean ** 2, 1e-4))
    local = np.clip(.5 + (lum - mean) / (2.5 * std + .05), 0, 1)
    lum = local * .7 + lum * .3
    ink = np.clip((1 - lum) ** 1.4 * 1.3, 0, 1) * a          # print: dark areas get the dense glyphs

    font = ImageFont.truetype(io.BytesIO(_bytes(typewriter)), size=round(FS * scale))
    size_px = (round(COLS * CW * scale), round(ROWS * CH * scale))
    alpha_layer = Image.new("L", size_px, 0)
    draw = ImageDraw.Draw(alpha_layer)
    for y in range(ROWS):
        for x in range(COLS):
            v = float(ink[y, x])
            ch = RAMP[min(len(RAMP) - 1, int(v * (len(RAMP) - 1)))]
            if ch == " ":
                continue
            draw.text((x * CW * scale, (y + .8) * CH * scale), ch, font=font, fill=int(90 + 165 * v), anchor="ls")
    canvas = Image.new("LA", size_px, (27, 0))
    canvas.putalpha(alpha_layer)
    buf = io.BytesIO()
    canvas.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------ cover
def cover():
    W, H = 1200, 820
    png = portrait_png()

    pol_w, pol_h = 470, 600
    photo = (f'<rect x="28" y="28" width="{PHOTO_W}" height="{PHOTO_H}" fill="#efe8da"/>'
             f'<rect x="28" y="28" width="{PHOTO_W}" height="{PHOTO_H}" fill="url(#grain)"/>'
             f'<image href="data:image/png;base64,{png}" x="28" y="28" width="{COLS * CW:.1f}" height="{ROWS * CH:.1f}"/>'
             f'<text x="{pol_w / 2}" y="{pol_h - 30}" text-anchor="middle" class="hand" font-size="40" fill="{z.INK}">that\'s me :)</text>')
    polaroid = (f'<g transform="translate(62,128) rotate(-3.5 {pol_w / 2} {pol_h / 2})">'
                f'<rect x="7" y="9" width="{pol_w}" height="{pol_h}" fill="#000" opacity=".35"/>'
                f'<rect width="{pol_w}" height="{pol_h}" fill="{z.PAPER_W}" stroke="#d8d0c0"/>{photo}</g>'
                + z.tape(110, 138, 130, -32) + z.tape(500, 122, 130, 28))

    name, _ = z.ransom("ZAINUL", 610, 262, 96, seed=11)
    sub_size = 52
    while z.text_w("ARKAAN ALINSI", "Block", sub_size) > 540:
        sub_size -= 1
    arkaan_w = z.text_w("ARKAAN ", "Block", sub_size)
    alinsi_w = z.text_w("ALINSI", "Block", sub_size)

    para = ["full-stack developer & student at",
            "IDN Boarding School. i build web apps",
            "with laravel, next.js & tailwind css,",
            "and right now i'm learning flutter."]
    para_svg = "".join(f'<text x="614" y="{428 + i * 34}" class="tw" font-size="23" fill="{z.INK}">{escape(t)}</text>' for i, t in enumerate(para))
    cursor_x = 614 + z.text_w(para[-1], "Type", 23) + 6

    body = (
        z.paper(16, 22, 1168, 780, seed=3, torn=(True, False, True, False))
        + f'<text x="60" y="78" class="tw" font-size="18" fill="{z.INK}">ISSUE #01 -- SEPT 2026 -- FREE, TAKE ONE</text>'
        + f'<text x="1140" y="80" text-anchor="end" class="hand" font-size="32" fill="{z.PENCIL}">a tiny zine by zainul</text>'
        + f'<line x1="60" y1="98" x2="1140" y2="98" stroke="{z.INK}" stroke-width="2" stroke-dasharray="10 7"/>'
        + polaroid
        + z.arrow(640, 170, 470, 262, bend=-50, cls="bob")
        + f'<g transform="translate(652,168) rotate(-10)"><text class="hand wob" font-size="54" fill="{z.RED}">hi!</text></g>'
        + name
        + z.highlight(610 + arkaan_w - 6, 318, alinsi_w + 16, 50, z.PINK, rot=-1.5)
        + f'<text x="612" y="358" class="blk" font-size="{sub_size}" fill="{z.INK}">ARKAAN ALINSI</text>'
        + para_svg
        + f'<rect x="{cursor_x:.0f}" y="{428 + 3 * 34 - 19}" width="12" height="22" fill="{z.INK}" class="blink"/>'
        + z.squiggle(614, 580, 250, color=z.RED)
        + z.circle_sticker(1112, 612, 56, z.YELLOW, ["FULL", "STACK!"], rot=12, size=18, cls="wob")
        + z.label_sticker(740, 640, "OPEN TO COLLAB", z.MINT, rot=-5, size=22, cls="wob", delay=-1.2)
        + z.label_sticker(990, 700, "LARAVEL + NEXT.JS", z.LILAC, rot=4, size=19)
        + z.star(1135, 392, 28, color=z.MINT, cls="spin")
        + z.typed_cat(912, 562, size=19, accent=z.RED)
        + f'<g transform="translate(118,776) rotate(-2)"><text class="tw" font-size="16" fill="{z.PENCIL}">fig. 1 -- the author, rendered in ascii</text></g>'
        + f'<g transform="translate(640,760) rotate(-3)"><text class="hand" font-size="34" fill="{z.INK}">psst... scroll down</text></g>'
        + z.arrow(880, 735, 905, 790, bend=14, cls="bob")
    )
    (OUT / "cover.svg").write_text(z.doc(W, H, "Zainul Arkaan Alinsi — a tiny zine", body, seed=1), encoding="utf-8")


cover()
for p in sorted(OUT.glob("*.svg")):
    print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
