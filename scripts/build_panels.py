"""Static panels: link buttons, the about terminal, the stack inventory, section
headers and the footer. No network, no API — run it any time:

    python scripts/build_panels.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ASSETS, PULSE_CSS, THEMES, glass, line, pixel_text, pixel_width,
                   rect, slot, svg_doc, text, ticks)

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
    ("ink", "Zainul Arkaan Alinsi \u2014 full-stack developer"),
    ("muted", "student @ IDN Boarding School, a program for future tech leaders"),
    ("gap", ""),
    ("cmd", "cat focus.txt"),
    ("dot", "Full-stack web apps with PHP, Laravel, Next.js and Tailwind CSS"),
    ("dot", "Learning Flutter for mobile development"),
    ("dot", "Efficient code, real-world impact \u2014 that is the whole brief"),
]
CHIPS = [("ROLE", "Full-stack developer", "blue"),
         ("SCHOOL", "IDN Boarding School", "violet"),
         ("NOW", "Learning Flutter", "green")]

PROMPT, PSIZE = "zainul@github", 12


def about(t):
    x, y0 = PAD + 28, PAD + 104
    y = y0
    lines = []
    for kind, s in BIO:
        if kind == "gap":
            y += 10
            continue
        if kind == "cmd":
            lines.append(text(x, y, PROMPT, PSIZE, t["green"], weight=600))
            lines.append(text(x + mono_w(PROMPT, PSIZE), y, ":~$", PSIZE, t["muted"]))
            lines.append(text(x + mono_w(PROMPT + ":~$ ", PSIZE), y, s, PSIZE, t["ink"]))
            y += 28
        else:
            if kind == "dot":
                lines.append(rect(x + 2, y - 7, 6, 6, fill=t["blue"]))
            lines.append(text(x + (16 if kind == "dot" else 0), y, s, 12.5,
                              t["muted" if kind == "muted" else "ink"]))
            y += 23
    lines.append(text(x, y + 8, PROMPT, PSIZE, t["green"], weight=600))
    lines.append(text(x + mono_w(PROMPT, PSIZE), y + 8, ":~$", PSIZE, t["muted"]))
    lines.append(f'<rect class="bob" x="{x + mono_w(PROMPT + ":~$ ", PSIZE):.1f}" y="{y - 2:.0f}"'
                 f' width="8" height="13" fill="{t["ink"]}"/>')

    h = int(y + 36 - PAD)
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "zainul@github: ~/about", "bash \u2014 80x24", "blue", "about"),
            heading(t, "ABOUT ME", x, PAD + 52, px=3), "".join(lines)]

    cw = 300
    cx = W - PAD - 28 - cw
    cy0 = y0 - 30 + max(0, (y - y0 - 3 * 56) / 2)
    for i, (k, v, accent) in enumerate(CHIPS):
        cy = cy0 + i * 56
        body.append(glass(f"chip{i}", cx, cy, cw, 46, t, r=12, glows=[(.12, .5, 70, accent)]))
        body.append(rect(cx + 14, cy + 14, 3, 18, fill=t[accent]))
        body.append(text(cx + 26, cy + 20, k, 9.5, t["muted"], weight=600, ls="1.3"))
        body.append(text(cx + 26, cy + 35, v, 12.5, t["ink"], weight=500))
    return svg_doc(W, h + PAD * 2, "".join(body), label="About Zainul Arkaan Alinsi", css=PULSE_CSS)


# ------------------------------------------------------------ stack inventory
COLS = 9           # a Minecraft hotbar is nine slots wide; short rows stay empty


def stack_panel(t):
    x0 = PAD + 28
    grid_w = W - PAD * 2 - 56
    gap = 14
    cell = (grid_w - (COLS - 1) * gap) / COLS
    y = PAD + 104
    parts = []
    for name, items in STACK.items():
        accent = ROW_ACCENT[name]
        parts.append(rect(x0, y + 4, 3, 12, fill=t[accent]))
        parts.append(text(x0 + 12, y + 14, name.upper(), 10, t["muted"], weight=600, ls="1.6"))
        parts.append(line(x0 + 26 + len(name) * 7.6, y + 9, x0 + grid_w, y + 9, t["line"], 1, .8))
        y += 26
        for i in range(COLS):
            sx = x0 + i * (cell + gap)
            parts.append(slot(sx, y, cell, cell, t, depth=3))
            if i >= len(items):
                continue
            sl, lab = items[i]
            size = cell * .44
            parts.append(icon(sl, sx + (cell - size) / 2, y + cell * .20, size, t[accent]))
            parts.append(text(sx + cell / 2, y + cell - 15, lab, 9.5, t["muted"], anchor="middle"))
        y += cell + 20

    h = int(y - PAD + 16)
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "~/stack \u2014 inventory",
                   f"{sum(len(v) for v in STACK.values())} items", "violet", "stack"),
            heading(t, "TECH STACK", x0, PAD + 52, px=3),
            text(W - PAD - 28, PAD + 70, "what I actually ship with", 11.5, t["muted"], anchor="end"),
            "".join(parts)]
    return svg_doc(W, h + PAD * 2, "".join(body), label="Tech stack: " + ", ".join(
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
def footer(t, stamp=""):
    h = 84
    msg, px = "THANKS FOR STOPPING BY", 3
    body = [rect(0, 0, W, h + 16, fill=t["bg"]),
            glass("foot", PAD, 8, W - PAD * 2, h, t, r=14),
            pixel_text(msg, (W - pixel_width(msg, px)) / 2, 30, px, t["ink"],
                       shadow=t["shadow"], shadow_op=t["px_shadow"]),
            text(W / 2, 72, stamp or "built from code in this repo, refreshed on a schedule",
                 11, t["muted"], anchor="middle")]
    for i, k in enumerate(("green", "blue", "amber", "violet", "red")):
        body.append(rect(PAD + 24 + i * 14, 38, 9, 9, fill=t[k], op=.85))
        body.append(rect(W - PAD - 33 - i * 14, 38, 9, 9, fill=t[k], op=.85))
    return svg_doc(W, h + 16, "".join(body), label="Thanks for stopping by")


# ----------------------------------------------------------------------- build
def build(stamp=""):
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
        p.write_text(footer(tokens, stamp), encoding="utf-8")
        made.append(p.name)
    return made


if __name__ == "__main__":
    for n in build():
        print("wrote", n)
