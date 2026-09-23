"""Static panels: link buttons, the about terminal, the stack inventory, section
headers and the footer. No network, no API — run it any time:

    python scripts/build_panels.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ACCENTS, ASSETS, THEMES, Iso, glass, line, mix, pixel_text, pixel_width,
                   poly, rect, shade, svg_doc, text, ticks)

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


# ------------------------------------------------------------------ link chips
def link_chip(t, slug, label, accent):
    w, h = 184, 48
    body = [rect(0, 0, w, h, fill=t["bg"]),
            glass(f"lk{slug}", 2, 2, w - 4, h - 4, t, r=12, glows=[(.18, .5, 52, accent)]),
            rect(14, 15, 3, 18, fill=t[accent]),
            icon(slug, 28, 14, 20, t["ink"], .92),
            text(60, h / 2 + 4.5, label, 13, t["ink"], weight=500)]
    return svg_doc(w, h, "".join(body), label=label)


# ---------------------------------------------------------------- about window
MW = .601          # monospace advance, as a fraction of font size


def mono_w(s, size):
    return len(s) * size * MW


BIO = [
    ("cmd", "whoami"),
    ("ink", "Zainul Arkaan Alinsi — full-stack developer"),
    ("muted", "student @ IDN Boarding School, a program for future tech leaders"),
    ("gap", ""),
    ("cmd", "cat focus.txt"),
    ("dot", "Full-stack web apps with PHP, Laravel, Next.js and Tailwind CSS"),
    ("dot", "Learning Flutter for mobile development"),
    ("dot", "Efficient code, real-world impact — that is the whole brief"),
    ("gap", ""),
    ("cmd", "echo $STATUS"),
    ("ok", "open to collaborate · shipping something every week"),
]
FACTS = [("role", "Full-stack developer"),
         ("school", "IDN Boarding School"),
         ("stack", "Laravel · Next.js · Tailwind"),
         ("learning", "Flutter · Dart"),
         ("editor", "VS Code"),
         ("timezone", "WIB · UTC+7")]

PROMPT, PSIZE = "zainul@github", 12
CARD_W = 500

ABOUT_CSS = (
    "@keyframes bob{0%,100%{opacity:1}50%{opacity:.35}}"
    "@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}"
    "@keyframes sh{0%,100%{transform:scale(1)}50%{transform:scale(.86)}}"
    ".bob{animation:bob 1.1s steps(1) infinite}"
    ".fl{animation:fl 4.2s ease-in-out infinite}"
    ".sh{animation:sh 4.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
    "@media (prefers-reduced-motion:reduce){.bob,.fl,.sh{animation:none}}")


def terminal(t, x, y):
    """The left column: a session you could have typed yourself. Nothing here
    animates in: a renderer that skips CSS must still show every line."""
    out = []
    reveal = str

    def prompt(y, cmd=""):
        return (text(x, y, PROMPT, PSIZE, t["green"], weight=600)
                + text(x + mono_w(PROMPT, PSIZE), y, ":~$", PSIZE, t["muted"])
                + (text(x + mono_w(PROMPT + ":~$ ", PSIZE), y, cmd, PSIZE, t["ink"]) if cmd else ""))

    for kind, ln in BIO:
        if kind == "gap":
            y += 10
            continue
        if kind == "cmd":
            out.append(reveal(prompt(y, ln)))
            y += 28
            continue
        lead = ""
        if kind == "dot":
            lead = rect(x + 2, y - 7, 6, 6, fill=t["blue"])
        elif kind == "ok":
            lead = (f'<circle cx="{x + 5:.1f}" cy="{y - 4:.1f}" r="7" fill="{t["green"]}" opacity=".18"/>'
                    f'<circle cx="{x + 5:.1f}" cy="{y - 4:.1f}" r="3.2" fill="{t["green"]}"/>')
        colour = {"muted": t["muted"], "ok": t["green"]}.get(kind, t["ink"])
        out.append(reveal(lead + text(x + (16 if kind in ("dot", "ok") else 0), y, ln, 12.5, colour)))
        y += 23
    y += 8
    out.append(reveal(prompt(y) + f'<rect class="bob" x="{x + mono_w(PROMPT + ":~$ ", PSIZE):.1f}"'
                                  f' y="{y - 10:.0f}" width="8" height="13" fill="{t["ink"]}"/>'))
    return "".join(out), y + 8


def island(t, cx, cy, k):
    """A floating voxel island with a desk setup on it: the neofetch logo, if
    neofetch drew in 3D. Painter's order, far to near."""
    iso = Iso(cx, cy, k)
    grass, leaf = t["green"], mix(t["green"], t["bg"], .18)
    dirt = mix(t["bg"], t["amber"], .52)
    stone = mix(t["bg"], t["ink"], .30)
    wood = mix(t["bg"], t["amber"], .78)
    metal = mix(t["bg"], t["ink"], .22)
    out = []
    # the underside tapers, as if it was scooped out of the ground
    out.append(iso.box(.7, .7, -2.1, 1.6, 1.6, .9, stone))
    out.append(iso.box(.3, .3, -1.2, 2.4, 2.4, .8, dirt))
    out.append(iso.box(0, 0, -.4, 3, 3, .4, dirt, top=grass))
    out.append(poly([iso.p(0, 3, 0), iso.p(3, 3, 0), iso.p(3, 3, -.14), iso.p(0, 3, -.14)], shade(grass, .72)))
    out.append(poly([iso.p(3, 0, 0), iso.p(3, 3, 0), iso.p(3, 3, -.14), iso.p(3, 0, -.14)], shade(grass, .52)))
    for (u, v) in ((.3, .4), (2.5, 2.3), (.4, 2.4), (1.5, 2.65), (2.65, 1.5)):
        out.append(poly([iso.p(u, v), iso.p(u + .2, v), iso.p(u + .2, v + .2), iso.p(u, v + .2)],
                        shade(grass, 1.15)))
    # tree, back right
    out.append(iso.box(2.3, .4, 0, .3, .3, 1.1, wood))
    out.append(iso.box(1.9, 0, 1.0, 1.1, 1.1, .9, leaf))
    out.append(iso.box(2.1, .2, 1.9, .7, .7, .45, shade(leaf, 1.08)))
    # desk
    for u, v in ((.35, 1.05), (1.95, 1.05), (.35, 1.9), (1.95, 1.9)):
        out.append(iso.box(u, v, 0, .14, .14, .62, wood))
    out.append(iso.box(.25, .95, .62, 1.95, 1.15, .12, wood))
    # monitor: stand, then the panel, facing the viewer on its +v face
    out.append(iso.box(1.0, 1.15, .74, .42, .3, .06, metal))
    out.append(iso.box(1.14, 1.22, .8, .14, .1, .36, metal))
    out.append(iso.box(.45, 1.1, 1.08, 1.55, .12, .95, metal))
    m = iso.face_matrix("left", .45, 1.1, 1.08, 1.55, .12, .95)
    code = [(.10, .16, .28, "violet"), (.42, .16, .22, "ink"), (.16, .31, .40, "blue"),
            (.16, .46, .24, "green"), (.44, .46, .30, "amber"), (.10, .61, .20, "violet"),
            (.16, .76, .42, "muted")]
    lines = "".join(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height=".07" fill="{t[c]}"/>'
                    for x, y, w, c in code)
    out.append(f'<g transform="{m}"><rect x=".05" y=".07" width=".9" height=".86" fill="#0B0F14"/>{lines}'
               f'<rect class="bob" x=".62" y=".74" width=".04" height=".11" fill="{t["green"]}"/></g>')
    # keyboard and a mug, nearest to the camera
    out.append(iso.box(.6, 1.55, .74, 1.0, .32, .05, mix(t["bg"], t["ink"], .40)))
    out.append(iso.box(1.75, 1.62, .74, .24, .24, .24, t["red"]))
    return "".join(out)


def id_card(t, x, y, h):
    """The right column: neofetch — logo on the left, key/value pairs, colour row."""
    out = [glass("idcard", x, y, CARD_W, h, t, r=14,
                 glows=[(.20, .35, CARD_W * .42, "green"), (.95, .10, CARD_W * .45, "violet")])]
    # the island floats; its shadow on the card breathes with it
    out.append(f'<ellipse class="sh" cx="{x + 104:.1f}" cy="{y + h - 26:.1f}" rx="66" ry="9"'
               f' fill="{t["shadow"]}" opacity="{.3 if t["px_shadow"] > .3 else .12}"/>')
    out.append(f'<g class="fl">{island(t, x + 108, y + 52, 23)}</g>')

    fx = x + 232
    out.append(text(fx, y + 42, PROMPT, 13, t["green"], weight=700))
    out.append(line(fx, y + 53, fx + mono_w(PROMPT, 13), y + 53, t["muted"], 1, .6))
    top = y + 80
    for i, (k, v) in enumerate(FACTS):
        ry = top + 25 * i
        out.append(text(fx, ry, k, 11.5, t[ACCENTS[i % len(ACCENTS)]], weight=700))
        out.append(text(fx + 76, ry, v, 11.5, t["ink"]))
    sy = top + 25 * len(FACTS) - 6
    for i, c in enumerate(("red", "amber", "green", "blue", "violet")):
        out.append(rect(fx + i * 22, sy, 18, 10, fill=t[c]))
        out.append(rect(fx + i * 22, sy + 10, 18, 3, fill=shade(t[c], .6)))
    return "".join(out)


def about(t):
    x0, y0 = PAD + 28, PAD + 104
    term, term_end = terminal(t, x0, y0)
    card_top, card_h = PAD + 48, 282
    h = int(max(term_end, card_top + card_h) + 24 - PAD)
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "zainul@github: ~/about", "bash — 80x24", "blue", "about"),
            heading(t, "ABOUT ME", x0, PAD + 52, px=3),
            term,
            id_card(t, W - PAD - 24 - CARD_W, card_top, card_h)]
    return svg_doc(W, h + PAD * 2, "".join(body), label="About Zainul Arkaan Alinsi", css=ABOUT_CSS)


# ------------------------------------------------------------ stack inventory
# The four the bio names as what gets built with, plus the one it names as being
# learned. Marked, not invented — the same list the about panel prints.
CORE = {"php", "laravel", "nextdotjs", "tailwindcss", "flutter"}
CELL, K = 108, 28            # horizontal pitch per block, iso unit

STACK_CSS = (
    "@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}"
    "@keyframes sh{0%,100%{opacity:.34}50%{opacity:.14}}"
    "@keyframes gl{0%,100%{opacity:.15}50%{opacity:.6}}"
    ".fl{animation:fl 3.6s ease-in-out infinite}"
    ".sh{animation:sh 3.6s ease-in-out infinite}"
    ".gl{animation:gl 3.6s ease-in-out infinite}"
    "@media (prefers-reduced-motion:reduce){.fl,.sh,.gl{animation:none}}")


def block(t, cx, gy, slug, label, accent, delay, core):
    """One tool as a floating voxel block: logo stamped on the lit top face,
    name on the ground under it."""
    iso = Iso(cx, gy, K)
    col = t[accent]
    out = []
    # the tile it hovers over, and a shadow that thins out as it rises
    tile = [iso.p(-.62, -.62), iso.p(.62, -.62), iso.p(.62, .62), iso.p(-.62, .62)]
    out.append(poly(tile, mix(t["bg"], col, .07), f' stroke="{col}" stroke-opacity=".30" stroke-width="1"'))
    out.append(poly([iso.p(-.42, -.42), iso.p(.42, -.42), iso.p(.42, .42), iso.p(-.42, .42)], t["shadow"],
                    f' class="sh" style="animation-delay:{delay:.2f}s" opacity=".3"'))
    lift = .55
    cube = []
    if core:
        c0 = iso.p(0, 0, lift + .5)
        cube.append(f'<ellipse class="gl" style="animation-delay:{delay:.2f}s" cx="{c0[0]:.1f}"'
                    f' cy="{c0[1]:.1f}" rx="{K * 1.35:.1f}" ry="{K * 1.2:.1f}" fill="{col}" opacity=".3"'
                    f' filter="url(#soft)"/>')
    dark = t["bg"] == THEMES["dark"]["bg"]
    # dark canvas: a smoky block with lit edges; light canvas: a solid coloured one
    sides = mix(t["bg"], col, .30) if dark else mix(col, "#FFFFFF", .12)
    cube.append(iso.box(-.5, -.5, lift, 1, 1, 1, sides, top=mix(t["bg"], col, .44 if dark else .30)))
    # lit edges: the three that face the light pick up the accent
    a, b, c, d = iso.p(-.5, .5, lift + 1), iso.p(.5, .5, lift + 1), iso.p(.5, -.5, lift + 1), iso.p(.5, .5, lift)
    cube.append(f'<path d="M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}L{c[0]:.1f} {c[1]:.1f}'
                f'M{b[0]:.1f} {b[1]:.1f}L{d[0]:.1f} {d[1]:.1f}" stroke="{col}" stroke-width="1.3"'
                f' stroke-linecap="round" fill="none" opacity=".9"/>')
    m = iso.face_matrix("top", -.5, -.5, lift, 1, 1, 1)
    cube.append(f'<g transform="{m}"><g transform="translate(.11,.11) scale({.78 / 24:.5f})"'
                f' fill="{t["ink"]}"><path d="{PATHS[slug]}"/></g></g>')
    # the front faces carry a few accent pixels, the way a textured block would
    ml = iso.face_matrix("left", -.5, -.5, lift, 1, 1, 1)
    cube.append(f'<g transform="{ml}" fill="{col}"><rect x=".12" y=".70" width=".16" height=".14" opacity=".7"/>'
                f'<rect x=".34" y=".70" width=".16" height=".14" opacity=".35"/></g>')
    out.append(f'<g class="fl" style="animation-delay:{delay:.2f}s">{"".join(cube)}</g>')
    ly = iso.p(.62, .62)[1] + 20
    out.append(text(cx, ly, label, 12.5, t["ink"], anchor="middle", weight=500))
    if core:
        out.append(rect(cx - 3, ly + 8, 6, 6, fill=col))
    return "".join(out)


def stack_panel(t):
    x0 = PAD + 28
    top = PAD + 112
    row_h = 160
    out = []
    for r, (name, items) in enumerate(STACK.items()):
        accent = ROW_ACCENT[name]
        ry = top + r * row_h
        if r:
            out.append(line(x0, ry - 8, W - PAD - 28, ry - 8, t["line"], 1, .8))
        # the row's label: a coloured rail, the name, the count in pixel type
        out.append(rect(x0, ry + 30, 3, 66, fill=t[accent]))
        out.append(text(x0 + 16, ry + 44, name.upper(), 11, t["muted"], weight=700, ls="1.8"))
        out.append(pixel_text(f"{len(items):02d}", x0 + 16, ry + 56, 4, t[accent],
                              shadow=t["shadow"], shadow_op=t["px_shadow"]))
        out.append(text(x0 + 16, ry + 100, "blocks", 10.5, t["muted"]))
        gx = x0 + 214
        for i, (slug, label) in enumerate(items):
            out.append(block(t, gx + i * CELL, ry + 84, slug, label, accent,
                             -(r * .9 + i * .45), slug in CORE))
    h = int(top + row_h * len(STACK) - PAD)
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "~/stack — inventory",
                   f"{sum(len(v) for v in STACK.values())} items", "violet", "stack",
                   glows=[(.10, .30, 320, "blue"), (.55, .60, 300, "violet"), (.95, .85, 300, "amber")]),
            heading(t, "TECH STACK", x0, PAD + 52,
                    sub="every tool as a block · the glowing ones are what I build with daily", px=3),
            "".join(out)]
    defs = '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>'
    return svg_doc(W, h + PAD * 2, "".join(body), defs=defs, css=STACK_CSS, label="Tech stack: " + ", ".join(
        lab for items in STACK.values() for _, lab in items))


# ----------------------------------------------------------------- news header
def news_header(t, stamp="", count=0):
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
        for slug, label, accent in LINKS:
            p = ASSETS / f"link-{slug}-{name}.svg"
            p.write_text(link_chip(tokens, slug, label, accent), encoding="utf-8")
            made.append(p.name)
        for fn, base in ((about, "about"), (stack_panel, "stack")):
            p = ASSETS / f"{base}-{name}.svg"
            p.write_text(fn(tokens), encoding="utf-8")
            made.append(p.name)
        p = ASSETS / f"news-{name}.svg"
        if not p.exists():                     # build_news.py owns this once it has real counts
            p.write_text(news_header(tokens), encoding="utf-8")
            made.append(p.name)
        p = ASSETS / f"footer-{name}.svg"
        p.write_text(footer(tokens), encoding="utf-8")
        made.append(p.name)
    return made


if __name__ == "__main__":
    for n in build():
        print("wrote", n)
