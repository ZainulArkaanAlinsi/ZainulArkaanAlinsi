"""Static panels: hotbar link slots, the about window, the stack inventory, the
news header and the footer. No network, no API — run it any time:

    python scripts/build_panels.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ASSETS, SANS, SPLASH_CSS, THEMES, Iso, mix, panel, pixel_text, pixel_width, rect, rgb,
                   selector, shade, slot, splash, svg_doc, text, window)

W = 1200
X0, WW = 4, W - 8            # panels sit 4px in so their 2px outline is never clipped
ICONS = json.loads((ASSETS.parent / "scripts" / "icons.json").read_text())
PATHS, STACK = ICONS["paths"], ICONS["stack"]

LINKS = [("instagram", "Instagram", "@zainarilbre", "red"),
         ("linkedin", "LinkedIn", "zainul-arkaan", "blue"),
         ("youtube", "YouTube", "@zainarilbre", "red"),
         ("gmail", "Email", "say hello", "gold")]

BLINK_CSS = ("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
             ".blink{animation:blink 1.05s steps(1) infinite}")


def icon(slug, x, y, size, fill, op=1.0):
    k = size / 24
    o = f' opacity="{op}"' if op < 1 else ""
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="{fill}"{o}>'
            f'<path d="{PATHS[slug]}"/></g>')


def heading(t, label, x, y, px=4, colour=None):
    return pixel_text(label, x, y, px, colour or t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"])


def prompt(t, x, y, cmd, size=12):
    """A terminal prompt line with a blinking block cursor after it."""
    w = len(cmd) * size * .6
    return (text(x, y, "$", size, t["green"], weight=700)
            + text(x + size * 1.2, y, cmd, size, t["muted"])
            + rect(x + size * 1.2 + w + 4, y - size + 2, size * .55, size, fill=t["green"], extra=' class="blink"'))


# ---------------------------------------------------------------- brand colour
BRAND = {
    "php": "#777BB4", "typescript": "#3178C6", "javascript": "#F7DF1E", "dart": "#0175C2",
    "openjdk": "#E76F00", "html5": "#E34F26", "css": "#663399", "laravel": "#FF2D20",
    "nextdotjs": None, "react": "#61DAFB", "vuedotjs": "#4FC08D", "tailwindcss": "#06B6D4",
    "alpinedotjs": "#8BC0D0", "flutter": "#02569B", "nodedotjs": "#5FA04E", "mysql": "#4479A1",
    "sqlite": "#003B57", "firebase": "#DD2C00", "vercel": None, "git": "#F05032",
    "github": None, "figma": "#F24E1E", "postman": "#FF6C37",
    "instagram": "#E4405F", "linkedin": "#0A66C2", "youtube": "#FF0000", "gmail": "#EA4335",
}
BADGES = {"javascript"}


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
    """The logo in its own colour, nudged toward the ink until it clears 3:1 on
    the slot it sits in."""
    c = BRAND.get(slug) or t["ink"]
    if slug in BADGES:
        return c
    k = 0
    while contrast(c, face) < 3.0 and k < 10:
        c = mix(c, t["ink"], .2)
        k += 1
    return c


# ------------------------------------------------------------- hotbar link slots
def link_chip(t, slug, label, sub, key):
    w, h = 214, 64
    s = 48
    body = [panel(4, 4, w - 8, h - 8, t),
            slot(12, 8, s, s, t),
            icon(slug, 12 + (s - 26) / 2, 8 + (s - 26) / 2, 26, brand(t, slug, t["slot"])),
            text(12 + s - 3, 8 + s - 4, str(key), 11, t["ink"], anchor="end", weight=700),
            pixel_text(label, 72, 17, 2, t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"]),
            text(72, 46, sub, 11.5, t["muted"])]
    return svg_doc(w, h, "".join(body), label=f"{label}: {sub}")


# ---------------------------------------------------------------- about window
# Plain words, the ones the bio already uses. No invented status lines.
NAME = "Zainul Arkaan Alinsi"
ROLE = "FULL-STACK DEVELOPER · IDN BOARDING SCHOOL"
BLURB = [
    "I build full-stack web apps with PHP, Laravel, Next.js and",
    "Tailwind CSS, and I'm learning Flutter so I can take the same",
    "work to mobile. I like efficient code that people actually use.",
]
FACTS = [("Building", "Web apps", "green"), ("Learning", "Flutter, Dart", "blue"),
         ("Editor", "VS Code", "violet"), ("Timezone", "WIB, UTC+7", "gold")]

ABOUT_CSS = (
    "@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}"
    "@keyframes sh{0%,100%{transform:scale(1)}50%{transform:scale(.86)}}"
    "@keyframes bob{0%,100%{opacity:1}50%{opacity:.15}}"
    ".fl{animation:fl 4.5s ease-in-out infinite}"
    ".sh{animation:sh 4.5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
    ".bob{animation:bob 1.1s steps(1) infinite}" + BLINK_CSS + SPLASH_CSS)


def island(t, cx, cy, k):
    """A floating voxel island with a desk on it. Painter's order, far to near."""
    iso = Iso(cx, cy, k)
    dark = t["dark"]
    grass = t["green"] if dark else mix(t["green"], "#FFFFFF", .15)
    leaf = shade(grass, .82)
    dirt = "#8A5A33" if dark else "#7A4E2B"
    stone = "#6B6F78" if dark else "#7E7E7E"
    wood = "#B88A4E"
    metal = "#4A4F5A" if dark else "#5B5B5B"
    out = [iso.box(.7, .7, -2.1, 1.6, 1.6, .9, stone),
           iso.box(.3, .3, -1.2, 2.4, 2.4, .8, dirt),
           iso.box(0, 0, -.4, 3, 3, .4, dirt, top=grass)]
    for (u, v) in ((.3, .4), (2.5, 2.3), (.4, 2.4), (1.5, 2.65), (2.65, 1.5)):
        out.append(iso.box(u, v, 0, .2, .2, .06, shade(grass, 1.18)))
    out += [iso.box(2.3, .4, 0, .3, .3, 1.1, shade(wood, .7)),
            iso.box(1.9, 0, 1.0, 1.1, 1.1, .9, leaf),
            iso.box(2.1, .2, 1.9, .7, .7, .45, shade(leaf, 1.1))]
    for u, v in ((.35, 1.05), (1.95, 1.05), (.35, 1.9), (1.95, 1.9)):
        out.append(iso.box(u, v, 0, .14, .14, .62, wood))
    out += [iso.box(.25, .95, .62, 1.95, 1.15, .12, wood),
            iso.box(1.0, 1.15, .74, .42, .3, .06, metal),
            iso.box(1.14, 1.22, .8, .14, .1, .36, metal),
            iso.box(.45, 1.1, 1.08, 1.55, .12, .95, metal)]
    m = iso.face_matrix("left", .45, 1.1, 1.08, 1.55, .12, .95)
    code = [(.10, .16, .28, "violet"), (.42, .16, .22, "ink"), (.16, .31, .40, "blue"),
            (.16, .46, .24, "green"), (.44, .46, .30, "gold"), (.10, .61, .20, "violet"),
            (.16, .76, .42, "diamond")]
    lines = "".join(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height=".07" fill="{THEMES["dark"][c]}"/>'
                    for x, y, w, c in code)
    out.append(f'<g transform="{m}"><rect x=".05" y=".07" width=".9" height=".86" fill="#0B0F14"/>{lines}'
               f'<rect class="bob" x=".62" y=".74" width=".04" height=".11" fill="{THEMES["dark"]["green"]}"/></g>')
    out += [iso.box(.6, 1.55, .74, 1.0, .32, .05, mix(metal, "#000000", .2)),
            iso.box(1.75, 1.62, .74, .24, .24, .24, t["red"])]
    return "".join(out)


def about(t):
    h = 368
    x = X0 + 40
    body = [window(X0, 4, WW, h, t, "~/about.md", "zainul@idn:~", "green"),
            prompt(t, x, 64, "whoami"),
            heading(t, "ABOUT ME", x, 82, px=5),
            text(x, 150, NAME, 27, t["ink"], weight=700, font=SANS),
            pixel_text(ROLE, x, 170, 2, t["green"])]
    for i, ln in enumerate(BLURB):
        body.append(text(x, 218 + i * 24, ln, 15, t["ink"], font=SANS))
    # facts as four inventory slots
    fy = h - 66
    for i, (k, v, c) in enumerate(FACTS):
        fx = x + i * 160
        body.append(slot(fx, fy, 148, 50, t))
        body.append(rect(fx + 2, fy + 2, 4, 46, fill=t[c]))
        body.append(text(fx + 16, fy + 20, k.upper(), 10, t["muted"], weight=700, ls="1.4"))
        body.append(text(fx + 16, fy + 39, v, 14, t["ink"], weight=600, font=SANS))
    # the one 3D object, in a sunken viewport, with a splash on top
    vx, vy, vw, vh = W - X0 - 372, 48, 340, h - 64
    body.append(slot(vx, vy, vw, vh, t, fill=mix(t["slot"], t["blue"], .10) if t["dark"] else "#9DB6DA"))
    for i in range(14):                                   # stars / dust in the viewport
        sx, sy = vx + 18 + (i * 97) % (vw - 36), vy + 16 + (i * 53) % 110
        body.append(rect(sx, sy, 2 + i % 2, 2 + i % 2, fill=t["ink"], op=.25 + (i % 3) * .15,
                         extra=' class="bob"' if i % 4 == 0 else ""))
    ix = vx + vw / 2 - 2
    body.append(f'<ellipse class="sh" cx="{ix:.1f}" cy="{vy + vh - 26:.1f}" rx="88" ry="9"'
                f' fill="#000000" opacity="{.35 if t["dark"] else .18}"/>')
    body.append(f'<g class="fl">{island(t, ix, vy + 70, 30)}</g>')
    body.append(splash(vx + 96, vy + 40, "Laravel + Next.js!", t, 14, -14))
    return svg_doc(W, h + 8, "".join(body), css=ABOUT_CSS,
                   label="About Zainul Arkaan Alinsi: " + " ".join(BLURB))


# --------------------------------------------------------------- stack inventory
SLOT, SGAP = 72, 14


def stack_panel(t):
    x = X0 + 40
    gx = x + 196
    top = 128
    row = SLOT + 40
    body = [prompt(t, x, 64, "ls ~/inventory --all"),
            heading(t, "INVENTORY", x, 82, px=5),
            text(W - X0 - 40, 106, f"{sum(len(v) for v in STACK.values())} items equipped", 12,
                 t["muted"], anchor="end")]
    order = []
    for r, (name, items) in enumerate(STACK.items()):
        y = top + r * row
        body.append(pixel_text(name.upper(), x, y + 22, 2, t["ink"], shadow=t["shadow"],
                               shadow_op=t["px_shadow"]))
        body.append(text(x, y + 56, f"{len(items)} items", 12, t["muted"]))
        for i, (slug, label) in enumerate(items):
            sx = gx + i * (SLOT + SGAP)
            order.append((sx, y))
            body.append(slot(sx, y, SLOT, SLOT, t))
            body.append(icon(slug, sx + (SLOT - 34) / 2, y + (SLOT - 34) / 2, 34, brand(t, slug, t["slot"])))
            body.append(text(sx + SLOT / 2, y + SLOT + 18, label, 11.5, t["ink"], anchor="middle", weight=500,
                             font=SANS))
    # the selection frame hops slot to slot, like scrolling the hotbar
    vals = ";".join(f"{sx:.0f} {sy:.0f}" for sx, sy in order)
    body.append(f'<g>{selector(0, 0, SLOT, "#FFFFFF" if t["dark"] else "#FFFFFF")}'
                f'<animateTransform attributeName="transform" type="translate" values="{vals}"'
                f' calcMode="discrete" dur="{len(order) * .8:.1f}s" repeatCount="indefinite"/></g>')
    h = int(top + row * len(STACK) + 6)
    head = window(X0, 4, WW, h, t, "~/inventory", "[E] to close", "violet")
    return svg_doc(W, h + 8, head + "".join(body), css=BLINK_CSS,
                   label="Tech stack: " + ", ".join(lab for items in STACK.values() for _, lab in items))


# ----------------------------------------------------------------- news header
def news_header(t, stamp="", count=0):
    h = 118
    x = X0 + 40
    sub = (f"{count} stories pulled straight from the source feeds, newest first" if count
           else "pulled straight from the source feeds, newest first")
    body = [window(X0, 4, WW, h, t, "~/feed --topic programming", f"refreshed {stamp}" if stamp else "", "red"),
            heading(t, "DEV NEWS", x, 52, px=4),
            text(x, 104, sub, 12, t["muted"]),
            slot(W - X0 - 92, 46, 56, 56, t),
            icon("rss", W - X0 - 92 + 14, 60, 28, brand(t, "rss", t["slot"]) if "rss" in BRAND else t["gold"])]
    return svg_doc(W, h + 8, "".join(body), css=BLINK_CSS, label="Developer news, refreshed automatically")


# ---------------------------------------------------------------------- footer
FOOT_CSS = SPLASH_CSS + ("@keyframes hop{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}"
                         ".hop{animation:hop 2.4s ease-in-out infinite}")


def grass_row(t, x, y, n, k=13):
    out = []
    dark = t["dark"]
    grass = t["green"] if dark else mix(t["green"], "#FFFFFF", .15)
    for i in range(n):
        iso = Iso(x + i * k * 2, y, k)
        top = grass if i % 3 else shade(grass, 1.12)
        body = iso.box(-.5, -.5, 0, 1, 1, 1, "#8A5A33" if dark else "#7A4E2B", top=top)
        out.append(f'<g class="hop" style="animation-delay:{-i * .3:.1f}s">{body}</g>')
    return "".join(out)


def footer(t):
    h = 112
    msg, px = "THANKS FOR STOPPING BY", 4
    body = [panel(X0, 4, WW, h, t),
            grass_row(t, X0 + 44, 54, 4),
            grass_row(t, W - X0 - 44 - 3 * 26, 54, 4),
            pixel_text(msg, (W - pixel_width(msg, px)) / 2, 30, px, t["ink"],
                       shadow=t["shadow"], shadow_op=t["px_shadow"]),
            text(W / 2, 88, "every panel on this page is drawn by the python scripts in this repo",
                 11.5, t["muted"], anchor="middle"),
            splash(W / 2 + pixel_width(msg, px) / 2 + 62, 26, "git push!", t, 14, -16)]
    return svg_doc(W, h + 8, "".join(body), css=FOOT_CSS, label="Thanks for stopping by")


# ------------------------------------------------------------------ placeholder
def loading(t, title, path, h=150):
    """Shown only until the first real sync writes the panel: says so, invents nothing."""
    msg, px = "LOADING WORLD...", 4
    body = [window(X0, 4, WW, h, t, path, "waiting for first sync", "gold"),
            pixel_text(msg, (W - pixel_width(msg, px)) / 2, 62, px, t["ink"], shadow=t["shadow"],
                       shadow_op=t["px_shadow"]),
            text(W / 2, 118, f"{title} appears after the next GitHub Actions run", 12, t["muted"], anchor="middle")]
    return svg_doc(W, h + 8, "".join(body), label=f"{title}: waiting for the first sync")


# ----------------------------------------------------------------------- build
def build():
    ASSETS.mkdir(parents=True, exist_ok=True)
    made = []
    for name, tokens in THEMES.items():
        for i, (slug, label, sub, _) in enumerate(LINKS, 1):
            p = ASSETS / f"link-{slug}-{name}.svg"
            p.write_text(link_chip(tokens, slug, label, sub, i), encoding="utf-8")
            made.append(p.name)
        for fn, base in ((about, "about"), (stack_panel, "stack"), (news_header, "news"), (footer, "footer")):
            p = ASSETS / f"{base}-{name}.svg"
            if base == "news" and p.exists() and "--force-news" not in sys.argv:
                continue                       # build_news.py owns this once it has real counts
            p.write_text(fn(tokens), encoding="utf-8")
            made.append(p.name)
        for base, title, path in (("hud", "The HUD", "~/hud"), ("log", "The commit log", "~/commits --tail -f")):
            p = ASSETS / f"{base}-{name}.svg"
            if not p.exists():                 # build_activity.py / build_log.py own these after that
                p.write_text(loading(tokens, title, path), encoding="utf-8")
                made.append(p.name)
    return made


if __name__ == "__main__":
    for n in build():
        print("wrote", n)
