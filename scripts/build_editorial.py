"""Monochrome editorial panels that sit under the hero.

  about-dark.svg     dithered "creation" hands with an ABOUT_ME.EXE window, bio below
  stack-dark.svg     a folder with three fanned cards: languages, frameworks, tools
  activity-dark.svg  contribution numbers + a dithered year heatmap (needs GITHUB_TOKEN)
  footer-dark.svg    closing line

One palette, the hero's: black plate, white ink, greys. The serif and mono faces
are the subsets already embedded in hero.svg (scripts/art/fonts.css), so the type
matches the hero exactly. Motion is CSS only and every element is visible without it.
"""
import base64
import datetime as dt
import math
import os
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import ASSETS
from build_panels import BLURB, FACTS, NAME, PATHS, STACK, brand
from theme import THEMES

ART = Path(__file__).parent / "art"
FONTS = (ART / "fonts.css").read_text(encoding="utf-8")
BG, INK, MUTED, DIM, LINE, CARD = "#0A0A0A", "#FAFAFA", "#A3A3A3", "#525252", "#262626", "#141414"
PINK, VIOLET, CYAN, GREEN, AMBER, BLUE = "#FF7AB6", "#B392FF", "#5CE1E6", "#5EE07A", "#FFC53D", "#5AA9FF"
GRAD = (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{PINK}"/>'
        f'<stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>')
W = 1200
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"
BASE_CSS = (FONTS
            + f".s{{font-family:Serif,Georgia,serif}}.si{{font-family:SerifI,Georgia,serif;font-style:italic}}"
            f".m{{font-family:Mono,ui-monospace,Consolas,monospace}}"
            f".cap{{font-family:Mono,ui-monospace,monospace;font-size:12px;letter-spacing:2.6px;fill:{MUTED}}}"
            "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1.1s steps(1) infinite}"
            "@keyframes reachL{0%,100%{transform:translateX(0)}50%{transform:translateX(10px)}}"
            "@keyframes reachR{0%,100%{transform:translateX(0)}50%{transform:translateX(-10px)}}"
            ".rl{animation:reachL 5s ease-in-out infinite}.rr{animation:reachR 5s ease-in-out infinite}"
            "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}"
            ".bob{animation:bob 4.8s ease-in-out infinite}"
            "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:.9}}.pulse{animation:pulse 3s ease-in-out infinite}"
            "@keyframes scan{0%{transform:translateX(-120px)}100%{transform:translateX(1180px)}}"
            ".scan{animation:scan 6s linear infinite}")
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def esc(s):
    return escape(str(s), quote=False)


def doc(h, body, label, css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img"'
            f' aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f"<style>{BASE_CSS}{css}{REDUCED}</style>"
            f'<defs>{GRAD}<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feGaussianBlur stdDeviation="7"/></filter></defs>'
            f'<rect width="{W}" height="{h}" fill="{BG}"/>{body}</svg>')


def t(x, y, s, cls="m", size=14, fill=INK, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size}" fill="{fill}"'
            f' text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def cap(x, y, s, anchor="start", fill=MUTED):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="cap" fill="{fill}" text-anchor="{anchor}">{esc(s.upper())}</text>'


def hair(x1, y1, x2, y2, op=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="1" opacity="{op}"/>'


def ticks(x, y, w, h, size=10):
    d = (f"M{x} {y + size}V{y}H{x + size} M{x + w - size} {y}H{x + w}V{y + size} "
         f"M{x + w} {y + h - size}V{y + h}H{x + w - size} M{x + size} {y + h}H{x}V{y + h - size}")
    return f'<path d="{d}" stroke="{MUTED}" stroke-width="1.2" fill="none" opacity=".6"/>'


def glyph(slug, x, y, size, fill=INK):
    k = size / 24
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="{fill}"><path d="{PATHS[slug]}"/></g>'


# ------------------------------------------------------------------- about
def about():
    art = base64.b64encode((ART / "hands.png").read_bytes()).decode()
    iw, ih = 736, 340                       # hands.png, already cropped and 1-bit
    k = W / iw
    ah = ih * k
    X = lambda v: v * k                    # image px -> panel px
    # the window inside the artwork: x 265..510, title bar y 83..94, body to 257
    split = X(388)                          # between the fingertips
    wx, wy, ww, wh = X(266), X(84), X(243), X(172)
    body = [f'<mask id="hm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{ah:.1f}">'
            f'<image href="data:image/png;base64,{art}" x="0" y="0" width="{W}" height="{ah:.1f}"'
            f' style="image-rendering:pixelated" preserveAspectRatio="none"/></mask>',
            f'<clipPath id="cl"><rect x="0" y="0" width="{split:.1f}" height="{ah:.1f}"/></clipPath>',
            f'<clipPath id="cr"><rect x="{split:.1f}" y="0" width="{W - split:.1f}" height="{ah:.1f}"/></clipPath>',
            f'<g class="rl"><g clip-path="url(#cl)"><rect width="{W}" height="{ah:.1f}" fill="{INK}" mask="url(#hm)"/></g></g>',
            f'<g class="rr"><g clip-path="url(#cr)"><rect width="{W}" height="{ah:.1f}" fill="{INK}" mask="url(#hm)"/></g></g>',
            f'<rect class="pulse" x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh:.1f}" fill="none"'
            f' stroke="{INK}" stroke-width="8" filter="url(#glow)"/>',
            f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh:.1f}" fill="none" stroke="{INK}" stroke-width="4"/>',
            f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="26" fill="{INK}"/>',
            t(wx + 12, wy + 18, "ABOUT_ME.EXE", "m", 14, BG, extra=' font-weight="700" letter-spacing="1"'),
            "".join(f'<rect x="{wx + ww - 22 - i * 22:.1f}" y="{wy + 6}" width="14" height="14" fill="none"'
                    f' stroke="{BG}" stroke-width="2.5"/>' for i in range(3)),
            t(X(392), wy + 56, "> hi, i'm zainul", "m", 15, INK),
            t(X(392), wy + 80, "> welcome in", "m", 15, MUTED),
            f'<rect class="blink" x="{X(392) + 120:.1f}" y="{wy + 67:.1f}" width="9" height="16" fill="{INK}"/>']

    y0 = ah + 28
    body += [hair(60, y0, W - 60, y0),
             cap(60, y0 + 30, "Fig. 02 — About"), cap(W - 60, y0 + 30, "Creation / 2026", "end"),
             t(60, y0 + 104, NAME, "s", 56, "url(#g)"),
             t(60, y0 + 146, "full-stack developer, student at IDN.", "si", 27, MUTED)]
    for i, ln in enumerate(BLURB):
        body.append(t(660, y0 + 84 + i * 32, ln.replace("I'm", "I’m"), "s", 21, MUTED))
    fy = y0 + 214
    body.append(hair(60, fy - 30, W - 60, fy - 30, .9))
    for i, (key, val) in enumerate(FACTS):
        fx = 60 + i * 280
        body.append(cap(fx, fy, key, fill=(PINK, VIOLET, CYAN, GREEN)[i]))
        body.append(t(fx, fy + 36, val, "s", 27))
    h = fy + 70
    return doc(h, "".join(body), "About Zainul Arkaan Alinsi: " + " ".join(BLURB))


# ------------------------------------------------------------------- stack
CARD_W, CARD_H = 300, 384


def card(cx, top, angle, title, items, edge=INK, delay=0.0):
    """One white-edged card with a grid of tool glyphs, rotated about its centre."""
    x = cx - CARD_W / 2
    cy = top + CARD_H / 2
    g = [f'<g class="bob" style="animation-delay:{delay}s"><g transform="rotate({angle} {cx:.1f} {cy:.1f})">',
         f'<rect x="{x - 9:.1f}" y="{top - 9:.1f}" width="{CARD_W + 18}" height="{CARD_H + 18}" rx="26" fill="{edge}"/>',
         f'<rect x="{x:.1f}" y="{top:.1f}" width="{CARD_W}" height="{CARD_H}" rx="18" fill="{CARD}"/>',
         f'<text x="{x + 24:.1f}" y="{top + 40:.1f}" class="cap" fill="{edge}">{esc(title.upper())}</text>',
         f'<text x="{x + CARD_W - 24:.1f}" y="{top + 40:.1f}" class="cap" text-anchor="end">{len(items):02d}</text>',
         f'<line x1="{x + 24:.1f}" y1="{top + 56:.1f}" x2="{x + CARD_W - 24:.1f}" y2="{top + 56:.1f}" stroke="{LINE}"/>']
    cols, cw, rh = 3, (CARD_W - 48) / 3, 76
    for i, (slug, label) in enumerate(items):
        gx = x + 24 + (i % cols) * cw + cw / 2
        gy = top + 78 + (i // cols) * rh
        g.append(glyph(slug, gx - 15, gy, 30, brand(THEMES['dark'], slug, CARD)))
        g.append(f'<text x="{gx:.1f}" y="{gy + 50:.1f}" font-family="{SANS}" font-size="12.5" fill="{MUTED}"'
                 f' text-anchor="middle">{esc(label)}</text>')
    g.append("</g></g>")
    return "".join(g)


def stack():
    groups = list(STACK.items())            # languages, frameworks, tools
    total = sum(len(v) for _, v in groups)
    cx = W / 2
    fx, fy, fw, fh = cx - 300, 392, 600, 220   # folder front
    body = [
        # ghost cards peeking out, like the reference
        f'<rect x="{cx - 290}" y="66" width="180" height="200" rx="22" fill="#1E1630"/>',
        f'<rect x="{cx + 110}" y="96" width="180" height="200" rx="22" fill="#10262A"/>',
        card(cx - 318, 104, -8, groups[0][0], groups[0][1], BLUE, 0),
        card(cx + 318, 104, 8, groups[2][0], groups[2][1], AMBER, -1.6),
        card(cx, 46, 0, groups[1][0], groups[1][1], VIOLET, -3.2),
        # folder back tab + front, flat greys with a soft top light
        f'<path d="M{fx} {fy + 24} q0 -24 24 -24 h190 q14 0 24 12 l18 22 h{fw - 276} q24 0 24 24 v{fh - 46}'
        f' q0 24 -24 24 h-{fw - 48} q-24 0 -24 -24 z" fill="#2A2A2A" opacity=".96"/>',
        f'<rect x="{fx}" y="{fy + 34}" width="{fw}" height="{fh - 10}" rx="24" fill="#232323" opacity=".97"/>',
        f'<rect x="{fx + 24}" y="{fy + 35}" width="{fw - 48}" height="1.2" fill="#FFFFFF" opacity=".18"/>',
        t(fx + 30, fy + 26, "*TECHSTACK.", "m", 15, CYAN),
        t(fx + 30, fy + 96, "the tools I reach for", "si", 30, MUTED),
        t(fx + 30, fy + 130, "web · mobile · data", "m", 14, DIM),
        # round arrow button
        f'<circle cx="{fx + fw - 62}" cy="{fy + fh - 54}" r="40" fill="url(#g)"/>',
        f'<circle cx="{fx + fw - 62}" cy="{fy + fh - 54}" r="34" fill="#1A1A1A"/>',
        f'<path d="M{fx + fw - 76} {fy + fh - 40} l26 -26 M{fx + fw - 72} {fy + fh - 66} h22 v22" stroke="#FAFAFA"'
        f' stroke-width="7" fill="none" stroke-linecap="square"/>',
        # title + pill
        f'<text x="{cx}" y="{fy + fh + 128}" font-family="{SANS}" font-size="92" font-weight="600" fill="url(#g)"'
        f' text-anchor="middle" letter-spacing="-1">TECH STACK</text>',
        f'<rect x="{cx - 118}" y="{fy + fh + 154}" width="236" height="46" rx="23" fill="#1C1C1C"/>',
        t(cx, fy + fh + 184, f"{total} tools · 2026", "m", 16, MUTED, "middle"),
    ]
    h = fy + fh + 236
    label = "Tech stack: " + "; ".join(f"{k}: " + ", ".join(lab for _, lab in v) for k, v in groups)
    return doc(h, "".join(body), label)


# ---------------------------------------------------------------- activity
# 2x2-dot ordered dither, 0..4 of the four dots lit — the hands' texture, as data.
RAMP = {1: "#2F8F55", 2: "#45C46F", 3: "#5EE07A", 4: "#C8FFD2"}
DITHER = {1: [(0, 0)], 2: [(0, 0), (1, 1)], 3: [(0, 0), (1, 1), (1, 0)], 4: [(0, 0), (1, 1), (1, 0), (0, 1)]}
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def dither_defs():
    out = ['<pattern id="d0" width="8" height="8" patternUnits="userSpaceOnUse">'
           f'<rect x="2" y="2" width="3" height="3" fill="{INK}" opacity=".18"/></pattern>']
    for lv, dots in DITHER.items():
        cells = "".join(f'<rect x="{dx * 4}" y="{dy * 4}" width="3" height="3" fill="{RAMP[lv]}"/>'
                        for dx, dy in dots)
        out.append(f'<pattern id="d{lv}" width="8" height="8" patternUnits="userSpaceOnUse">{cells}</pattern>')
    return "<defs>" + "".join(out) + "</defs>"


def stats_numbers(all_days, today):
    from build_activity import streaks
    total = sum(all_days.values())
    cur, _, longest, _ = streaks(all_days, today)
    best_d = max(all_days, key=lambda d: all_days[d]) if all_days else None
    return total, cur, longest, best_d, (all_days.get(best_d, 0) if best_d else 0)


def activity(created, recent, all_days, stamp, today):
    total, cur, longest, best_d, best_n = stats_numbers(all_days, today)
    days = [d for w in recent["weeks"] for d in w["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"])
    since = dt.date.fromisoformat(created[:10]).strftime("%b %Y")
    best_txt = dt.date.fromisoformat(best_d).strftime("%b %d").replace(" 0", " ") if best_d else "—"
    cols = [("Total", f"{total:,}", f"since {since}"),
            ("Last 12 months", f"{recent['totalContributions']:,}", f"{active} active days"),
            ("Current streak", str(cur), "days in a row"),
            ("Longest streak", str(longest), "days"),
            ("Best day", str(best_n), best_txt)]

    body = [dither_defs(), hair(60, 40, W - 60, 40),
            cap(60, 70, "Fig. 03 — Contributions"), cap(W - 60, 70, f"synced {stamp}", "end")]
    cw = (W - 120) / len(cols)
    for i, (k, v, sub) in enumerate(cols):
        x = 60 + i * cw
        if i:
            body.append(hair(x - 14, 100, x - 14, 214))
        body.append(cap(x, 118, k))
        body.append(t(x, 184, v, "s", 64, (PINK, VIOLET, GREEN, CYAN, AMBER)[i]))
        body.append(t(x, 210, sub, "m", 13, DIM))

    # the year as a dithered field: weeks run right, weekdays down
    weeks = recent["weeks"]
    cell, gap = 15, 5
    gw = len(weeks) * (cell + gap) - gap
    gx, gy = (W - gw) / 2, 268
    body.append(hair(60, 244, W - 60, 244, .9))
    last = None
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            x, y = gx + wi * (cell + gap), gy + d["weekday"] * (cell + gap)
            lv = LEVEL.get(d["contributionLevel"], 0)
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" fill="url(#d{lv})"/>')
            last = (x, y)
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.day <= 7 and wi < len(weeks) - 2:
            body.append(cap(gx + wi * (cell + gap), gy + 7 * (cell + gap) + 22, first.strftime("%b")))
    rows_h = 7 * (cell + gap) + 4
    body.append(f'<clipPath id="hc"><rect x="{gx - 4:.1f}" y="{gy - 4}" width="{gw + 8:.1f}" height="{rows_h}"/></clipPath>'
                f'<g clip-path="url(#hc)"><rect class="scan" x="0" y="{gy - 4}" width="90" height="{rows_h}"'
                f' fill="url(#g)" opacity=".22"/></g>')
    if last:                                  # today: a blinking outline
        body.append(f'<rect class="blink" x="{last[0] - 3:.1f}" y="{last[1] - 3:.1f}" width="{cell + 6}"'
                    f' height="{cell + 6}" fill="none" stroke="{GREEN}" stroke-width="2"/>')
    for i, lab in enumerate(("Mon", "Wed", "Fri")):
        body.append(cap(gx - 12, gy + (1 + 2 * i) * (cell + gap) + 12, lab, "end", DIM))
    ly = gy + 7 * (cell + gap) + 60
    body.append(cap(W - 60 - 6 * 26 - 60, ly, "less", "end", DIM))
    for lv in range(5):
        body.append(f'<rect x="{W - 60 - 6 * 26 - 48 + lv * 26}" y="{ly - 14}" width="{cell}" height="{cell}"'
                    f' fill="url(#d{lv})"/>')
    body.append(cap(W - 60, ly, "more", "end", DIM))
    body.append(cap(60, ly, f"{recent['totalContributions']:,} contributions in the last year"))
    h = ly + 34
    return doc(h, "".join(body), f"Contributions: {total:,} total, current streak {cur} days, longest {longest}, "
                                  f"best day {best_n}.")


# ------------------------------------------------------------------ footer
def footer():
    body = [hair(60, 30, W - 60, 30), ticks(40, 14, W - 80, 172),
            t(W / 2, 116, "Thanks for stopping by.", "si", 58, "url(#g)", "middle"),
            cap(W / 2, 156, "Zainul Arkaan Alinsi — 2026 — see you in the next commit", "middle"),
            f'<rect class="blink" x="{W / 2 + 246}" y="78" width="14" height="40" fill="{CYAN}"/>']
    return doc(210, "".join(body), "Thanks for stopping by")


def build_static():
    """No network: about, stack, footer."""
    made = []
    for name, fn in (("about", about), ("stack", stack), ("footer", footer)):
        (ASSETS / f"{name}-dark.svg").write_text(fn(), encoding="utf-8")
        made.append(f"{name}-dark.svg")
    return made


if __name__ == "__main__":
    for n in build_static():
        print("wrote", n)
