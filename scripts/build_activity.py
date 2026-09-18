"""GitHub activity panel: glass stat cards + an isometric voxel contribution world.

Every contribution day is a tower of blocks — dirt below, a grass cap on top whose
green step comes from GitHub's own contribution level. Today's column gets a beacon.

    GITHUB_TOKEN=... python scripts/build_activity.py
"""
import datetime as dt
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (ASSETS, PULSE_CSS, THEMES, glass, line, mix, pixel_text, poly, ramp, rect,
                   shade, slot, svg_doc, text, ticks)

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]

W = 1200
PAD = 34
S = 19.0                      # cell size
WEEK = (S * .94, S * .155)    # weeks run right, drifting gently down
DAY = (-S * .44, S * .640)    # weekdays run toward the viewer
BLOCK = S * .60               # one voxel of height
MAX_BLOCKS = 6

CAL = ("contributionCalendar{ totalContributions weeks{ contributionDays{"
       " date weekday contributionCount contributionLevel } } }")


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


def tower(w, d, ox, oy, n_blocks, grass, dirt, t, gap=.06):
    """One column: extruded prism + per-block seams + a grass rim on the cap."""
    a, b, c, e = w + gap, d + gap, w + 1 - gap, d + 1 - gap
    h = n_blocks * BLOCK
    left = shade(dirt, .70)
    right = shade(dirt, .50)
    parts = [
        poly([pt(a, e, ox, oy), pt(c, e, ox, oy), pt(c, e, ox, oy, h), pt(a, e, ox, oy, h)], left),
        poly([pt(c, b, ox, oy), pt(c, e, ox, oy), pt(c, e, ox, oy, h), pt(c, b, ox, oy, h)], right),
    ]
    # grass rim: the cap block's soil is green on the sides too
    rim = min(BLOCK * .34, h)
    parts += [
        poly([pt(a, e, ox, oy, h - rim), pt(c, e, ox, oy, h - rim), pt(c, e, ox, oy, h), pt(a, e, ox, oy, h)],
             shade(grass, .72)),
        poly([pt(c, b, ox, oy, h - rim), pt(c, e, ox, oy, h - rim), pt(c, e, ox, oy, h), pt(c, b, ox, oy, h)],
             shade(grass, .52)),
    ]
    # seams between stacked blocks, one path for the whole column
    if n_blocks > 1:
        seg = []
        for i in range(1, n_blocks):
            z = i * BLOCK
            p0, p1, p2 = pt(a, e, ox, oy, z), pt(c, e, ox, oy, z), pt(c, b, ox, oy, z)
            seg.append(f"M{p0[0]:.1f} {p0[1]:.1f}L{p1[0]:.1f} {p1[1]:.1f}L{p2[0]:.1f} {p2[1]:.1f}")
        parts.append(f'<path d="{"".join(seg)}" stroke="{t["shadow"]}" stroke-width=".7"'
                     f' opacity=".30" fill="none"/>')
    parts.append(poly([pt(a, b, ox, oy, h), pt(c, b, ox, oy, h), pt(c, e, ox, oy, h), pt(a, e, ox, oy, h)], grass))
    # two pixel flecks on the cap, deterministic — grass texture, not noise
    seed = (int(w) * 7 + int(d) * 13) % 5
    for k, (fu, fv) in enumerate(((.24, .30), (.62, .66), (.44, .18), (.70, .34), (.30, .62))[seed:seed + 2]):
        u0, v0 = a + (c - a) * fu, b + (e - b) * fv
        u1, v1 = u0 + (c - a) * .17, v0 + (e - b) * .17
        parts.append(poly([pt(u0, v0, ox, oy, h), pt(u1, v0, ox, oy, h), pt(u1, v1, ox, oy, h), pt(u0, v1, ox, oy, h)],
                          shade(grass, 1.16 if k else .84)))
    return "".join(parts)


def plate(w, d, ox, oy, fill, gap=.06):
    a, b, c, e = w + gap, d + gap, w + 1 - gap, d + 1 - gap
    return poly([pt(a, b, ox, oy), pt(c, b, ox, oy), pt(c, e, ox, oy), pt(a, e, ox, oy)], fill)


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
    return "".join(out), ch


def window_chrome(t, x, y, w, h, title, right, accent):
    out = [glass("world", x, y, w, h, t, r=16,
                 glows=[(.10, .18, w * .30, accent), (.86, .78, w * .26, "blue")])]
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
    dirt = mix(t["bg"], t["amber"], .46)
    stone = [mix(t["bg"], t["ink"], k) for k in (.085, .17, .25)]
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
    # Reserve exactly enough sky for the header band: no tower may reach into it.
    def stack(cnt):
        return 1 + round((cnt / top) ** .55 * (MAX_BLOCKS - 1)) if cnt else 0

    sky = y + 58 + 52                       # heading + subtitle + best-day callout
    ox = PAD + 120
    oy = max(y + 120, sky + max(stack(d["contributionCount"]) * BLOCK - (w * WEEK[1] + wd * DAY[1])
                                for w, wd, d in days))
    w0, w1, d0, d1 = -.55, n + .55, -.55, 7.55
    plinth = 13                                   # the world sits on a slab, not on the panel floor
    month_base = pt(n - 3.5, d1, ox, oy)[1] + plinth + 15
    win_h = int(max(pt(w1, d1, ox, oy)[1] + plinth, month_base) - y + 26)
    H = int(y + win_h + PAD)

    body = [rect(0, 0, W, H, fill=t["bg"]), cards]
    body.append(window_chrome(t, PAD, y, W - PAD * 2, win_h,
                              "~/contributions --last 12mo --render iso", f"synced {stamp}", "green"))

    head_y = y + 58
    body.append(pixel_text("CONTRIBUTION WORLD", PAD + 22, head_y - 10, 3, t["ink"],
                           shadow=t["shadow"], shadow_op=t["px_shadow"]))
    body.append(text(PAD + 22, head_y + 22, f"{recent['totalContributions']:,} contributions \u00b7 "
                                            f"{active} active days \u00b7 taller stack = busier day",
                     11.5, t["muted"]))

    lx = W - PAD - 190
    body.append(text(lx - 12, head_y + 6, "less", 11, t["muted"], anchor="end"))
    for i, c in enumerate(cells):
        body.append(slot(lx + i * 26, head_y - 8, 20, 20, t, depth=2, fill=c))
    body.append(text(lx + len(cells) * 26 + 4, head_y + 6, "more", 11, t["muted"]))

    # ---- plinth: a slab of stone with the calendar grid scored into the top
    body.append(poly([pt(w0, d0, ox, oy), pt(w1, d0, ox, oy), pt(w1, d1, ox, oy), pt(w0, d1, ox, oy)], stone[0]))
    grid = []
    for w in range(0, n + 1, 4):
        a, b = pt(w, d0, ox, oy), pt(w, d1, ox, oy)
        grid.append(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}")
    for d in range(8):
        a, b = pt(w0, d, ox, oy), pt(w1, d, ox, oy)
        grid.append(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}")
    body.append(f'<path d="{"".join(grid)}" stroke="{t["ink"]}" stroke-width=".6"'
                f' opacity="{t["grid"] * 1.5:.3f}" fill="none"/>')
    for pts, col in ((((w0, d1), (w1, d1)), stone[1]), (((w1, d0), (w1, d1)), stone[2])):
        (ua, va), (ub, vb) = pts
        a, b = pt(ua, va, ox, oy), pt(ub, vb, ox, oy)
        body.append(poly([a, b, (b[0], b[1] + plinth), (a[0], a[1] + plinth)], col))

    # ---- towers, painter's order: far to near
    beacon = peak_top = None
    for w, wd, day in sorted(days, key=lambda x: (x[0] + x[1], x[1])):
        cnt = day["contributionCount"]
        if not cnt:
            body.append(plate(w, wd, ox, oy, cells[0]))
            continue
        blocks = stack(cnt)
        body.append(tower(w, wd, ox, oy, blocks, cells[LEVELS.index(day["contributionLevel"])], dirt, t))
        if day["date"] == latest:
            beacon = (w, wd, blocks)
        if day["date"] == peak[2]["date"]:
            peak_top = pt(w + .5, wd + .5, ox, oy, blocks * BLOCK)

    if beacon:
        w, wd, blocks = beacon
        bx, by = pt(w + .5, wd + .5, ox, oy, blocks * BLOCK)
        body.append(f'<g class="bob"><rect x="{bx - 2.5:.1f}" y="{by - 44:.1f}" width="5" height="44"'
                    f' fill="{t["green"]}" opacity=".5"/>'
                    f'<rect x="{bx - 5:.1f}" y="{by - 56:.1f}" width="10" height="10" fill="{t["green"]}"/></g>')
        body.append(text(bx, by - 64, "today", 10.5, t["green"], anchor="middle", weight=600))

    if peak_top:
        px, py = peak_top
        ly = max(head_y + 44, py - 44)                 # never climb into the window header
        if ly < py - 14:
            body.append(line(px, py - 6, px, ly + 10, t["muted"], 1.1, .8))
            body.append(rect(px - 3, ly + 5, 6, 6, fill=t["amber"]))
        px = min(max(px, PAD + 130), W - PAD - 130)
        body.append(text(px, ly, f"best day \u00b7 {top} on {short(peak[2]['date'])}", 11.5, t["ink"],
                         anchor="middle", weight=600))

    # ---- axis labels, hugging the slab
    last = None
    for w, wk in enumerate(weeks):
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last and w < n - 2:
            x, yy = pt(w + .5, d1, ox, oy)
            body.append(text(x, yy + plinth + 15, first.strftime("%b").upper(), 10, t["muted"],
                             anchor="middle", ls=".6"))
            last = first.month
    for d, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        x, yy = pt(w0, d + .5, ox, oy)
        body.append(text(x - 10, yy + 4, name, 10, t["muted"], anchor="end", ls=".6"))

    # ---- world plaque, in the slab's shadow
    plq_y = y + win_h - 54
    for i, (k, v) in enumerate((("SEED", LOGIN.lower()), ("BIOME", f"commits \u00b7 {n}w x 7d"))):
        body.append(text(PAD + 22, plq_y + i * 16, k, 9.5, t["muted"], weight=600, ls="1.2"))
        body.append(text(PAD + 74, plq_y + i * 16, v, 10.5, t["ink"]))
    return svg_doc(W, H, "".join(body),
                   label=(f"GitHub activity: {sum(all_days.values()):,} contributions, "
                          f"current streak {cur} days, longest {longest} days, synced {stamp}"),
                   css=PULSE_CSS)


ACCENT_ORDER = ("green", "blue", "amber", "violet", "red")

if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    created, recent, all_days = fetch()
    stamp = dt.datetime.now(TZ).strftime("%d %b %Y %H:%M WIB")
    for name in THEMES:
        (ASSETS / f"activity-{name}.svg").write_text(render(name, created, recent, all_days, stamp), encoding="utf-8")
        print("wrote", f"activity-{name}.svg")
