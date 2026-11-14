"""Static panels: link buttons, the about terminal, the stack inventory, section
headers and the footer. No network, no API — run it any time:

    python scripts/build_panels.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ASSETS, SANS, THEMES, Iso, glass, line, mix, pixel_text, pixel_width, poly,
                   rect, rgb, shade, svg_doc, text, ticks)

W, PAD = 1200, 34
ICONS = json.loads((ASSETS.parent / "scripts" / "icons.json").read_text())
PATHS, STACK = ICONS["paths"], ICONS["stack"]

ROW_ACCENT = {"languages": "blue", "frameworks": "violet", "tools": "amber"}
LINKS = [("instagram", "Instagram", "red"), ("linkedin", "LinkedIn", "blue"),
         ("youtube", "YouTube", "red"), ("gmail", "Email", "amber")]


def icon(slug, x, y, size, fill, op=1.0):
    k = size / 24
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="{fill}"'
            f'{f" opacity={chr(34)}{op}{chr(34)}" if op < 1 else ""}>'
            f'<path d="{PATHS[slug]}"/></g>')


def chrome(t, x, y, w, h, title, right="", accent="blue", uid="pane", glows=None):
    g = glows if glows is not None else [(.08, .15, w * .28, accent), (.92, .85, w * .24, "blue")]
    out = [glass(uid, x, y, w, h, t, r=16, glows=g),
           line(x, y + 30, x + w, y + 30, t["line"], 1, .9)]
    for i, c in enumerate((t["red"], t["amber"], t["green"])):
        out.append(rect(x + 14 + i * 13, y + 12, 7, 7, fill=c, op=.85))
    out.append(text(x + 62, y + 20, title, 11.5, t["muted"]))
    if right:
        out.append(text(x + w - 14, y + 20, right, 11.5, t["muted"], anchor="end"))
    out.append(ticks(x + 7, y + 37, w - 14, h - 50, t["ink"], 8, 1, .18))
    return "".join(out)


def heading(t, label, x, y, sub=None, px=3):
    out = [pixel_text(label, x, y, px, t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"])]
    if sub:
        out.append(text(x, y + px * 7 + 18, sub, 11.5, t["muted"]))
    return "".join(out)


# --------------------------------------------------------------- hotbar slots
# Each link is one inventory slot with a Minecraft-style tooltip underneath. The
# white selection frame walks across the four slots like scrolling a hotbar; each
# slot owns its own delay, so they stay in step without sharing one image.
SLOT = 76
SLOT_W, SLOT_H = 150, 128
SLOT_CSS = ("@keyframes sel{0%{opacity:1}23%{opacity:0}100%{opacity:0}}"
            ".sel{opacity:0;animation:sel 6s steps(1) infinite}"
            "@keyframes lift{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}"
            ".lift{animation:lift 6s steps(2) infinite}"
            "@media (prefers-reduced-motion:reduce){.sel,.lift{animation:none}}")
TIP_BG, TIP_INK = "#140F1E", "#FFFFFF"


def link_chip(t, slug, label, accent, idx=0):
    from build_editorial import link
    return link(slug, label, idx)


def _old_link_chip(t, slug, label, accent, idx=0):
    dark = t["px_shadow"] > .3
    face = mix(t["bg"], t["ink"], .14 if dark else .07)
    recess_lo = mix(face, "#000000", .55 if dark else .20)        # top and left: in shadow
    recess_hi = mix(face, "#FFFFFF", .22 if dark else .90)        # bottom and right: lit
    edge = shade(face, .25)
    sx, sy = (SLOT_W - SLOT) // 2, 10
    delay = f"{idx * 1.5:.1f}s"

    slot = [rect(sx - 2, sy - 2, SLOT + 4, SLOT + 4, fill=edge),
            rect(sx, sy, SLOT, SLOT, fill=face),
            rect(sx, sy, SLOT, 4, fill=recess_lo), rect(sx, sy, 4, SLOT, fill=recess_lo),
            rect(sx, sy + SLOT - 4, SLOT, 4, fill=recess_hi), rect(sx + SLOT - 4, sy, 4, SLOT, fill=recess_hi),
            rect(sx + SLOT - 4, sy, 4, 4, fill=face), rect(sx, sy + SLOT - 4, 4, 4, fill=face)]
    ix, iy = (SLOT_W - 38) / 2, sy + (SLOT - 38) / 2
    item = (f'<g class="lift" style="animation-delay:{delay}">'
            + icon(slug, ix + 3, iy + 3, 38, t["shadow"], .38 if dark else .16)      # item shadow
            + icon(slug, ix, iy, 38, brand(t, slug, face)) + "</g>")

    frame = (f'<g class="sel" style="animation-delay:{delay}" fill="none">'
             f'<rect x="{sx - 7}" y="{sy - 7}" width="{SLOT + 14}" height="{SLOT + 14}" stroke="#000" stroke-width="5" opacity=".75"/>'
             f'<rect x="{sx - 6}" y="{sy - 6}" width="{SLOT + 12}" height="{SLOT + 12}" stroke="{t["ink"]}" stroke-width="3"/>'
             + "".join(rect(cx_, cy_, 6, 6, fill=t[accent]) for cx_, cy_ in
                       ((sx - 9, sy - 9), (sx + SLOT + 3, sy - 9), (sx - 9, sy + SLOT + 3), (sx + SLOT + 3, sy + SLOT + 3)))
             + "</g>")

    px = 2
    tw = pixel_width(label, px) + 22
    tx, ty = (SLOT_W - tw) / 2, sy + SLOT + 12
    tip = [rect(tx, ty, tw, 26, fill=t[accent]),
           rect(tx + 2, ty + 2, tw - 4, 22, fill=TIP_BG),
           pixel_text(label, tx + 11, ty + 6, px, TIP_INK, shadow="#000000", shadow_op=.6)]

    body = ['<g shape-rendering="crispEdges">', rect(0, 0, SLOT_W, SLOT_H, fill=t["bg"]),
            "".join(slot), item, frame, "".join(tip), "</g>"]
    return svg_doc(SLOT_W, SLOT_H, "".join(body), label=label, css=SLOT_CSS)


# ---------------------------------------------------------------- about panel
# Plain words, the ones the bio already uses. No invented status lines.
NAME = "Zainul Arkaan Alinsi"
ROLE = "Full-stack developer · Student at IDN Boarding School"
BLURB = [
    "I build full-stack web apps with PHP, Laravel, Next.js and",
    "Tailwind CSS, and I'm learning Flutter so I can take the same",
    "work to mobile. I like efficient code that people actually use.",
]
FACTS = [("Building", "Web apps"), ("Learning", "Flutter, Dart"),
         ("Editor", "VS Code"), ("Timezone", "WIB, UTC+7")]

ABOUT_CSS = (
    "@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}"
    "@keyframes sh{0%,100%{transform:scale(1)}50%{transform:scale(.88)}}"
    "@keyframes bob{0%,100%{opacity:1}50%{opacity:.2}}"
    ".fl{animation:fl 4.5s ease-in-out infinite}"
    ".sh{animation:sh 4.5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
    ".bob{animation:bob 1.1s steps(1) infinite}"
    "@media (prefers-reduced-motion:reduce){.fl,.sh,.bob{animation:none}}")


def island(t, cx, cy, k):
    """A floating voxel island with a desk on it. Painter's order, far to near."""
    iso = Iso(cx, cy, k)
    grass, leaf = t["green"], mix(t["green"], t["bg"], .18)
    dirt = mix(t["bg"], t["amber"], .52)
    stone = mix(t["bg"], t["ink"], .30)
    wood = mix(t["bg"], t["amber"], .78)
    metal = mix(t["bg"], t["ink"], .22)
    out = [iso.box(.7, .7, -2.1, 1.6, 1.6, .9, stone),
           iso.box(.3, .3, -1.2, 2.4, 2.4, .8, dirt),
           iso.box(0, 0, -.4, 3, 3, .4, dirt, top=grass),
           poly([iso.p(0, 3, 0), iso.p(3, 3, 0), iso.p(3, 3, -.14), iso.p(0, 3, -.14)], shade(grass, .72)),
           poly([iso.p(3, 0, 0), iso.p(3, 3, 0), iso.p(3, 3, -.14), iso.p(3, 0, -.14)], shade(grass, .52))]
    for (u, v) in ((.3, .4), (2.5, 2.3), (.4, 2.4), (1.5, 2.65), (2.65, 1.5)):
        out.append(poly([iso.p(u, v), iso.p(u + .2, v), iso.p(u + .2, v + .2), iso.p(u, v + .2)],
                        shade(grass, 1.15)))
    out += [iso.box(2.3, .4, 0, .3, .3, 1.1, wood),
            iso.box(1.9, 0, 1.0, 1.1, 1.1, .9, leaf),
            iso.box(2.1, .2, 1.9, .7, .7, .45, shade(leaf, 1.08))]
    for u, v in ((.35, 1.05), (1.95, 1.05), (.35, 1.9), (1.95, 1.9)):
        out.append(iso.box(u, v, 0, .14, .14, .62, wood))
    out += [iso.box(.25, .95, .62, 1.95, 1.15, .12, wood),
            iso.box(1.0, 1.15, .74, .42, .3, .06, metal),
            iso.box(1.14, 1.22, .8, .14, .1, .36, metal),
            iso.box(.45, 1.1, 1.08, 1.55, .12, .95, metal)]
    m = iso.face_matrix("left", .45, 1.1, 1.08, 1.55, .12, .95)
    code = [(.10, .16, .28, "violet"), (.42, .16, .22, "ink"), (.16, .31, .40, "blue"),
            (.16, .46, .24, "green"), (.44, .46, .30, "amber"), (.10, .61, .20, "violet"),
            (.16, .76, .42, "muted")]
    lines = "".join(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height=".07" fill="{t[c]}"/>'
                    for x, y, w, c in code)
    out.append(f'<g transform="{m}"><rect x=".05" y=".07" width=".9" height=".86" fill="#0B0F14"/>{lines}'
               f'<rect class="bob" x=".62" y=".74" width=".04" height=".11" fill="{t["green"]}"/></g>')
    out += [iso.box(.6, 1.55, .74, 1.0, .32, .05, mix(t["bg"], t["ink"], .40)),
            iso.box(1.75, 1.62, .74, .24, .24, .24, t["red"])]
    return "".join(out)


def about(t):
    x0 = PAD + 36
    h = 318
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "about", "", "blue", "about",
                   glows=[(.08, .2, 300, "blue"), (.82, .55, 300, "green")]),
            heading(t, "ABOUT ME", x0, PAD + 56, px=3),
            text(x0, PAD + 120, NAME, 24, t["ink"], weight=700, font=SANS),
            text(x0, PAD + 146, ROLE, 14, t["muted"], font=SANS)]
    for i, ln in enumerate(BLURB):
        body.append(text(x0, PAD + 186 + i * 24, ln, 15, t["ink"], font=SANS))
    fy = PAD + h - 44
    body.append(line(x0, fy - 26, x0 + 610, fy - 26, t["line"], 1))
    for i, (k, v) in enumerate(FACTS):
        fx = x0 + i * 156
        body.append(text(fx, fy, k.upper(), 10.5, t["muted"], weight=600, font=SANS, ls="1.2"))
        body.append(text(fx, fy + 20, v, 14, t["ink"], weight=500, font=SANS))
    # the one 3D object on the panel, with room to breathe
    ix, iy = W - PAD - 250, PAD + 96
    body.append(f'<ellipse class="sh" cx="{ix:.1f}" cy="{PAD + h - 24:.1f}" rx="92" ry="11"'
                f' fill="{t["shadow"]}" opacity="{.32 if t["px_shadow"] > .3 else .10}"/>')
    body.append(f'<g class="fl">{island(t, ix, iy, 31)}</g>')
    return svg_doc(W, h + PAD * 2, "".join(body), css=ABOUT_CSS,
                   label="About Zainul Arkaan Alinsi: " + " ".join(BLURB))


# ------------------------------------------------------------------ tech stack
# Each tool is a keycap: the logo upright in its own brand colour, so it reads at
# a glance. Colours are nudged toward the ink when they would vanish on the key.
BRAND = {
    "php": "#777BB4", "typescript": "#3178C6", "javascript": "#F7DF1E", "dart": "#0175C2",
    "openjdk": "#E76F00", "html5": "#E34F26", "css": "#663399", "laravel": "#FF2D20",
    "nextdotjs": None, "react": "#61DAFB", "vuedotjs": "#4FC08D", "tailwindcss": "#06B6D4",
    "alpinedotjs": "#8BC0D0", "flutter": "#02569B", "nodedotjs": "#5FA04E", "mysql": "#4479A1",
    "sqlite": "#003B57", "firebase": "#DD2C00", "vercel": None, "git": "#F05032",
    "github": None, "figma": "#F24E1E", "postman": "#FF6C37",
}
BADGES = {"javascript"}
KEY_W, KEY_H, LIP, GAP = 106, 82, 6, 11


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb(c))
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def brand(t, slug, face):
    c = BRAND.get(slug) or t["ink"]
    if slug in BADGES:                  # the logo is a filled tile: its colour is the logo
        return c
    k = 0
    while contrast(c, face) < 3.2 and k < 10:
        c = mix(c, t["ink"], .2)
        k += 1
    return c


def keycap(t, x, y, slug, label):
    dark = t["px_shadow"] > .3
    face = mix(t["bg"], t["ink"], .075 if dark else .0)
    side = mix(t["bg"], t["ink"], .03 if dark else .10)
    edge = mix(t["bg"], t["ink"], .16 if dark else .18)
    out = [rect(x, y + LIP, KEY_W, KEY_H, fill=t["shadow"], r=11, op=.35 if dark else .06),
           rect(x, y + LIP, KEY_W, KEY_H - 2, fill=side, r=11, stroke=edge),
           rect(x, y, KEY_W, KEY_H - LIP, fill=face, r=10, stroke=edge),
           f'<path d="M{x + 10} {y + 1.2}H{x + KEY_W - 10}" stroke="#FFFFFF" stroke-width="1"'
           f' opacity="{.10 if dark else .9}"/>',
           icon(slug, x + (KEY_W - 28) / 2, y + 12, 28, brand(t, slug, face)),
           text(x + KEY_W / 2, y + KEY_H - LIP - 12, label, 12.5, t["ink"], anchor="middle",
                weight=500, font=SANS)]
    return "".join(out)


def stack_panel(t):
    x0 = PAD + 36
    kx = x0 + 136
    top = PAD + 104
    row = KEY_H + 30
    body_rows = []
    for r, (name, items) in enumerate(STACK.items()):
        y = top + r * row
        body_rows.append(text(x0, y + 44, name.capitalize(), 15, t["ink"], weight=600, font=SANS))
        body_rows.append(text(x0, y + 64, f"{len(items)} tools", 12, t["muted"], font=SANS))
        for i, (slug, label) in enumerate(items):
            body_rows.append(keycap(t, kx + i * (KEY_W + GAP), y, slug, label))
    h = int(top + row * len(STACK) - PAD + 4)
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "stack", "", "violet", "stack",
                   glows=[(.10, .25, 300, "violet"), (.90, .80, 300, "blue")]),
            heading(t, "TECH STACK", x0, PAD + 56, px=3),
            "".join(body_rows)]
    return svg_doc(W, h + PAD * 2, "".join(body), label="Tech stack: " + ", ".join(
        lab for items in STACK.values() for _, lab in items))


# ----------------------------------------------------------------- news header
def news_header(t, stamp="", count=0):
    from build_editorial import news
    return news(stamp, count)


def _old_news_header(t, stamp="", count=0):
    h = 116
    body = [rect(0, 0, W, h + PAD, fill=t["bg"]),
            chrome(t, PAD, 8, W - PAD * 2, h, "~/feed --topic programming",
                   f"refreshed {stamp}" if stamp else "", "red", "news",
                   glows=[(.06, .30, 300, "red")]),
            heading(t, "DEV NEWS", PAD + 28, 64, px=3,
                    sub=(f"{count} stories pulled straight from the source feeds, newest first" if count
                         else "pulled straight from the source feeds, newest first")),
            icon("rss", W - PAD - 54, 62, 24, t["red"], .85)]
    return svg_doc(W, h + PAD, "".join(body), label="Developer news, refreshed automatically")


# ---------------------------------------------------------------------- footer
def footer(t):
    h = 84
    msg, px = "THANKS FOR STOPPING BY", 3
    body = [rect(0, 0, W, h + 16, fill=t["bg"]),
            glass("foot", PAD, 8, W - PAD * 2, h, t, r=14),
            pixel_text(msg, (W - pixel_width(msg, px)) / 2, 30, px, t["ink"],
                       shadow=t["shadow"], shadow_op=t["px_shadow"]),
            text(W / 2, 72, "every panel on this page is generated by the scripts in this repo",
                 11, t["muted"], anchor="middle")]
    for i, k in enumerate(("green", "blue", "amber", "violet", "red")):
        body.append(rect(PAD + 24 + i * 14, 38, 9, 9, fill=t[k], op=.85))
        body.append(rect(W - PAD - 33 - i * 14, 38, 9, 9, fill=t[k], op=.85))
    return svg_doc(W, h + 16, "".join(body), label="Thanks for stopping by")


# ----------------------------------------------------------------------- build
def build():
    ASSETS.mkdir(parents=True, exist_ok=True)
    made = []
    for name, tokens in THEMES.items():
        for idx, (slug, label, accent) in enumerate(LINKS if name == "dark" else ()):
            p = ASSETS / f"link-{slug}-{name}.svg"
            p.write_text(link_chip(tokens, slug, label, accent, idx), encoding="utf-8")
            made.append(p.name)
        p = ASSETS / f"news-{name}.svg"
        if not p.exists():                     # build_news.py owns this once it has real counts
            p.write_text(news_header(tokens), encoding="utf-8")
            made.append(p.name)
    from build_editorial import build_static       # about, stack, footer: monochrome editorial
    made += build_static()
    return made


if __name__ == "__main__":
    for n in build():
        print("wrote", n)
