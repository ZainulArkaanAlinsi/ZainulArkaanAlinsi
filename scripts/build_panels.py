"""Static panels: neo-brutalist cards with a Minecraft streak through them.
No network, no API — run it any time:

    python scripts/build_panels.py

  intro.svg        name, role, stickers, a pixel portrait, a tech-stack marquee
  btn-*.svg        the link buttons
  about.svg        about me                       (half width, pairs with stats)
  stack.svg        the tech stack as tiles        (half width, pairs with the log)
  news.svg         the news header
  footer.svg       the sign-off

hero.svg is the old ASCII portrait; it is kept only as the source the pixel
portrait is cut from.
"""
import base64
import io
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mc  # noqa: E402
from brut import (BLUE, CARD_H, HALF, INK, LIME, MUTED, ORANGE, PINK, RED, W, WHITE, YELLOW,  # noqa: E402
                  box, card, heavy, heavy_w, mono, pixel_text, pixel_width, rect, sticker, svg, tab, text)
from theme import ASSETS  # noqa: E402

ICONS = json.loads((ASSETS.parent / "scripts" / "icons.json").read_text())
PATHS, STACK = ICONS["paths"], ICONS["stack"]

LINKS = [("github", "GitHub", "https://github.com/ZainulArkaanAlinsi?tab=repositories", LIME),
         ("instagram", "Instagram", "https://instagram.com/zainarilbre", PINK),
         ("linkedin", "LinkedIn", "https://linkedin.com/in/zainul-arkaan-3bb51731a", BLUE),
         ("youtube", "YouTube", "https://www.youtube.com/@zainarilbre", RED),
         ("gmail", "Email", "mailto:zainaril13@gmail.com", YELLOW)]

BRAND = {
    "php": "#777BB4", "typescript": "#3178C6", "javascript": "#E8C400", "dart": "#0175C2",
    "openjdk": "#E76F00", "html5": "#E34F26", "css": "#663399", "laravel": "#FF2D20",
    "nextdotjs": "#000000", "react": "#149ECA", "vuedotjs": "#42B883", "tailwindcss": "#06B6D4",
    "alpinedotjs": "#2D8A9E", "flutter": "#02569B", "nodedotjs": "#5FA04E", "mysql": "#4479A1",
    "sqlite": "#003B57", "firebase": "#DD2C00", "vercel": "#000000", "git": "#F05032",
    "github": "#181717", "figma": "#F24E1E", "postman": "#FF6C37",
}
HEAVY_ARIAL = "'Arial Black',Arial,sans-serif"


def icon(slug, x, y, size, fill, op=1.0):
    k = size / 24
    o = f' opacity="{op}"' if op < 1 else ""
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="{fill}"{o}>'
            f'<path d="{PATHS[slug]}"/></g>')


def block(kind, x, y, s, cls="", style=""):
    """A Minecraft block, rendered with its real textures."""
    c = f' class="{cls}"' if cls else ""
    st = f' style="{style}"' if style else ""
    return f'<g{c}{st}>{mc.image(mc.png_uri(mc.icon(kind, 128)), x, y, s, s)}</g>'


# -------------------------------------------------------------------- portrait
def painting():
    """The ASCII portrait, re-cut as a chunky pixel portrait in a warm palette
    on the card's pink. Falls back to a plain field if the source is gone."""
    src = ASSETS / "hero.svg"
    m = re.search(r'href="data:image/png;base64,([^"]+)"', src.read_text()) if src.exists() else None
    W_, H_ = 44, 50
    if m:
        im = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("L")
        im = im.crop((150, 40, im.width - 150, int(im.height * .86))).filter(ImageFilter.GaussianBlur(7))
        im = im.resize((W_, H_), Image.BOX)
        a = np.asarray(im, float)
        a = (a - a.min()) / max(1, a.max() - a.min())
    else:
        a = np.full((H_, W_), .3)
    pal = np.array([(255, 122, 182), (17, 17, 17), (70, 50, 40), (140, 100, 70), (210, 160, 110), (255, 230, 180)])
    idx = np.clip((a ** .75) * (len(pal) - 1.01) + 1, 1, len(pal) - 1).astype(int)
    idx[a < .1] = 0
    return Image.fromarray(pal[idx].astype(np.uint8)).resize((W_ * 8, H_ * 8), Image.NEAREST)


# ----------------------------------------------------------------------- intro
MARQUEE = "PHP · LARAVEL · NEXT.JS · REACT · TYPESCRIPT · TAILWIND · FLUTTER · DART · MYSQL · FIREBASE · GIT · "
INTRO_CSS = ("@keyframes mq{from{transform:translateX(0)}to{transform:translateX(-%dpx)}}"
             ".mq{animation:mq 28s linear infinite}")


def intro():
    h = 540
    out = [card(W, h)]
    x = 44
    out.append(sticker(140, 56, "HELLO, WORLD!", LIME, -4, 16))
    out.append(rect(x - 8, 176, heavy_w("ARKAAN", 96) * .84, 62, YELLOW))           # highlighter
    for i, ln in enumerate(("ZAINUL", "ARKAAN", "ALINSI")):
        out.append(heavy(x, 146 + i * 88, ln, 96))
    out.append(mono(x, 358, "> FULL-STACK DEVELOPER_", 22, INK, weight=800))
    out.append(text(x, 394, "Student at IDN Boarding School. I build web apps with", 19, MUTED, weight=600))
    out.append(text(x, 422, "PHP, Laravel, Next.js & Tailwind, and I'm learning Flutter.", 19, MUTED, weight=600))
    px, py, pw, ph = 790, 44, 310, 350
    out.append(f'<g transform="rotate(3 {px + pw / 2} {py + ph / 2})">'
               + box(px, py, pw, ph, PINK, sh=8)
               + mc.image(mc.png_uri(painting(), 16), px + 14, py + 14, pw - 28, ph - 28) + "</g>")
    out.append(block("grass", px - 58, py + ph - 76, 100, "bob"))
    out.append(sticker(px + pw - 6, py + 4, "LVL UP!", YELLOW, 10, 17, cls="wob"))
    out.append(sticker(px + 150, py + ph + 6, "LEARNING FLUTTER", BLUE, -4, 14))
    by, bh = h - 96, 62
    out.append(rect(5, by, W - 16, bh, INK))
    unit = pixel_width(MARQUEE, 3) + 18
    strip = "".join(pixel_text(MARQUEE, 20 + k * unit, by + 21, 3, YELLOW) for k in range(3))
    out.append(f'<clipPath id="mq"><rect x="5" y="{by}" width="{W - 16}" height="{bh}"/></clipPath>'
               f'<g clip-path="url(#mq)"><g class="mq">{strip}</g></g>')
    return svg(W, h, "".join(out), css=INTRO_CSS % unit,
               label="Zainul Arkaan Alinsi — full-stack developer, student at IDN Boarding School")


# --------------------------------------------------------------------- buttons
def button(slug, lab, fill):
    w, h = 236, 76
    bw_, bh_ = w - 10, h - 10
    out = [box(2, 2, bw_ - 2, bh_ - 2, fill, sh=6),
           icon(slug, 20, (bh_ - 26) / 2 + 1, 26, INK),
           text(58, bh_ / 2 + 8, lab.upper(), 19, INK, weight=900, font=HEAVY_ARIAL),
           text(bw_ - 20, bh_ / 2 + 8, "→", 22, INK, "end", 900)]
    return svg(w, h, "".join(out), label=lab)


# ----------------------------------------------------------------------- about
BLURB = ["I build full-stack web apps with PHP,", "Laravel, Next.js and Tailwind CSS. I'm",
         "learning Flutter so the same work can", "ship to mobile. I like efficient code",
         "that people actually use."]
FACTS = [("BUILDING", "Web apps", YELLOW), ("LEARNING", "Flutter, Dart", BLUE),
         ("EDITOR", "VS Code", PINK), ("TIMEZONE", "WIB, UTC+7", LIME)]


def about():
    w, h = HALF, CARD_H
    out = [card(w, h)]
    out.append(tab(26, 24, "ABOUT ME")[0])
    out.append(sticker(w - 80, 46, "#01", ORANGE, 6, 16))
    for i, ln in enumerate(BLURB):
        out.append(text(30, 120 + i * 30, ln, 19, INK, weight=600))
    gx, gy, gw, gh = 26, 290, (w - 26 * 2 - 6 - 16) / 2, 92
    for i, (k, v, c) in enumerate(FACTS):
        x = gx + (i % 2) * (gw + 16)
        y = gy + (i // 2) * (gh + 18)
        out.append(box(x, y, gw, gh, c, sh=5))
        out.append(mono(x + 16, y + 30, k, 13, INK, weight=800))
        out.append(text(x + 16, y + 68, v, 23, INK, weight=900, font=HEAVY_ARIAL))
    out.append(block("bookshelf", w - 84, 92, 56))
    return svg(w, h, "".join(out), label="About me: " + " ".join(BLURB))


# ----------------------------------------------------------------------- stack
ROW_FILL = {"languages": YELLOW, "frameworks": PINK, "tools": BLUE}


def stack():
    w, h = HALF, CARD_H
    out = [card(w, h)]
    out.append(tab(26, 24, "TECH STACK")[0])
    n = sum(len(v) for v in STACK.values())
    out.append(sticker(w - 92, 46, f"{n} ITEMS", LIME, -5, 15))
    s, gap = 54, 10
    y = 92
    pos = []
    for name, items in STACK.items():
        lab = name.upper()
        out.append(box(26, y, len(lab) * 9.6 + 22, 26, ROW_FILL[name], sh=3, bw=2))
        out.append(mono(37, y + 18, lab, 13, INK, weight=900))
        y += 38
        for i, (slug, label) in enumerate(items):
            x = 26 + i * (s + gap)
            out.append(box(x, y, s, s, WHITE, sh=4, bw=3))
            out.append(icon(slug, x + 13, y + 13, 28, BRAND.get(slug, INK)))
            out.append(text(x + s / 2 + 2, y + s + 20, label, 10, INK, "middle", 700))
            pos.append((x, y))
        y += s + 40
    # a Minecraft hotbar selector walks the tiles
    o = s + 10
    vals = ";".join(f"{x - 5:.0f} {yy - 5:.0f}" for x, yy in pos)
    out.append(f'<g><path d="M0 0h{o}v{o}h-{o}Z M5 5v{s}h{s}v-{s}Z" fill="{INK}" fill-rule="evenodd"/>'
               f'<path d="M2 2h{o - 4}v{o - 4}h-{o - 4}Z M5 5v{s}h{s}v-{s}Z" fill="{WHITE}" fill-rule="evenodd"/>'
               f'<animateTransform attributeName="transform" type="translate" values="{vals}" calcMode="discrete"'
               f' dur="{len(pos) * .9:.1f}s" repeatCount="indefinite"/></g>')
    return svg(w, h, "".join(out),
               label="Tech stack: " + ", ".join(lab for items in STACK.values() for _, lab in items))


# ----------------------------------------------------------- news header, footer
def news_header(stamp="", count=0):
    h = 128
    out = [card(W, h, BLUE),
           heavy(40, 82, "DEV NEWS", 56),
           text(372, 64, (f"{count} fresh stories from the source feeds" if count
                          else "fresh stories from the source feeds"), 19, INK, weight=800),
           text(372, 92, f"refreshed {stamp}" if stamp else "refreshed automatically", 15, INK, weight=600),
           sticker(W - 150, 60, "HOT OFF THE PRESS", YELLOW, 5, 15, cls="wob")]
    return svg(W, h, "".join(out), label="Developer news, refreshed automatically")


def footer():
    h = 150
    out = [card(W, h, INK),
           heavy(W / 2, 76, "THANKS FOR STOPPING BY!", 44, YELLOW, "middle"),
           mono(W / 2, 110, "every panel here is generated by python in this repo · see you next push",
                13, WHITE, "middle", 500)]
    for i, k in enumerate(("grass", "planks", "gold_block")):
        out.append(block(k, 30 + i * 58, 42, 54, "bob", f"animation-delay:{-i * .4:.1f}s"))
        out.append(block(k, W - 100 - i * 58, 42, 54, "bob", f"animation-delay:{-i * .4 - .2:.1f}s"))
    return svg(W, h, "".join(out), label="Thanks for stopping by")


# ------------------------------------------------------------------ placeholder
def loading(w, h, what):
    """Shown only until the first real sync writes the panel."""
    out = [card(w, h), heavy(w / 2, h / 2 + 10, "LOADING...", 44, INK, "middle"),
           text(w / 2, h / 2 + 46, f"{what} appears after the next GitHub Actions run", 16, MUTED, "middle", 600),
           block("grass", w / 2 - 32, h / 2 - 100, 64, "bob")]
    return svg(w, h, "".join(out), label=f"{what}: waiting for the first sync")


# ----------------------------------------------------------------------- build
def build():
    ASSETS.mkdir(parents=True, exist_ok=True)
    made = {"intro.svg": intro(), "about.svg": about(), "stack.svg": stack(), "footer.svg": footer()}
    for slug, lab, _, fill in LINKS:
        made[f"btn-{slug}.svg"] = button(slug, lab, fill)
    if not (ASSETS / "news.svg").exists() or "--force-news" in sys.argv:
        made["news.svg"] = news_header()
    for name, (w, h, what) in {"stats.svg": (HALF, CARD_H, "Player stats"),
                               "log.svg": (HALF, CARD_H, "The commit log"),
                               "calendar.svg": (W, 420, "The contribution calendar")}.items():
        if not (ASSETS / name).exists():
            made[name] = loading(w, h, what)
    for name, body in made.items():
        (ASSETS / name).write_text(body, encoding="utf-8")
    return list(made)


if __name__ == "__main__":
    for n in build():
        print("wrote", n)
