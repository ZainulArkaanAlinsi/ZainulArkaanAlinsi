"""Static panels, drawn the way the game draws them. No network, no API:

    python scripts/build_panels.py

  title.svg         the title screen: blurred block panorama, stone logo, splash
  btn-*.svg         menu buttons (the profile's links)
  book.svg          About me, as a Book & Quill page with a painting of me
  inventory.svg     the tech stack as a survival inventory, with a crafting grid
  news.svg          the news header, on the options-screen dirt
  footer.svg        "Saving world..."
"""
import base64
import io
import json
import os
import random
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mc  # noqa: E402
from gui import (AQUA, GRAY, HALF, LABEL, SPLASH_CSS, W, YELLOW, inset, label, mc_pixel, mc_text,  # noqa: E402
                 pixel_width, rect, selector, slot, splash, svg, text, tooltip, window)
from theme import ASSETS, FONT5, SANS, rgb  # noqa: E402

ICONS = json.loads((ASSETS.parent / "scripts" / "icons.json").read_text())
PATHS, STACK = ICONS["paths"], ICONS["stack"]
CARD_H = 500                                  # every half-width card shares this height

LINKS = [("instagram", "Instagram", "https://instagram.com/zainarilbre"),
         ("linkedin", "LinkedIn", "https://linkedin.com/in/zainul-arkaan-3bb51731a"),
         ("youtube", "YouTube", "https://www.youtube.com/@zainarilbre"),
         ("gmail", "Email", "mailto:zainaril13@gmail.com"),
         ("github", "Repositories", "https://github.com/ZainulArkaanAlinsi?tab=repositories")]


def icon(slug, x, y, size, fill, op=1.0):
    k = size / 24
    o = f' opacity="{op}"' if op < 1 else ""
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="{fill}"{o}>'
            f'<path d="{PATHS[slug]}"/></g>')


BRAND = {
    "php": "#777BB4", "typescript": "#3178C6", "javascript": "#F7DF1E", "dart": "#0175C2",
    "openjdk": "#E76F00", "html5": "#E34F26", "css": "#663399", "laravel": "#FF2D20",
    "nextdotjs": "#FFFFFF", "react": "#61DAFB", "vuedotjs": "#4FC08D", "tailwindcss": "#06B6D4",
    "alpinedotjs": "#8BC0D0", "flutter": "#47C5FB", "nodedotjs": "#5FA04E", "mysql": "#4479A1",
    "sqlite": "#4FA3D1", "firebase": "#FFCA28", "vercel": "#FFFFFF", "git": "#F05032",
    "github": "#FFFFFF", "figma": "#F24E1E", "postman": "#FF6C37",
}
CATEGORY = {"languages": "Language", "frameworks": "Framework", "tools": "Tool"}


def item(slug, x, y, s):
    """A stack logo drawn as an item: its brand colour, a dark under-shadow so it
    sits on the grey slot like a sprite does."""
    c = BRAND.get(slug, "#FFFFFF")
    k = s * .06
    return icon(slug, x + k, y + k, s, "#000000", .45) + icon(slug, x, y, s, c)


# ----------------------------------------------------------------- dirt screens
def dirt_bg(w, h, k=.32):
    """The options-screen background: dirt, darkened, at 4px per texel."""
    return mc.tile("dirt", w * 2, h * 2, scale=8, k=k)


# ---------------------------------------------------------------- title screen
def panorama(w, h, seed=11):
    """A side-on slice of terrain at 2x: sky, hills, trees, caves, ores."""
    B = 72                                              # block size at 2x
    cols, rows = w * 2 // B + 2, h * 2 // B + 2
    rng = random.Random(seed)
    img = Image.new("RGB", (cols * B, rows * B))
    d = ImageDraw.Draw(img)
    top, bot = (120, 167, 255), (200, 222, 255)
    for y in range(rows * B):
        t = y / (rows * B)
        d.line([(0, y), (cols * B, y)], fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    surf = []
    hgt = rows * .58
    for x in range(cols):
        hgt += rng.choice((-1, 0, 0, 0, 1)) * .9
        hgt = min(max(hgt, rows * .45), rows * .72)
        surf.append(int(hgt))
    tiles = {}

    def put(cx, cy, name, k=1.0):
        key = (name, k)
        if key not in tiles:
            tiles[key] = Image.fromarray(mc.shade_arr(mc.tex(name), k)).resize((B, B), Image.NEAREST)
        img.paste(tiles[key], (cx * B, cy * B))
    for x, s in enumerate(surf):
        for y in range(s, rows):
            depth = y - s
            if depth == 0:
                put(x, y, "grass_side")
            elif depth < 3:
                put(x, y, "dirt")
            else:
                r = rng.random()
                name = ("diamond_ore" if r < .03 else "emerald_ore" if r < .07 else "gold_ore" if r < .11
                        else "redstone_ore" if r < .14 else "stone")
                put(x, y, name, .9 - min(.35, depth * .04))
    for x in range(2, cols - 2, 1):                     # trees
        if rng.random() < .22 and surf[x] == surf[x - 1]:
            s = surf[x]
            for k in range(1, 5):
                put(x, s - k, "log_side")
            for dx in (-2, -1, 0, 1, 2):
                for dy in (4, 5):
                    put(x + dx, s - dy - 1, "leaves")
            for dx in (-1, 0, 1):
                put(x + dx, s - 7, "leaves")
    return img.crop((0, 0, w * 2, h * 2))


def logo(s, px):
    """The stone logo: bitmap letters filled with cobblestone, lit from the
    top, extruded downward and outlined in black. Returns an RGBA image."""
    cols = len(s) * 6 - 1
    mask = np.zeros((7, cols), bool)
    for i, ch in enumerate(s):
        for ry, row in enumerate(FONT5.get(ch, FONT5[" "]).split()):
            for rx, v in enumerate(row):
                if v == "1":
                    mask[ry, i * 6 + rx] = True
    dep = int(px * .8)
    o = int(px * .22)
    W_, H_ = cols * px + 2 * o, 7 * px + dep + 2 * o
    img = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    m = Image.fromarray((mask * 255).astype(np.uint8)).resize((cols * px, 7 * px), Image.NEAREST)
    stone = mc.tile("cobble", cols * px, 7 * px, scale=max(2, px // 6)).convert("RGBA")
    # vertical light: brighter top rows, darker bottom
    grad = np.linspace(1.25, .78, 7 * px)[:, None, None]
    st = np.clip(np.asarray(stone, float)[:, :, :3] * grad, 0, 255).astype(np.uint8)
    stone = Image.fromarray(st).convert("RGBA")
    side = Image.new("RGBA", m.size, (52, 52, 52, 255))
    outline = Image.new("RGBA", m.size, (0, 0, 0, 255))
    for dy in range(dep + o, -1, -1):                  # outline under everything
        for dx in (-o, 0, o):
            img.paste(outline, (o + dx, o + dy - o), m)
    for dy in range(dep, 0, -1):                        # extrusion
        k = 60 + int(40 * (1 - dy / dep))
        side = Image.new("RGBA", m.size, (k, k, k, 255))
        img.paste(side, (o, o + dy), m)
    img.paste(stone, (o, o), m)
    return img


TITLE_CSS = SPLASH_CSS + ("@keyframes pan{0%{transform:translateX(0)}100%{transform:translateX(-60px)}}"
                          ".pan{animation:pan 30s ease-in-out infinite alternate}")


def title():
    h = 470
    bg = mc.blur(panorama(W + 80, h), 6)
    arr = np.asarray(bg, float) * .78
    bg = Image.fromarray(arr.astype(np.uint8))
    lg = logo("ZAINUL ARKAAN", 26)
    lw, lh = lg.size[0] / 2, lg.size[1] / 2
    lx, ly = (W - lw) / 2, 74
    body = [f'<g class="pan">{mc.image(mc.png_uri(bg, 160), 0, 0, W + 80, h)}</g>',
            mc.image(mc.png_uri(lg, 64), lx, ly, lw, lh)]
    ed = "FULL-STACK EDITION"
    ew = pixel_width(ed, 3)
    ey = ly + lh + 10
    body.append(rect((W - ew) / 2 - 14, ey - 9, ew + 28, 21 + 18, "#000000", .55))
    body.append(mc_pixel(ed, (W - ew) / 2, ey, 3, "#FFFFFF"))
    body.append(splash(lx + lw - 40, ly + lh - 6, "Laravel + Next.js!", 20, -20))
    body.append(mc_text(W / 2, ey + 74, "Full-stack developer · Student at IDN Boarding School", 18, "#FFFFFF",
                        "middle", 700, SANS))
    body.append(mc_text(W / 2, ey + 102, "I build web apps with PHP, Laravel, Next.js & Tailwind — and I'm learning"
                        " Flutter.", 14.5, "#E8E8E8", "middle", 400, SANS))
    body.append(mc_text(14, h - 14, "Zainul Arkaan Alinsi · v2026", 13, "#FFFFFF"))
    body.append(mc_text(W - 14, h - 14, "WIB (UTC+7) · Indonesia", 13, "#FFFFFF", "end"))
    body.append('<rect x="1" y="1" width="1198" height="{0}" fill="none" stroke="#000" stroke-width="2"/>'.format(h - 2))
    return svg(W, h, "".join(body), css=TITLE_CSS,
               label="Zainul Arkaan Alinsi — Full-stack developer, student at IDN Boarding School")


# ------------------------------------------------------------------- buttons
def button(slug, lab, w=380, h=48):
    tex = mc.tile("stone", w * 2, h * 2, scale=6, k=.62)
    body = [rect(0, 0, w, h, "#000000"),
            mc.image(mc.png_uri(tex, 32), 2, 2, w - 4, h - 4),
            rect(2, 2, w - 4, 3, "#FFFFFF", .32), rect(2, 2, 3, h - 4, "#FFFFFF", .22),
            rect(2, h - 6, w - 4, 4, "#000000", .38), rect(w - 5, 2, 3, h - 4, "#000000", .3),
            icon(slug, 18, (h - 22) / 2, 22, "#FFFFFF", .95),
            mc_text(w / 2 + 10, h / 2 + 6, lab, 17, "#FFFFFF", "middle", 700, SANS)]
    return svg(w, h, "".join(body), label=lab)


# ----------------------------------------------------------------- book & quill
BLURB = ["I build full-stack web apps with PHP,", "Laravel, Next.js and Tailwind CSS, and",
         "I'm learning Flutter so I can take the", "same work to mobile. I like efficient",
         "code that people actually use."]
FACTS = [("Building", "Web apps"), ("Learning", "Flutter, Dart"), ("Editor", "VS Code"),
         ("Timezone", "WIB, UTC+7")]
INK = "#2A1E12"


def painting():
    """The ASCII portrait from the hero, re-cut as a low-res painting with a
    warm palette, in an oak frame. Falls back to a plain canvas if it's gone."""
    src = ASSETS / "hero.svg"
    m = re.search(r'href="data:image/png;base64,([^"]+)"', src.read_text()) if src.exists() else None
    W_, H_ = 40, 46
    if m:
        im = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("L")
        im = im.crop((150, 40, im.width - 150, int(im.height * .86)))
        im = im.resize((W_, H_), Image.BOX)
        a = np.asarray(im, float)
        a = (a - a.min()) / max(1, a.max() - a.min())
    else:
        a = np.full((H_, W_), .3)
    pal = np.array([(38, 28, 24), (74, 52, 40), (118, 84, 58), (164, 120, 80), (206, 164, 112), (238, 210, 160)])
    idx = np.clip((a ** .8) * (len(pal) - .01), 0, len(pal) - 1).astype(int)
    canvas = Image.fromarray(pal[idx].astype(np.uint8))
    frame = Image.new("RGB", (W_ + 4, H_ + 4))
    frame.paste(Image.fromarray(mc.tex("planks")).resize((W_ + 4, H_ + 4), Image.NEAREST))
    frame.paste(canvas, (2, 2))
    return frame.resize(((W_ + 4) * 4, (H_ + 4) * 4), Image.NEAREST)


def book():
    w, h = HALF, CARD_H
    rng = random.Random(5)
    pg = Image.new("RGB", (w * 2, h * 2), (243, 233, 210))
    d = ImageDraw.Draw(pg)
    for _ in range(2600):
        x, y = rng.randrange(w * 2), rng.randrange(h * 2)
        c = rng.choice(((236, 224, 198), (248, 240, 220), (229, 216, 188)))
        d.rectangle([x, y, x + 3, y + 3], fill=c)
    body = [rect(0, 0, w, h, "#000000"),
            rect(2, 2, w - 4, h - 4, "#6B4A2B"),                         # leather cover
            mc.image(mc.png_uri(pg, 24), 12, 10, w - 30, h - 22),        # the page
            rect(w - 18, 10, 6, h - 22, "#C9B48E"),                      # page edges
            rect(w - 12, 12, 2, h - 24, "#A88F66")]
    body.append(text(w - 36, 40, "Page 1 of 1", 13, INK, "end"))
    p = painting()
    pw, ph = p.size[0] / 1.45, p.size[1] / 1.45
    body.append(mc.image(mc.png_uri(p, 64), 34, 30, pw, ph))
    tx = 34 + pw + 24
    body.append(text(tx, 76, "About me", 13, "#7A5C3A", weight=700))
    body.append(text(tx, 108, "Zainul Arkaan", 24, INK, weight=700, font=SANS))
    body.append(text(tx, 136, "Alinsi", 24, INK, weight=700, font=SANS))
    body.append(text(tx, 168, "Full-stack developer", 14, "#3A5A1E", weight=700))
    body.append(text(tx, 188, "Student @ IDN Boarding School", 13, INK))
    for i, (k, v) in enumerate(FACTS):
        y = 222 + i * 22
        body.append(text(tx, y, f"{k}:", 13, "#7A5C3A", weight=700) + text(tx + 92, y, v, 13, INK))
    for i, ln in enumerate(BLURB):
        body.append(text(34, 336 + i * 24, ln, 15, INK, font=SANS))
    body.append(text(w - 36, h - 30, "— signed by zainul", 12.5, "#7A5C3A", "end"))
    return svg(w, h, "".join(body), label="About Zainul Arkaan Alinsi: " + " ".join(BLURB))


# ------------------------------------------------------------------ inventory
INV_CSS = ""


def island_img():
    """A tiny floating island for the inventory's preview box."""
    img = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    k = 30
    cam = mc.Cam(150, 66, (k * .87, k * .5), (-k * .87, k * .5), k)
    plan = [(u, v) for u in range(3) for v in range(3)]
    for u, v in plan:
        if (u + v) >= 1:
            cam.block(img, u, v, -2, "stone")
    for u, v in plan:
        cam.block(img, u, v, -1, "dirt")
    for u, v in plan:
        cam.block(img, u, v, 0, "grass")
    for z in range(1, 4):
        cam.block(img, 0, 0, z, "log")
    for u in range(-1, 2):
        for v in range(-1, 2):
            cam.block(img, u, v, 4, "leaves")
    cam.block(img, 0, 0, 5, "leaves")
    cam.block(img, 2, 1, 1, "bookshelf")
    cam.block(img, 1, 2, 1, "planks")
    return img


def inventory():
    w, h = HALF, CARD_H
    s, gx = 54, (HALF - 9 * 54) / 2
    out = [window(2, 2, w - 4, h - 4)]
    # top: preview box with the island, and a 2x2 crafting grid
    out.append(inset(gx, 22, 196, 186, "#000000"))
    out.append(rect(gx + 2, 24, 192, 182, "#1B2238"))
    for i in range(16):
        out.append(rect(gx + 12 + (i * 53) % 176, 32 + (i * 37) % 120, 2, 2, "#FFFFFF", .5))
    out.append(mc.image(mc.png_uri(island_img(), 96), gx + 8, 26, 180, 180))
    cx, cy = gx + 250, 56
    out.append(label(cx, 42, "Crafting"))
    recipe = ["laravel", "nextdotjs", "tailwindcss", "mysql"]
    for i, slug in enumerate(recipe):
        x, y = cx + (i % 2) * s, cy + (i // 2) * s
        out.append(slot(x, y, s))
        out.append(item(slug, x + 11, y + 11, 32))
    ax = cx + 2 * s + 16
    out.append(f'<path d="M{ax} {cy + s - 6}h28v-10l18 16-18 16v-10h-28z" fill="#8B8B8B"/>')
    rx = ax + 62
    out.append(slot(rx - 6, cy + s - 33, s + 12))
    out.append(mc.image(mc.png_uri(mc.icon("bookshelf", 96)), rx + 4, cy + s - 22, 44, 44))
    out.append(text(rx + s / 2, cy + s + 50, "full-stack app", 12, LABEL, "middle", 700))
    # main grid 9x3, then the hotbar
    out.append(label(gx, 238, "Inventory"))
    items = [(slug, lab, cat) for cat, its in STACK.items() for slug, lab in its]
    pos = []
    for i in range(27):
        x, y = gx + (i % 9) * s, 248 + (i // 9) * s
        out.append(slot(x, y, s))
        if i < len(items):
            out.append(item(items[i][0], x + 11, y + 11, 32))
            pos.append((x, y, items[i]))
    hot = ["laravel", "nextdotjs", "php", "typescript", "react", "tailwindcss", "flutter", "mysql", "git"]
    hy = 248 + 3 * s + 12
    for i, slug in enumerate(hot):
        x = gx + i * s
        out.append(slot(x, hy, s))
        out.append(item(slug, x + 11, hy + 11, 32))
    out.append(text(gx + 9 * s, 238, f"{len(items)} items", 12, LABEL, "end"))
    # cursor + tooltip walking the grid
    n, step = len(pos), 1.1
    dur = n * step
    for i, (x, y, (slug, lab, cat)) in enumerate(pos):
        vals = "1;0" if i == 0 else "0;1;0"
        kt = f"0;{1 / n:.4f}" if i == 0 else f"0;{i / n:.4f};{(i + 1) / n:.4f}"
        tw_ = max(len(lab) * 9.2, len(CATEGORY[cat]) * 7.4) + 26
        tx = min(x + s - 6, w - 10 - tw_)
        ty = y - 34
        g = (rect(x + 2, y + 2, s - 4, s - 4, "#FFFFFF", .45)
             + tooltip(tx, ty, tw_, 46)
             + mc_text(tx + 12, ty + 20, lab, 14, "#FFFFFF", weight=700)
             + text(tx + 12, ty + 37, CATEGORY[cat], 11.5, "#5555FF", extra=' font-style="italic"'))
        out.append(f'<g opacity="{1 if i == 0 else 0}">{g}<animate attributeName="opacity" values="{vals}"'
                   f' keyTimes="{kt}" calcMode="discrete" dur="{dur:.1f}s" repeatCount="indefinite"/></g>')
    hv = ";".join(f"{gx + i * s:.0f} {hy}" for i in range(9))
    out.append(f'<g>{selector(0, 0, s)}<animateTransform attributeName="transform" type="translate"'
               f' values="{hv}" calcMode="discrete" dur="{9 * 1.4:.1f}s" repeatCount="indefinite"/></g>')
    return svg(w, h, "".join(out), css=INV_CSS,
               label="Inventory: " + ", ".join(lab for _, lab, _ in items))


# ----------------------------------------------------------- news header, footer
def news_header(stamp="", count=0):
    h = 120
    body = [mc.image(mc.png_uri(dirt_bg(W, h), 32), 0, 0, W, h),
            rect(0, 0, W, h, "#000000", .15)]
    t = "DEV NEWS"
    body.append(mc_pixel(t, (W - pixel_width(t, 5)) / 2, 22, 5))
    sub = (f"{count} stories, pulled straight from the source feeds" if count else
           "pulled straight from the source feeds, newest first")
    body.append(mc_text(W / 2, 88, sub + (f" · refreshed {stamp}" if stamp else ""), 13, GRAY, "middle"))
    body.append('<rect x="1" y="1" width="1198" height="118" fill="none" stroke="#000" stroke-width="2"/>')
    return svg(W, h, "".join(body), label="Developer news, refreshed automatically")


FOOT_CSS = ("@keyframes save{0%{transform:scaleX(0)}70%,100%{transform:scaleX(1)}}"
            ".save{animation:save 6s ease-out infinite;transform-box:fill-box;transform-origin:left}")


def footer():
    h = 150
    body = [mc.image(mc.png_uri(dirt_bg(W, h), 32), 0, 0, W, h)]
    t = "THANKS FOR STOPPING BY"
    body.append(mc_pixel(t, (W - pixel_width(t, 4)) / 2, 28, 4))
    body.append(mc_text(W / 2, 86, "Saving world...", 15, "#FFFFFF", "middle"))
    bw = 400
    body.append(rect((W - bw) / 2 - 2, 98, bw + 4, 10, "#000000"))
    body.append(rect((W - bw) / 2, 100, bw, 6, "#808080"))
    body.append(rect((W - bw) / 2, 100, bw, 6, "#80FF80", extra=' class="save"'))
    body.append(mc_text(W / 2, 134, "every panel on this page is rendered by the python scripts in this repo",
                        12, GRAY, "middle"))
    body.append('<rect x="1" y="1" width="1198" height="148" fill="none" stroke="#000" stroke-width="2"/>')
    return svg(W, h, "".join(body), css=FOOT_CSS, label="Thanks for stopping by")


# ------------------------------------------------------------------ placeholder
def loading(w, h, what):
    """Shown only until the first real sync writes the panel."""
    body = [mc.image(mc.png_uri(dirt_bg(w, h), 32), 0, 0, w, h)]
    body.append(mc_text(w / 2, h / 2 - 8, "Loading terrain...", 18, "#FFFFFF", "middle", 700))
    body.append(mc_text(w / 2, h / 2 + 20, f"{what} appears after the next GitHub Actions run", 12.5, GRAY,
                        "middle"))
    body.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="none" stroke="#000" stroke-width="2"/>')
    return svg(w, h, "".join(body), label=f"{what}: waiting for the first sync")


# ----------------------------------------------------------------------- build
def build():
    ASSETS.mkdir(parents=True, exist_ok=True)
    made = {}
    made["title.svg"] = title()
    for slug, lab, _ in LINKS:
        made[f"btn-{slug}.svg"] = button(slug, lab, 780 if slug == "github" else 380)
    made["book.svg"] = book()
    made["inventory.svg"] = inventory()
    made["footer.svg"] = footer()
    if not (ASSETS / "news.svg").exists() or "--force-news" in sys.argv:
        made["news.svg"] = news_header()
    for name, (w, h, what) in {"stats.svg": (HALF, CARD_H, "Player statistics"),
                               "chat.svg": (HALF, CARD_H, "The commit log"),
                               "world-dark.svg": (W, 560, "The contribution world"),
                               "world-light.svg": (W, 560, "The contribution world")}.items():
        if not (ASSETS / name).exists():
            made[name] = loading(w, h, what)
    for name, body in made.items():
        (ASSETS / name).write_text(body, encoding="utf-8")
    return list(made)


if __name__ == "__main__":
    for n in build():
        print("wrote", n)
