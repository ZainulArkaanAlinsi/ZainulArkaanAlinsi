"""Frosted-glass panels for the whole profile.

Three rules, applied to every image on the page:
  1. one solid palette — navy, sand, sage, terracotta, light grey, ivory; no gradient fills
     on type or accents
  2. tech logos keep their own brand colours
  3. a frosted-glass look: a navy plate lit by soft, heavily blurred light (bokeh), with
     translucent glass panes on top

  link-*-dark.svg    social buttons          about-dark.svg     dithered hands + bio
  stack-dark.svg     folder of fanned cards  activity-dark.svg  numbers + year map
  commits-dark.svg   latest public pushes    news-dark.svg      news header
  footer-dark.svg    sign-off

The serif and mono faces are the subsets already embedded in hero.svg
(scripts/art/fonts.css). Motion is CSS only; every element is visible without it.
"""
import base64
import datetime as dt
import os
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import ASSETS, THEMES
from build_panels import BLURB, FACTS, NAME, PATHS, STACK, brand

ART = Path(__file__).parent / "art"
FONTS = (ART / "fonts.css").read_text(encoding="utf-8")

NAVY, SAND, SAGE, TERRA, GREY, IVORY = "#0D1B2A", "#E8DCC4", "#A7B89A", "#E07A5F", "#D1D5DB", "#F5F1E8"
DEEP = "#08121C"                      # the darkest navy, for wells that carry logos
W = 1200
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"

CSS = (FONTS
       + ".s{font-family:Serif,Georgia,serif}.si{font-family:SerifI,Georgia,serif;font-style:italic}"
       ".m{font-family:Mono,ui-monospace,Consolas,monospace}"
       f".cap{{font-family:Mono,ui-monospace,monospace;font-size:12px;letter-spacing:2.6px;fill:{SAND}}}"
       "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1.1s steps(1) infinite}"
       "@keyframes reachL{0%,100%{transform:translateX(0)}50%{transform:translateX(10px)}}"
       "@keyframes reachR{0%,100%{transform:translateX(0)}50%{transform:translateX(-10px)}}"
       ".rl{animation:reachL 5s ease-in-out infinite}.rr{animation:reachR 5s ease-in-out infinite}"
       "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}"
       ".bob{animation:bob 4.8s ease-in-out infinite}"
       "@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(40px,-18px)}}"
       ".drift{animation:drift 16s ease-in-out infinite}"
       "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:.85}}.pulse{animation:pulse 3s ease-in-out infinite}"
       "@keyframes flash{0%{opacity:.16}8%{opacity:.05}100%{opacity:.05}}"
       ".flash{animation:flash 6s steps(3) infinite}"
       "@keyframes sel{0%{opacity:1}23%{opacity:0}100%{opacity:0}}.sel{opacity:0;animation:sel 6s steps(1) infinite}"
       "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")


def esc(s):
    return escape(str(s), quote=False)


# --------------------------------------------------------------- glass kit
LIGHTS = (TERRA, SAGE, SAND, "#4A6A8A")


def backdrop(w, h, seed=0):
    """A flat navy plate. Glass reads best on one calm solid colour, so no blurred lights."""
    return f'<rect width="{w}" height="{h}" fill="{NAVY}"/>'


def pane(x, y, w, h, r=26, op=.08):
    """A sheet of frosted glass: milky fill, hairline rim, a brighter top edge."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{IVORY}" opacity="{op}"/>'
            f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none"'
            f' stroke="{IVORY}" stroke-opacity=".26"/>'
            f'<rect x="{x + r}" y="{y + 1}" width="{w - 2 * r}" height="1.2" fill="{IVORY}" opacity=".45"/>')


def doc(h, body, label, seed=0, w=W):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img"'
            f' aria-label="{escape(label)}"><title>{escape(label)}</title><style>{CSS}</style>'
            f'<defs><filter id="bk" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>'
            f'<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="7"/></filter></defs>'
            f'{backdrop(w, h, seed)}{body}</svg>')


def t(x, y, s, cls="m", size=14, fill=IVORY, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size}" fill="{fill}"'
            f' text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def cap(x, y, s, anchor="start", fill=SAND):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="cap" fill="{fill}" text-anchor="{anchor}">{esc(s.upper())}</text>'


def hair(x1, y1, x2, y2, op=.22):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{IVORY}" stroke-opacity="{op}"/>'


def glyph(slug, x, y, size, fill=IVORY):
    k = size / 24
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="{fill}"><path d="{PATHS[slug]}"/></g>'


def logo(slug, x, y, size):
    return glyph(slug, x, y, size, brand(THEMES["dark"], slug, DEEP))


# ------------------------------------------------------------------- links
HANDLES = {"instagram": "@zainarilbre", "linkedin": "in/zainul-arkaan", "youtube": "@zainarilbre",
           "gmail": "say hello"}
LINK_W, LINK_H = 266, 96


def link(slug, label, idx=0):
    x, y, w, h = 10, 10, LINK_W - 20, LINK_H - 20
    delay = f"animation-delay:{idx * 1.5:.1f}s"
    body = [pane(x, y, w, h, 24, .10),
            f'<circle cx="{x + 40}" cy="{y + h / 2}" r="25" fill="{DEEP}" opacity=".85"/>',
            logo(slug, x + 27, y + h / 2 - 13, 26),
            t(x + 80, y + 34, label, "m", 17, IVORY, extra=' font-weight="700"'),
            t(x + 80, y + 56, HANDLES.get(slug, ""), "m", 13, GREY),
            f'<rect class="sel" style="{delay}" x="{x - 3}" y="{y - 3}" width="{w + 6}" height="{h + 6}" rx="27"'
            f' fill="none" stroke="{TERRA}" stroke-width="2.5"/>']
    return doc(LINK_H, "".join(body), label, seed=idx, w=LINK_W)


# ------------------------------------------------------------------- about
def about():
    art = base64.b64encode((ART / "hands.png").read_bytes()).decode()
    iw, ih = 736, 340
    k = (W - 80) / iw
    ah = ih * k
    ox, oy = 40, 30
    X = lambda v: ox + v * k
    Y = lambda v: oy + v * k
    split = X(388)
    wx, wy, ww, wh = X(266), Y(84), X(509) - X(266), Y(256) - Y(84)
    body = [pane(24, 16, W - 48, 0, 30, 0)]                  # placeholder, sized below
    art_layer = [
        f'<mask id="hm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{oy + ah:.1f}">'
        f'<image href="data:image/png;base64,{art}" x="{ox}" y="{oy}" width="{W - 80}" height="{ah:.1f}"'
        f' style="image-rendering:pixelated" preserveAspectRatio="none"/></mask>',
        f'<clipPath id="cl"><rect x="0" y="0" width="{split:.1f}" height="{oy + ah:.1f}"/></clipPath>',
        f'<clipPath id="cr"><rect x="{split:.1f}" y="0" width="{W - split:.1f}" height="{oy + ah:.1f}"/></clipPath>',
        f'<g class="rl"><g clip-path="url(#cl)"><rect width="{W}" height="{oy + ah:.1f}" fill="{IVORY}" mask="url(#hm)"/></g></g>',
        f'<g class="rr"><g clip-path="url(#cr)"><rect width="{W}" height="{oy + ah:.1f}" fill="{IVORY}" mask="url(#hm)"/></g></g>',
        f'<rect class="pulse" x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh:.1f}" fill="none"'
        f' stroke="{IVORY}" stroke-width="8" filter="url(#glow)"/>',
        f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh:.1f}" fill="none" stroke="{IVORY}" stroke-width="4"/>',
        f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="26" fill="{IVORY}"/>',
        t(wx + 12, wy + 18, "ABOUT_ME.EXE", "m", 14, NAVY, extra=' font-weight="700" letter-spacing="1"'),
        "".join(f'<rect x="{wx + ww - 22 - i * 22:.1f}" y="{wy + 6:.1f}" width="14" height="14" fill="none"'
                f' stroke="{NAVY}" stroke-width="2.5"/>' for i in range(3)),
        t(X(392), wy + 56, "> hi, i'm zainul", "m", 15, IVORY),
        t(X(392), wy + 80, "> welcome in", "m", 15, SAND),
        f'<rect class="blink" x="{X(392) + 120:.1f}" y="{wy + 67:.1f}" width="9" height="16" fill="{TERRA}"/>']

    y0 = oy + ah + 26
    text_layer = [hair(64, y0, W - 64, y0),
                  cap(64, y0 + 30, "Fig. 02 — About"), cap(W - 64, y0 + 30, "Creation / 2026", "end"),
                  t(64, y0 + 104, NAME, "s", 56, IVORY),
                  t(64, y0 + 146, "full-stack developer, student at IDN.", "si", 27, SAND)]
    for i, ln in enumerate(BLURB):
        text_layer.append(t(650, y0 + 84 + i * 32, ln.replace("I'm", "I’m"), "s", 21, GREY))
    fy = y0 + 214
    text_layer.append(hair(64, fy - 30, W - 64, fy - 30))
    for i, (key, val) in enumerate(FACTS):
        fx = 64 + i * 276
        text_layer.append(cap(fx, fy, key, fill=(TERRA, SAGE, SAND, GREY)[i]))
        text_layer.append(t(fx, fy + 36, val, "s", 27, IVORY))
    h = fy + 76
    body = [pane(24, 16, W - 48, h - 32, 30, .07)] + art_layer + text_layer
    return doc(h, "".join(body), "About Zainul Arkaan Alinsi: " + " ".join(BLURB), seed=1)


# ------------------------------------------------------------------- stack
CARD_W, CARD_H = 300, 384


def card(cx, top, angle, title, items, edge, delay=0.0):
    x, cy = cx - CARD_W / 2, top + CARD_H / 2
    g = [f'<g class="bob" style="animation-delay:{delay}s"><g transform="rotate({angle} {cx:.1f} {cy:.1f})">',
         f'<rect x="{x - 8:.1f}" y="{top - 8:.1f}" width="{CARD_W + 16}" height="{CARD_H + 16}" rx="26" fill="{edge}"/>',
         f'<rect x="{x:.1f}" y="{top:.1f}" width="{CARD_W}" height="{CARD_H}" rx="18" fill="{DEEP}"/>',
         cap(x + 24, top + 40, title, fill=edge),
         cap(x + CARD_W - 24, top + 40, f"{len(items):02d}", "end", GREY),
         f'<line x1="{x + 24:.1f}" y1="{top + 56:.1f}" x2="{x + CARD_W - 24:.1f}" y2="{top + 56:.1f}"'
         f' stroke="{IVORY}" stroke-opacity=".14"/>']
    cw, rh = (CARD_W - 48) / 3, 76
    for i, (slug, label) in enumerate(items):
        gx = x + 24 + (i % 3) * cw + cw / 2
        gy = top + 78 + (i // 3) * rh
        g.append(logo(slug, gx - 15, gy, 30))
        g.append(f'<text x="{gx:.1f}" y="{gy + 50:.1f}" font-family="{SANS}" font-size="12.5" fill="{GREY}"'
                 f' text-anchor="middle">{esc(label)}</text>')
    g.append("</g></g>")
    return "".join(g)


def stack():
    groups = list(STACK.items())
    total = sum(len(v) for _, v in groups)
    cx = W / 2
    fx, fy, fw, fh = cx - 300, 392, 600, 220
    body = [card(cx - 318, 104, -8, groups[0][0], groups[0][1], SAND, 0),
            card(cx + 318, 104, 8, groups[2][0], groups[2][1], TERRA, -1.6),
            card(cx, 46, 0, groups[1][0], groups[1][1], SAGE, -3.2),
            # the folder: frosted glass over the cards
            f'<path d="M{fx} {fy + 24} q0 -24 24 -24 h190 q14 0 24 12 l18 22 h{fw - 276} q24 0 24 24 v{fh - 46}'
            f' q0 24 -24 24 h-{fw - 48} q-24 0 -24 -24 z" fill="#3B4A5C" opacity=".72"/>',
            pane(fx, fy + 34, fw, fh - 10, 24, .16),
            t(fx + 30, fy + 26, "*TECHSTACK.", "m", 15, IVORY),
            t(fx + 30, fy + 96, "the tools I reach for", "si", 30, IVORY),
            t(fx + 30, fy + 130, "web · mobile · data", "m", 14, SAND),
            f'<circle cx="{fx + fw - 62}" cy="{fy + fh - 54}" r="38" fill="{TERRA}"/>',
            f'<path d="M{fx + fw - 76} {fy + fh - 40} l26 -26 M{fx + fw - 72} {fy + fh - 66} h22 v22" stroke="{IVORY}"'
            f' stroke-width="7" fill="none" stroke-linecap="square"/>',
            f'<text x="{cx}" y="{fy + fh + 128}" font-family="{SANS}" font-size="92" font-weight="600" fill="{IVORY}"'
            f' text-anchor="middle" letter-spacing="-1">TECH STACK</text>',
            pane(cx - 118, fy + fh + 154, 236, 46, 23, .12),
            t(cx, fy + fh + 184, f"{total} tools · 2026", "m", 16, SAND, "middle")]
    h = fy + fh + 236
    label = "Tech stack: " + "; ".join(f"{k}: " + ", ".join(lab for _, lab in v) for k, v in groups)
    return doc(h, "".join(body), label, seed=2)


# ---------------------------------------------------------------- activity
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
DOTS = {1: [(0, 0)], 2: [(0, 0), (1, 1)], 3: [(0, 0), (1, 1), (1, 0)], 4: [(0, 0), (1, 1), (1, 0), (0, 1)]}


def dot_defs():
    out = [f'<pattern id="d0" width="8" height="8" patternUnits="userSpaceOnUse">'
           f'<rect x="2" y="2" width="3" height="3" fill="{IVORY}" opacity=".16"/></pattern>']
    for lv, dots in DOTS.items():
        fill = SAND if lv == 4 else SAGE
        cells = "".join(f'<rect x="{dx * 4}" y="{dy * 4}" width="3" height="3" fill="{fill}"/>' for dx, dy in dots)
        out.append(f'<pattern id="d{lv}" width="8" height="8" patternUnits="userSpaceOnUse">{cells}</pattern>')
    return "<defs>" + "".join(out) + "</defs>"


def activity(created, recent, all_days, stamp, today):
    from build_activity import streaks
    total = sum(all_days.values())
    cur, _, longest, _ = streaks(all_days, today)
    best_d = max(all_days, key=lambda d: all_days[d]) if all_days else None
    best_n = all_days.get(best_d, 0) if best_d else 0
    days = [d for w in recent["weeks"] for d in w["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"])
    since = dt.date.fromisoformat(created[:10]).strftime("%b %Y")
    best_txt = dt.date.fromisoformat(best_d).strftime("%b %d").replace(" 0", " ") if best_d else "—"
    cols = [("Total", f"{total:,}", f"since {since}", TERRA),
            ("Last 12 months", f"{recent['totalContributions']:,}", f"{active} active days", SAND),
            ("Current streak", str(cur), "days in a row", SAGE),
            ("Longest streak", str(longest), "days", GREY),
            ("Best day", str(best_n), best_txt, IVORY)]

    weeks = recent["weeks"]
    cell, gap = 15, 5
    gw = len(weeks) * (cell + gap) - gap
    gx, gy = (W - gw) / 2, 284
    ly = gy + 7 * (cell + gap) + 60
    h = ly + 52

    body = [dot_defs(), pane(24, 16, W - 48, h - 32, 30, .07),
            cap(64, 62, "Fig. 03 — Contributions"), cap(W - 64, 62, f"synced {stamp}", "end", GREY),
            hair(64, 80, W - 64, 80)]
    cw = (W - 128) / len(cols)
    for i, (k, v, sub, col) in enumerate(cols):
        x = 64 + i * cw
        if i:
            body.append(hair(x - 14, 104, x - 14, 222))
        body.append(cap(x, 122, k, fill=GREY))
        body.append(t(x, 190, v, "s", 64, col))
        body.append(t(x, 216, sub, "m", 13, GREY))
    body.append(hair(64, 254, W - 64, 254))

    last = None
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            x, y = gx + wi * (cell + gap), gy + d["weekday"] * (cell + gap)
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}"'
                        f' fill="url(#d{LEVEL.get(d["contributionLevel"], 0)})"/>')
            last = (x, y)
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.day <= 7 and wi < len(weeks) - 2:
            body.append(cap(gx + wi * (cell + gap), gy + 7 * (cell + gap) + 22, first.strftime("%b"), fill=GREY))
    if last:
        body.append(f'<rect class="blink" x="{last[0] - 3:.1f}" y="{last[1] - 3:.1f}" width="{cell + 6}"'
                    f' height="{cell + 6}" fill="none" stroke="{TERRA}" stroke-width="2"/>')
    for i, lab in enumerate(("Mon", "Wed", "Fri")):
        body.append(cap(gx - 12, gy + (1 + 2 * i) * (cell + gap) + 12, lab, "end", GREY))
    body.append(cap(64, ly, f"{recent['totalContributions']:,} contributions in the last year", fill=GREY))
    lx = W - 64 - 5 * 24 - 54
    body.append(cap(lx - 10, ly, "less", "end", GREY))
    for lv in range(5):
        body.append(f'<rect x="{lx + lv * 24}" y="{ly - 14}" width="{cell}" height="{cell}" fill="url(#d{lv})"/>')
    body.append(cap(W - 64, ly, "more", "end", GREY))
    return doc(h, "".join(body), f"Contributions: {total:,} total, current streak {cur} days, longest {longest}, "
                                  f"best day {best_n}.", seed=3)


# ----------------------------------------------------------------- commits
TAG = {"feat": SAGE, "fix": TERRA, "docs": SAND, "chore": SAND, "refactor": SAND, "perf": SAND,
       "build": SAND, "ci": SAND, "style": SAND, "test": GREY}


def commits(rows, pushes, stamp):
    n = max(1, len(rows))
    top = 112
    h = top + n * 44 + 86
    body = [pane(24, 16, W - 48, h - 32, 30, .07),
            cap(64, 62, "Fig. 04 — Commit log"), cap(W - 64, 62, f"synced {stamp}", "end", GREY),
            hair(64, 80, W - 64, 80)]
    if pushes:
        body.append(t(W - 64, 106, f"{pushes} push{'es' if pushes != 1 else ''} in the last 7 days", "m", 13,
                      SAND, "end"))
    body.append(t(64, 106, "latest pushes to public repos, newest first", "si", 18, GREY))
    if not rows:
        body.append(t(64, top + 52, "no public pushes yet — the next one shows up here", "m", 14, GREY))
    for i, r in enumerate(rows):
        y = top + 16 + i * 44
        col = TAG.get(r["tag"], GREY)
        when = r["at"].astimezone(dt.timezone(dt.timedelta(hours=7))).strftime("%d %b %H:%M").lstrip("0")
        tag = r["tag"].upper()
        tw = len(tag) * 9 + 22
        repo = r["repo"] if len(r["repo"]) <= 26 else r["repo"][:25] + "…"
        body += [f'<rect x="56" y="{y}" width="{W - 112}" height="36" rx="12" fill="{IVORY}" opacity=".05"'
                 f' class="flash" style="animation-delay:{i * .5:.1f}s"/>',
                 t(76, y + 23, when, "m", 13, GREY),
                 f'<rect x="196" y="{y + 7}" width="{tw}" height="22" rx="11" fill="{col}"/>',
                 t(196 + tw / 2, y + 22.5, tag, "m", 12, NAVY, "middle", ' font-weight="700"'),
                 t(310, y + 23, repo, "m", 14, IVORY, extra=' font-weight="700"')]
        if r["text"]:
            body.append(t(560, y + 23, r["text"][:64] + ("…" if len(r["text"]) > 64 else ""), "m", 13, GREY))
        if r["new"]:
            body.append(f'<circle class="blink" cx="{W - 80}" cy="{y + 18}" r="5" fill="{TERRA}"/>')
    py = top + 16 + n * 44 + 24
    body.append(t(76, py, "> awaiting next push", "m", 14, SAND))
    body.append(f'<rect class="blink" x="{76 + 172}" y="{py - 13}" width="9" height="16" fill="{TERRA}"/>')
    return doc(h, "".join(body), f"Latest public pushes: {', '.join(r['repo'] for r in rows[:3]) or 'none yet'}",
               seed=4)


# -------------------------------------------------------------------- news
def news(stamp="", count=0):
    h = 150
    sub = (f"{count} stories pulled straight from the source feeds, newest first" if count
           else "pulled straight from the source feeds, newest first")
    body = [pane(24, 16, W - 48, h - 32, 30, .07),
            cap(64, 62, "Fig. 05 — Dev news"), cap(W - 64, 62, f"refreshed {stamp}" if stamp else "", "end", GREY),
            hair(64, 80, W - 64, 80),
            t(64, 118, sub, "si", 20, GREY)]
    return doc(h, "".join(body), "Developer news, refreshed automatically", seed=5)


# ------------------------------------------------------------------ footer
def footer():
    h = 210
    body = [pane(24, 16, W - 48, h - 32, 30, .07),
            t(W / 2, 112, "Thanks for stopping by.", "si", 58, IVORY, "middle"),
            cap(W / 2, 152, "Zainul Arkaan Alinsi — 2026 — see you in the next commit", "middle"),
            f'<rect class="blink" x="{W / 2 + 246}" y="74" width="14" height="40" fill="{TERRA}"/>']
    return doc(h, "".join(body), "Thanks for stopping by", seed=6)


def build_static():
    """No network: links, about, stack, footer."""
    made = []
    for name, fn in (("about", about), ("stack", stack), ("footer", footer)):
        (ASSETS / f"{name}-dark.svg").write_text(fn(), encoding="utf-8")
        made.append(f"{name}-dark.svg")
    return made


if __name__ == "__main__":
    for n in build_static():
        print("wrote", n)
