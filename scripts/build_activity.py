"""GitHub activity panel: glass stat cards + an isometric voxel contribution world.

Every contribution day is a tower of blocks coloured by GitHub's own contribution
level, standing on a floating chunk of ground — grass, dirt, stone, a few ores.
Clouds drift over the back row and today's column gets a beacon.

    GITHUB_TOKEN=... python scripts/build_activity.py
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ASSETS, THEMES, Iso, glass, line, mix, pixel_text, poly, ramp, rect, shade,
                   svg_doc, text, ticks)

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]

W = 1200
PAD = 34
S = 19.0                      # cell size
WEEK = (S * .94, S * .155)    # weeks run right, drifting gently down
DAY = (-S * .44, S * .640)    # weekdays run toward the viewer
BLOCK = S * .50               # one voxel of height
MAX_BLOCKS = 9
PLINTH = 34                   # how deep the chunk of ground is cut

CAL = ("contributionCalendar{ totalContributions weeks{ contributionDays{"
       " date weekday contributionCount contributionLevel } } }")

CSS = ("@keyframes bob{0%,100%{opacity:1}50%{opacity:.35}}"
       "@keyframes beam{0%,100%{opacity:.9}50%{opacity:.45}}"
       "@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}"
       "@keyframes tw{0%,100%{opacity:1}50%{opacity:.2}}"
       ".tw{animation:tw 3s ease-in-out infinite}"
       "@keyframes drift{0%,100%{transform:translateX(0)}50%{transform:translateX(34px)}}"
       ".bob{animation:bob 2.6s ease-in-out infinite}"
       ".beam{animation:beam 2.2s ease-in-out infinite}"
       ".fl{animation:fl 3.4s ease-in-out infinite}"
       ".drift{animation:drift 22s ease-in-out infinite}"
       "@media (prefers-reduced-motion:reduce){.bob,.beam,.fl,.drift,.tw{animation:none}}")


# ------------------------------------------------------------------------ data
def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": "profile-activity"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def fetch():
    user = gql("query($login:String!){ user(login:$login){ createdAt contributionsCollection{"
               " contributionYears " + CAL + " } } }", login=LOGIN)
    recent = user["contributionsCollection"]["contributionCalendar"]
    all_days = {}
    for year in user["contributionsCollection"]["contributionYears"]:
        cal = gql("query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){"
                  " contributionsCollection(from:$from,to:$to){ " + CAL + " } } }",
                  login=LOGIN, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
        for week in cal["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                all_days[d["date"]] = d["contributionCount"]
    return user["createdAt"], recent, all_days


def streaks(days, today):
    longest, best, run, start = 0, (None, None), 0, None
    for d in sorted(k for k in days if k <= today.isoformat()):
        if days[d]:
            run += 1
            start = start or d
            if run > longest:
                longest, best = run, (start, d)
        else:
            run, start = 0, None
    cursor = today if days.get(today.isoformat()) else today - dt.timedelta(days=1)  # today isn't over yet
    end, cur = cursor, 0
    while days.get(cursor.isoformat()):
        cur += 1
        cursor -= dt.timedelta(days=1)
    return cur, (cursor + dt.timedelta(days=1), end), longest, best


def short(d):
    if isinstance(d, str):
        d = dt.date.fromisoformat(d)
    return f"{d.strftime('%b')} {d.day}" if d else ""


# -------------------------------------------------------------------- geometry
def pt(w, d, ox, oy, h=0.0):
    return ox + w * WEEK[0] + d * DAY[0], oy + w * WEEK[1] + d * DAY[1] - h


def prism(a, b, c, e, z0, z1, ox, oy, top, left, right):
    """Box over the footprint [a,c] x [b,e] from height z0 to z1 (px): the three
    faces this camera can see, flat-shaded."""
    P = lambda u, v, z: pt(u, v, ox, oy, z)
    return "".join([
        poly([P(a, e, z0), P(c, e, z0), P(c, e, z1), P(a, e, z1)], left),
        poly([P(c, b, z0), P(c, e, z0), P(c, e, z1), P(c, b, z1)], right),
        poly([P(a, b, z1), P(c, b, z1), P(c, e, z1), P(a, e, z1)], top),
    ])


def tower(w, d, ox, oy, n_blocks, col, t, gap=.07):
    """One day: a column of blocks in its level colour, seams between the blocks,
    a lit rim on the cap and a little ambient occlusion where it meets the ground."""
    a, b, c, e = w + gap, d + gap, w + 1 - gap, d + 1 - gap
    h = n_blocks * BLOCK
    P = lambda u, v, z: pt(u, v, ox, oy, z)
    top = mix(col, "#FFFFFF", .10) if t["px_shadow"] > .3 else col
    parts = [prism(a, b, c, e, 0, h, ox, oy, top, shade(col, .80), shade(col, .58))]
    # contact shadow at the foot of the column
    ao = min(BLOCK * .8, h)
    parts.append(poly([P(a, e, 0), P(c, e, 0), P(c, b, 0), P(c, b, ao), P(c, e, ao), P(a, e, ao)],
                      t["shadow"], ' opacity=".22"'))
    if n_blocks > 1:
        seg = []
        for i in range(1, n_blocks):
            z = i * BLOCK
            p0, p1, p2 = P(a, e, z), P(c, e, z), P(c, b, z)
            seg.append(f"M{p0[0]:.1f} {p0[1]:.1f}L{p1[0]:.1f} {p1[1]:.1f}L{p2[0]:.1f} {p2[1]:.1f}")
        parts.append(f'<path d="{"".join(seg)}" stroke="{t["shadow"]}" stroke-width=".8"'
                     f' opacity=".32" fill="none"/>')
    # lit rim along the two near edges of the cap
    r0, r1, r2 = P(a, e, h), P(c, e, h), P(c, b, h)
    parts.append(f'<path d="M{r0[0]:.1f} {r0[1]:.1f}L{r1[0]:.1f} {r1[1]:.1f}L{r2[0]:.1f} {r2[1]:.1f}"'
                 f' stroke="{mix(col, "#FFFFFF", .5)}" stroke-width=".9" opacity=".75" fill="none"/>')
    # two pixel flecks on the cap, deterministic — texture, not noise
    seed = (int(w) * 7 + int(d) * 13) % 5
    for k, (fu, fv) in enumerate(((.24, .30), (.62, .66), (.44, .18), (.70, .34), (.30, .62))[seed:seed + 2]):
        u0, v0 = a + (c - a) * fu, b + (e - b) * fv
        u1, v1 = u0 + (c - a) * .17, v0 + (e - b) * .17
        parts.append(poly([P(u0, v0, h), P(u1, v0, h), P(u1, v1, h), P(u0, v1, h)],
                          shade(col, 1.16 if k else .84)))
    return "".join(parts)


def cast(w, d, ox, oy, t, n_blocks, gap=.07):
    """A footprint cast down-right, longer for taller towers, so they stand on
    the ground instead of hovering over it."""
    a, b, c, e = w + gap, d + gap, w + 1 - gap, d + 1 - gap
    k = 3 + n_blocks * 1.1
    pts = [pt(a, b, ox, oy), pt(c, b, ox, oy), pt(c, e, ox, oy), pt(a, e, ox, oy)]
    return poly([(x + k, y + k * .55) for x, y in pts], t["shadow"], ' opacity=".20"')


def chip(cx, y, label, t, fg, size=11.5):
    """A label that has to stay readable over whatever towers are behind it."""
    w = len(label) * size * .601 + 18
    return ("".join([
        rect(cx - w / 2, y - size - 3, w, size + 11, fill=t["bg"], r=5, op=.86),
        rect(cx - w / 2 + .5, y - size - 2.5, w - 1, size + 10, r=5, stroke=fg, op=.55),
        text(cx, y, label, size, fg, anchor="middle", weight=600),
    ]))


def chunk(t, ox, oy, w0, w1, d0, d1, ground):
    """The slab the world sits on, cut like a Minecraft chunk: a grass lip, a
    band of dirt, stone underneath with a few ores showing on the cut faces."""
    P = lambda u, v, z=0: pt(u, v, ox, oy, z)
    grass = mix(t["bg"], t["green"], .55)
    dirt = mix(t["bg"], t["amber"], .42)
    stone = mix(t["bg"], t["ink"], .30)
    bands = ((0, 5, grass), (5, 15, dirt), (15, PLINTH, stone))
    out = [poly([P(w0, d0), P(w1, d0), P(w1, d1), P(w0, d1)], ground)]
    for z0, z1, col in bands:
        out.append(poly([P(w0, d1, -z0), P(w1, d1, -z0), P(w1, d1, -z1), P(w0, d1, -z1)], shade(col, .78)))
        out.append(poly([P(w1, d0, -z0), P(w1, d1, -z0), P(w1, d1, -z1), P(w1, d0, -z1)], shade(col, .56)))
    # ores: fixed positions along the front cut, so every rebuild looks the same
    ores = ("amber", "blue", "red", "green", "violet")
    for i in range(26):
        u = w0 + 1.2 + ((i * 37) % 97) / 97 * (w1 - w0 - 2.4)
        z = 18 + (i * 11) % 13
        col = mix(t[ores[i % len(ores)]], t["bg"], .10)
        out.append(poly([P(u, d1, -z), P(u + .28, d1, -z), P(u + .28, d1, -z - 3), P(u, d1, -z - 3)], col))
    for i in range(4):
        v = d0 + 1 + i * 1.7
        z = 19 + (i * 7) % 11
        col = shade(t[ores[(i + 2) % len(ores)]], .8)
        out.append(poly([P(w1, v, -z), P(w1, v + .5, -z), P(w1, v + .5, -z - 3), P(w1, v, -z - 3)], col))
    # the very bottom edge in bedrock black
    out.append(poly([P(w0, d1, -PLINTH + 3), P(w1, d1, -PLINTH + 3), P(w1, d1, -PLINTH), P(w0, d1, -PLINTH)],
                    t["shadow"], ' opacity=".35"'))
    return "".join(out)


def cloud(t, ox, oy, cells, w, d, z):
    """A flat voxel cloud floating at height z over cell (w, d)."""
    dark = t["px_shadow"] > .3
    top = "#FFFFFF" if dark else "#FFFFFF"
    side = mix("#FFFFFF", t["bg"], .35 if dark else .12)
    cells = sorted(cells, key=lambda c: (c[0] + c[1], c[1]))
    body = "".join(prism(w + cw, d + cd, w + cw + 1, d + cd + 1, z, z + 7, ox, oy, top, side, shade(side, .9))
                   for cw, cd in cells)
    return f'<g opacity="{.20 if dark else .95}">{body}</g>'


# --------------------------------------------------------------------- drawing
def stat_cards(t, stats, y, accents):
    cw = (W - PAD * 2 - 12 * (len(stats) - 1)) / len(stats)
    ch = 104
    out = []
    for i, (value, name, sub) in enumerate(stats):
        x = PAD + (cw + 12) * i
        col = accents[i % len(accents)]
        out.append(glass(f"stat{i}", x, y, cw, ch, t, r=14,
                         glows=[(.16, .12, cw * .52, col)]))
        out.append(rect(x + 14, y + 15, 3, 13, fill=t[col]))
        out.append(text(x + 24, y + 26, name.upper(), 10.5, t["muted"], weight=600, ls="1.4"))
        out.append(pixel_text(value, x + 15, y + 40, 4, t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"]))
        out.append(text(x + 15, y + 90, sub, 11.5, t["muted"]))
        # a small floating block per card, one accent each — the page's 3D motif
        iso = Iso(x + cw - 30, y + 58, 11)
        out.append(f'<ellipse cx="{x + cw - 30:.1f}" cy="{y + 80:.1f}" rx="11" ry="3.5"'
                   f' fill="{t["shadow"]}" opacity=".22"/>')
        out.append(f'<g class="fl" style="animation-delay:{-i * .6:.1f}s">'
                   + iso.box(-.5, -.5, 0, 1, 1, 1, t[col], top=mix(t[col], "#FFFFFF", .22)) + "</g>")
    return "".join(out), ch


def window_chrome(t, x, y, w, h, title, right, accent):
    out = [glass("world", x, y, w, h, t, r=16,
                 glows=[(.10, .18, w * .30, accent), (.86, .78, w * .26, "blue"), (.55, .05, w * .2, "violet")])]
    out.append(line(x, y + 30, x + w, y + 30, t["line"], 1, .9))
    for i, c in enumerate((t["red"], t["amber"], t["green"])):
        out.append(rect(x + 14 + i * 13, y + 12, 7, 7, fill=c, op=.85))
    out.append(text(x + 62, y + 20, title, 11.5, t["muted"]))
    out.append(text(x + w - 14, y + 20, right, 11.5, t["muted"], anchor="end"))
    out.append(ticks(x + 7, y + 37, w - 14, h - 50, t["ink"], 8, 1, .18))
    return "".join(out)


def render(theme, created, recent, all_days, stamp):
    t = THEMES[theme]
    cells = ramp(t, "green")
    ground = mix(t["bg"], t["green"], .09 if t["px_shadow"] > .3 else .07)
    today = dt.datetime.now(TZ).date()
    cur, cur_range, longest, best_range = streaks(all_days, today)
    weeks = recent["weeks"]
    n = len(weeks)
    days = [(w, d["weekday"], d) for w, wk in enumerate(weeks) for d in wk["contributionDays"]]
    peak = max(days, key=lambda x: x[2]["contributionCount"])
    top = max(1, peak[2]["contributionCount"])
    latest = max(d["date"] for _, _, d in days)
    active = sum(1 for _, _, d in days if d["contributionCount"])

    y = PAD
    stats = [
        (f"{sum(all_days.values()):,}", "Total", f"since {dt.date.fromisoformat(created[:10]).strftime('%b %Y')}"),
        (f"{recent['totalContributions']:,}", "Last 12 months", f"{active} active days"),
        (f"{cur}", "Current streak", f"{short(cur_range[0])} - {short(cur_range[1])}" if cur else "start one today"),
        (f"{longest}", "Longest streak", f"{short(best_range[0])} - {short(best_range[1])}"),
        (f"{top}", "Best day", short(peak[2]["date"])),
    ]
    cards, ch = stat_cards(t, stats, y, ACCENT_ORDER)
    y += ch + 16

    # ---- the world -------------------------------------------------------
    # One 137-commit day against a median of four made every other tower a stub, so
    # height is a log scale normalised to the 90th percentile rather than the peak.
    busy = sorted(d["contributionCount"] for _, _, d in days if d["contributionCount"])
    ref = max(3, busy[int(len(busy) * .9)] if busy else 3)

    def stack(cnt):
        if not cnt:
            return 0
        return 1 + round(min(1.0, math.log1p(cnt) / math.log1p(ref)) * (MAX_BLOCKS - 1))

    # Reserve exactly enough sky for the header band: no tower may reach into it.
    sky = y + 58 + 52                       # heading + subtitle + best-day callout
    ox = PAD + 120
    oy = max(y + 120, sky + max(stack(d["contributionCount"]) * BLOCK - (w * WEEK[1] + wd * DAY[1])
                                for w, wd, d in days))
    w0, w1, d0, d1 = -.55, n + .55, -.55, 7.55
    month_base = pt(n - 3.5, d1, ox, oy)[1] + PLINTH + 19
    win_h = int(max(pt(w1, d1, ox, oy)[1] + PLINTH + 18, month_base) - y + 26)
    H = int(y + win_h + PAD)

    body = [rect(0, 0, W, H, fill=t["bg"]), cards]
    body.append(window_chrome(t, PAD, y, W - PAD * 2, win_h,
                              "~/contributions --last 12mo --render iso", f"synced {stamp}", "green"))

    head_y = y + 58
    body.append(pixel_text("CONTRIBUTION WORLD", PAD + 22, head_y - 10, 3, t["ink"],
                           shadow=t["shadow"], shadow_op=t["px_shadow"]))
    body.append(text(PAD + 22, head_y + 22, f"{recent['totalContributions']:,} contributions · "
                                            f"{active} active days · taller stack = busier day",
                     11.5, t["muted"]))

    # legend as the same blocks the world is built from
    lx = W - PAD - 176
    body.append(text(lx - 16, head_y + 6, "less", 11, t["muted"], anchor="end"))
    for i, c in enumerate([ground] + cells[1:]):
        iso = Iso(lx + i * 26, head_y + 1, 8)
        body.append(iso.box(-.5, -.5, -.4, 1, 1, .4 + i * .35, c if i else mix(t["bg"], t["ink"], .16)))
    body.append(text(lx + len(cells) * 26 - 6, head_y + 6, "more", 11, t["muted"]))

    # ---- sky: clouds drifting over the back row by day, stars at night
    if t["px_shadow"] > .3:
        stars = []
        for i in range(34):
            sx = PAD + 70 + ((i * 131) % 1000) * .98
            sy = sky - 18 + ((i * 53) % 71) * 1.1
            wb = (sx - ox) / WEEK[0]                          # the back edge under this star
            if sy > pt(wb, d0, ox, oy)[1] - 16 or sy < sky - 20 or (sx < PAD + 470 and sy < sky + 4):
                continue
            size = 2 if i % 4 else 3
            stars.append(f'<rect class="tw" style="animation-delay:{-(i * .37) % 3:.2f}s" x="{sx:.0f}"'
                         f' y="{sy:.0f}" width="{size}" height="{size}" fill="{t["ink"]}"'
                         f' opacity="{.35 + (i % 3) * .2:.2f}"/>')
        body.append("".join(stars))
    else:
        for cw_, cells_, dur in ((14, ((0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (3, 1)), 22),
                                 (32, ((0, 0), (1, 0), (1, 1), (2, 1)), 28)):
            z = max(18, pt(cw_, -4.5, ox, oy)[1] - (sky + 40))
            body.append(f'<g class="drift" style="animation-duration:{dur}s">'
                        f'{cloud(t, ox, oy, cells_, cw_, -4.5, z)}</g>')

    # ---- the ground: a floating chunk with the calendar scored into its top
    lo = pt(w0, d1, ox, oy)[0], pt(w1, d0, ox, oy)[0]
    cx_, cy_ = (lo[0] + lo[1]) / 2, pt(w1, d1, ox, oy)[1] - 6
    body.append(f'<ellipse cx="{cx_:.1f}" cy="{cy_:.1f}" rx="{(lo[1] - lo[0]) * .46:.1f}" ry="26"'
                f' fill="{t["shadow"]}" opacity="{.35 if t["px_shadow"] > .3 else .10}" filter="url(#blur)"/>')
    body.append(chunk(t, ox, oy, w0, w1, d0, d1, ground))
    weekly, monthly, last = [], [], None
    for w in range(n + 1):
        a, b = pt(w, d0, ox, oy), pt(w, d1, ox, oy)
        seg = f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}"
        month = dt.date.fromisoformat(weeks[min(w, n - 1)]["contributionDays"][0]["date"]).month
        (monthly if month != last and w < n else weekly).append(seg)
        if w < n:
            last = month
    for d in range(8):
        a, b = pt(w0, d, ox, oy), pt(w1, d, ox, oy)
        weekly.append(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}")
    body.append(f'<path d="{"".join(weekly)}" stroke="{t["ink"]}" stroke-width=".5"'
                f' opacity="{t["grid"] * 1.2:.3f}" fill="none"/>')
    body.append(f'<path d="{"".join(monthly)}" stroke="{t["ink"]}" stroke-width=".8"'
                f' opacity="{t["grid"] * 2.8:.3f}" fill="none"/>')

    # ---- towers, painter's order: far to near
    lit = [(w, wd, day) for w, wd, day in days if day["contributionCount"]]
    body.extend(cast(w, wd, ox, oy, t, stack(day["contributionCount"])) for w, wd, day in lit)
    beacon = peak_top = None
    for w, wd, day in sorted(lit, key=lambda x: (x[0] + x[1], x[1])):
        blocks = stack(day["contributionCount"])
        col = cells[LEVELS.index(day["contributionLevel"])]
        body.append(tower(w, wd, ox, oy, blocks, col, t))
        if day["date"] == latest:
            beacon = (w, wd, blocks)
        if day["date"] == peak[2]["date"]:
            peak_top = pt(w + .5, wd + .5, ox, oy, blocks * BLOCK)

    # Markers go on last, above every tower, each on its own backing plate.
    if beacon:
        w, wd, blocks = beacon
        bx, by = pt(w + .5, wd + .5, ox, oy, blocks * BLOCK)
        beam = max(52, by - (sky + 34))
        g = t["green"]
        body.append(f'<g class="beam">'
                    f'<rect x="{bx - 9:.1f}" y="{by - beam:.1f}" width="18" height="{beam:.1f}" fill="{g}"'
                    f' opacity=".10" filter="url(#glow)"/>'
                    f'<rect x="{bx - 4:.1f}" y="{by - beam:.1f}" width="8" height="{beam:.1f}" fill="{g}" opacity=".28"/>'
                    f'<rect x="{bx - 1.5:.1f}" y="{by - beam:.1f}" width="3" height="{beam:.1f}" fill="{g}" opacity=".95"/>'
                    f'</g>')
        iso = Iso(bx, by - beam - 4, 6)
        body.append(iso.box(-.5, -.5, 0, 1, 1, 1, g, top=mix(g, "#FFFFFF", .35)))
        body.append(chip(min(max(bx, PAD + 60), W - PAD - 60), by - beam - 20, "today", t, t["green"], 10.5))

    if peak_top:
        px, py = peak_top
        ly = max(sky + 12, py - 46)                    # never climb into the window header
        if ly < py - 18:
            body.append(line(px, py - 6, px, ly + 8, t["amber"], 1.2, .9))
            body.append(f'<circle cx="{px:.1f}" cy="{py - 4:.1f}" r="3" fill="{t["amber"]}"/>')
        body.append(chip(min(max(px, PAD + 150), W - PAD - 150), ly,
                         f"best day · {top} on {short(peak[2]['date'])}", t, t["amber"]))

    # ---- axis labels, hugging the slab
    last = None
    for w, wk in enumerate(weeks):
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last and w < n - 2:
            x, yy = pt(w + .5, d1, ox, oy)
            body.append(text(x, yy + PLINTH + 19, first.strftime("%b").upper(), 10, t["muted"],
                             anchor="middle", ls=".6"))
            last = first.month
    for d, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        x, yy = pt(w0, d + .5, ox, oy)
        body.append(text(x - 10, yy + 4, name, 10, t["muted"], anchor="end", ls=".6"))

    # ---- world plaque, in the slab's shadow
    plq_y = y + win_h - 54
    for i, (k, v) in enumerate((("SEED", LOGIN.lower()), ("BIOME", f"commits · {n}w x 7d"))):
        body.append(text(PAD + 22, plq_y + i * 16, k, 9.5, t["muted"], weight=600, ls="1.2"))
        body.append(text(PAD + 74, plq_y + i * 16, v, 10.5, t["ink"]))
    defs = '<filter id="glow" x="-200%" y="-10%" width="500%" height="120%"><feGaussianBlur stdDeviation="5"/></filter>'
    return svg_doc(W, H, "".join(body), defs=defs,
                   label=(f"GitHub activity: {sum(all_days.values()):,} contributions, "
                          f"current streak {cur} days, longest {longest} days, synced {stamp}"),
                   css=CSS)


ACCENT_ORDER = ("green", "blue", "amber", "violet", "red")

if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    created, recent, all_days = fetch()
    stamp = dt.datetime.now(TZ).strftime("%d %b %Y %H:%M WIB")
    for name in THEMES:
        (ASSETS / f"activity-{name}.svg").write_text(render(name, created, recent, all_days, stamp), encoding="utf-8")
        print("wrote", f"activity-{name}.svg")
