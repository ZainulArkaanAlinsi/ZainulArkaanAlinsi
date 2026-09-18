"""Static panels: link buttons, the about terminal, the stack inventory, section
headers and the footer. No network, no API — run it any time:

    python scripts/build_panels.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ACCENTS, ASSETS, PULSE_CSS, THEMES, glass, grass_block, line, mix,
                   pixel_text, pixel_width, rect, slot, svg_doc, text, ticks)

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
FACTS = [("ROLE", "Full-stack developer"),
         ("SCHOOL", "IDN Boarding School"),
         ("STACK", "Laravel \u00b7 Next.js \u00b7 Tailwind"),
         ("LEARNING", "Flutter \u00b7 Dart"),
         ("EDITOR", "VS Code"),
         ("TIMEZONE", "WIB \u00b7 UTC+7")]

PROMPT, PSIZE = "zainul@github", 12
CARD_W = 392


def terminal(t, x, y):
    """The left column: a session you could have typed yourself."""
    out = []
    for kind, line in BIO:
        if kind == "gap":
            y += 12
            continue
        if kind == "cmd":
            out.append(text(x, y, PROMPT, PSIZE, t["green"], weight=600))
            out.append(text(x + mono_w(PROMPT, PSIZE), y, ":~$", PSIZE, t["muted"]))
            out.append(text(x + mono_w(PROMPT + ":~$ ", PSIZE), y, line, PSIZE, t["ink"]))
            y += 29
        else:
            if kind == "dot":
                out.append(rect(x + 2, y - 7, 6, 6, fill=t["blue"]))
            out.append(text(x + (16 if kind == "dot" else 0), y, line, 12.5,
                            t["muted" if kind == "muted" else "ink"]))
            y += 24
    y += 6
    out.append(text(x, y, PROMPT, PSIZE, t["green"], weight=600))
    out.append(text(x + mono_w(PROMPT, PSIZE), y, ":~$", PSIZE, t["muted"]))
    out.append(f'<rect class="bob" x="{x + mono_w(PROMPT + ":~$ ", PSIZE):.1f}" y="{y - 10:.0f}"'
               f' width="8" height="13" fill="{t["ink"]}"/>')
    return "".join(out), y + 8


def id_card(t, x, y, h):
    """The right column: neofetch, basically. Rows stretch to fill the height."""
    out = [glass("idcard", x, y, CARD_W, h, t, r=14, glows=[(.85, .10, CARD_W * .55, "violet")])]
    out.append(grass_block(x + 44, y + 40, 20, 15, t["green"], mix(t["bg"], t["amber"], .46)))
    out.append(text(x + 80, y + 34, PROMPT, 13, t["green"], weight=600))
    out.append(text(x + 80, y + 51, "profile \u2014 the short version", 10.5, t["muted"]))
    out.append(line(x + 22, y + 70, x + CARD_W - 22, y + 70, t["line"], 1, .9))

    top, bottom = y + 94, y + h - 20
    step = min(30, (bottom - top) / max(1, len(FACTS) - 1))
    for i, (k, v) in enumerate(FACTS):
        ry = top + step * i
        out.append(rect(x + 22, ry - 8, 2, 9, fill=t[ACCENTS[i % len(ACCENTS)]]))
        out.append(text(x + 32, ry, k, 9.5, t["muted"], weight=600, ls="1.2"))
        out.append(text(x + 126, ry, v, 12, t["ink"]))
    return "".join(out)


def about(t):
    x0, y0 = PAD + 28, PAD + 106
    term, term_end = terminal(t, x0, y0)
    h = int(max(term_end, y0 + 232) + 30 - PAD)
    body = [rect(0, 0, W, h + PAD * 2, fill=t["bg"]),
            chrome(t, PAD, PAD, W - PAD * 2, h, "zainul@github: ~/about", "bash \u2014 80x24", "blue", "about"),
            heading(t, "ABOUT ME", x0, PAD + 52, px=3),
            term,
            id_card(t, W - PAD - 28 - CARD_W, y0 - 26, PAD + h - (y0 - 26) - 22)]
    return svg_doc(W, h + PAD * 2, "".join(body), label="About Zainul Arkaan Alinsi", css=PULSE_CSS)


# ------------------------------------------------------------ stack inventory
CELL_H, ICON = 96, 40      # one height for every row, so the rhythm stays even


def stack_panel(t):
    """Every row is flush left and right: a row holds exactly what it holds, so
    there are no empty slots pretending to be items."""
    x0 = PAD + 28
    grid_w = W - PAD * 2 - 56
    gap = 13
    y = PAD + 104
    parts = []
    for name, items in STACK.items():
        accent = ROW_ACCENT[name]
        cell = (grid_w - (len(items) - 1) * gap) / len(items)   # width fills the row exactly
        parts.append(rect(x0, y + 4, 3, 12, fill=t[accent]))
        parts.append(text(x0 + 12, y + 14, name.upper(), 10, t["muted"], weight=600, ls="1.6"))
        parts.append(text(x0 + grid_w, y + 14, f"{len(items)}", 10, t["muted"], anchor="end", ls="1.2"))
        parts.append(line(x0 + 26 + len(name) * 7.6, y + 9, x0 + grid_w - 18, y + 9, t["line"], 1, .8))
        y += 26
        for i, (sl, lab) in enumerate(items):
            sx = x0 + i * (cell + gap)
            parts.append(slot(sx, y, cell, CELL_H, t, depth=3))
            parts.append(icon(sl, sx + (cell - ICON) / 2, y + 20, ICON, t[accent]))
            parts.append(text(sx + cell / 2, y + CELL_H - 15, lab, 10, t["muted"], anchor="middle"))
        y += CELL_H + 22

    h = int(y - PAD)
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
