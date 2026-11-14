"""Contribution World + Player Stats.

Contribution World: every day of the last twelve months is a tower of textured
blocks on a floating chunk of ground, cut like a Minecraft chunk: grass, dirt,
stone with ores, bedrock. Taller tower = busier day; the block type steps up
with GitHub's own contribution level. Day sky in light mode, night in dark.

Player Stats: the numbers, as a Minecraft GUI card: hearts for the current
streak, an XP bar whose level comes from lifetime contributions, and a stat
list with a block icon per row.

    GITHUB_TOKEN=... python scripts/build_activity.py
    PROFILE_FIXTURE=fixture.json python scripts/build_activity.py   # offline
"""
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mc  # noqa: E402
from gui import (AQUA, HALF, LABEL, W, YELLOW, card_frame, chip, heart, inset, label, mc_pixel, mc_text,  # noqa: E402
                 pixel_text, pixel_width, rect, svg)
from PIL import Image, ImageChops, ImageDraw  # noqa: E402

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
MATERIAL = [None, "grass", "planks", "gold_block", "emerald_block"]
MATERIAL_NAME = ["", "grass", "planks", "gold", "emerald"]

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
    fixture = os.environ.get("PROFILE_FIXTURE")
    if fixture:                                   # offline previews and tests
        with open(fixture, encoding="utf-8") as f:
            data = json.load(f)
        return data["created"], data["recent"], data["all_days"]
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


# ------------------------------------------------------------------- the world
SC = 2                                   # raster scale: rendered at 2x, shown at 1x
EX = (19.4, 3.1)                         # one week to the right, drifting down
EY = (-8.6, 11.2)                        # one weekday toward the viewer
EZ = 15.0                                # one block up
MAX_BLOCKS = 7
SLAB = 3.6                               # blocks of ground under the surface

SKY = {"dark": ((9, 13, 33), (32, 46, 82)), "light": ((104, 152, 255), (196, 220, 255))}
CSS = ("@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}.tw{animation:tw 2.8s steps(3) infinite}"
       "@keyframes drift{0%{transform:translateX(0)}100%{transform:translateX(90px)}}"
       ".drift{animation:drift 40s linear infinite alternate}"
       "@keyframes beam{0%,100%{opacity:.95}50%{opacity:.55}}.beam{animation:beam 1.6s ease-in-out infinite}"
       "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}"
       ".bob{animation:bob 2s ease-in-out infinite}")


def heights(days):
    """Log-scaled tower heights, normalised to the 90th percentile so one huge
    day does not flatten every other one."""
    busy = sorted(d["contributionCount"] for _, _, d in days if d["contributionCount"])
    ref = max(3, busy[int(len(busy) * .9)] if busy else 3)

    def stack(cnt):
        if not cnt:
            return 0
        return 1 + round(min(1.0, math.log1p(cnt) / math.log1p(ref)) * (MAX_BLOCKS - 1))
    return stack


def sky(theme, w, h):
    top, bot = SKY[theme]
    a = Image.new("RGB", (w, h))
    px = ImageDraw.Draw(a)
    for y in range(h):
        t = (y / h) ** 1.2
        px.line([(0, y), (w, y)], fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return a.convert("RGBA")


def sun_or_moon(img, theme, x, y, s):
    d = ImageDraw.Draw(img)
    if theme == "light":
        d.rectangle([x, y, x + s, y + s], fill=(255, 247, 170))
        d.rectangle([x + s * .2, y + s * .2, x + s * .8, y + s * .8], fill=(255, 255, 222))
    else:
        d.rectangle([x, y, x + s, y + s], fill=(226, 228, 214))
        q = s / 8
        for cx, cy, r in ((2, 2, 1), (5, 4, 1.5), (3, 5.5, 1)):
            d.rectangle([x + cx * q, y + cy * q, x + (cx + r) * q, y + (cy + r) * q], fill=(178, 182, 170))


def render_world(theme, weeks, stack, sky_h):
    """The raster: sky, chunk, shadows, towers. Returns (image, camera, size)."""
    n = len(weeks)
    ox = 70 + 7 * -EY[0]                                  # leftmost point of the near edge sits at x=70
    oy = sky_h + MAX_BLOCKS * EZ
    w_px = W
    h_px = int(oy + n * EX[1] + 7 * EY[1] + SLAB * EZ + 46)
    img = sky(theme, w_px * SC, h_px * SC)
    cam = mc.Cam(ox * SC, oy * SC, (EX[0] * SC, EX[1] * SC), (EY[0] * SC, EY[1] * SC), EZ * SC)

    # stars or sun/moon (twinkling stars are overlaid in SVG)
    sun_or_moon(img, theme, (W - 190) * SC, 30 * SC, 34 * SC)

    # ground: one grass top per day cell, the chunk's cut faces, ores, bedrock
    rng = random.Random(7)
    for w in range(n):
        for d in range(7):
            cam.block(img, w, d, -1, "grass", faces=())
    for w in range(n):                                    # front cut face, top to bottom
        for z, kind in ((-1, "grass"), (-2, "dirt"), (-3, "stone"), (-4, "stone")):
            k = kind
            if kind == "stone" and rng.random() < .16:
                k = rng.choice(("emerald_ore", "stone", "stone"))
            if kind == "stone" and rng.random() < .07:
                k = "diamond_ore"
            cam.block(img, w, 6, z, k, top=False, faces=("front",))
    for d in range(7):                                    # right cut face
        for z, kind in ((-1, "grass"), (-2, "dirt"), (-3, "stone"), (-4, "stone")):
            k = "gold_ore" if kind == "stone" and rng.random() < .12 else kind
            cam.block(img, n - 1, d, z, k, top=False, faces=("right",))
    # bedrock lip along the bottom
    for w in range(n):
        cam.block(img, w, 6, -4.5, "bedrock", dz=.5, top=False, faces=("front",))
    for d in range(7):
        cam.block(img, n - 1, d, -4.5, "bedrock", dz=.5, top=False, faces=("right",))

    # grid seams on the grass, so the calendar still reads as days
    seams = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(seams)
    for w in range(n + 1):
        sd.line([cam.p(w, 0), cam.p(w, 7)], fill=(0, 0, 0, 34), width=SC)
    for d in range(8):
        sd.line([cam.p(0, d), cam.p(n, d)], fill=(0, 0, 0, 34), width=SC)
    img.alpha_composite(seams)

    # shadows: every tower casts one down-right, merged into a single layer
    cells = [(w, wd, stack(day["contributionCount"]), day) for w, wk in enumerate(weeks)
             for day in wk["contributionDays"] for wd in [day["weekday"]] if day["contributionCount"]]
    sh = Image.new("L", img.size, 0)
    shd = ImageDraw.Draw(sh)
    for w, d, hgt, _ in cells:
        L = .55 + hgt * .32                               # shadow length in cells
        quad = [cam.p(w, d), cam.p(w + 1, d), cam.p(w + 1 + L, d + 1 + L * .35), cam.p(w + L, d + 1 + L * .35),
                cam.p(w, d + 1)]
        shd.polygon(quad, fill=110)
    # keep shadows on the ground
    ground = Image.new("L", img.size, 0)
    ImageDraw.Draw(ground).polygon([cam.p(0, 0), cam.p(n, 0), cam.p(n, 7), cam.p(0, 7)], fill=255)
    sh = ImageChops.multiply(sh, ground)
    dark = Image.new("RGBA", img.size, (8, 14, 4, 255))
    dark.putalpha(sh)
    img.alpha_composite(dark)

    # towers, far to near
    for w, d, hgt, day in sorted(cells, key=lambda c: (c[0] + c[1], c[1])):
        mat = MATERIAL[LEVELS.index(day["contributionLevel"])] or "grass"
        for z in range(hgt):
            kind = mat
            if mat == "grass" and z < hgt - 1:
                kind = "dirt"
            ao = .78 + .22 * min(1, (z + 1) / 2)          # a little ambient occlusion at the foot
            cam.block(img, w, d, z, kind, ao=ao, top=(z == hgt - 1))
    return img, cam, (w_px, h_px)


def render(theme, created, recent, all_days, stamp):
    weeks = recent["weeks"]
    n = len(weeks)
    days = [(w, d["weekday"], d) for w, wk in enumerate(weeks) for d in wk["contributionDays"]]
    stack = heights(days)
    peak = max(days, key=lambda x: x[2]["contributionCount"])
    latest = max(d["date"] for _, _, d in days)
    active = sum(1 for _, _, d in days if d["contributionCount"])
    sky_h = 96
    img, cam, (w_px, h_px) = render_world(theme, weeks, stack, sky_h)
    P = lambda u, v, z=0: (cam.p(u, v, z)[0] / SC, cam.p(u, v, z)[1] / SC)

    body = [mc.image(mc.png_uri(img.convert("RGB"), 192), 0, 0, w_px, h_px)]
    # stars / clouds
    rng = random.Random(3)
    if theme == "dark":
        for i in range(46):
            x, y = rng.randrange(20, W - 20), rng.randrange(8, sky_h + 70)
            if P(min(n, max(0, (x - 70) / EX[0])), 0)[1] - MAX_BLOCKS * EZ < y and x > 60:
                continue
            s = 2 if i % 3 else 3
            cls = ' class="tw"' if i % 4 == 0 else ""
            body.append(f'<rect{cls} x="{x}" y="{y}" width="{s}" height="{s}" fill="#FFFFFF"'
                        f' opacity="{.45 + (i % 3) * .2:.2f}" style="animation-delay:{-i * .37 % 2.8:.2f}s"/>')
    else:
        for cx, cy, cw in ((600, 34, 150), (330, 132, 120), (880, 150, 170)):
            body.append(f'<g class="drift" style="animation-delay:{-cx / 20:.0f}s" opacity=".92">'
                        f'<rect x="{cx}" y="{cy}" width="{cw}" height="18" fill="#FFFFFF"/>'
                        f'<rect x="{cx + cw * .2:.0f}" y="{cy - 12}" width="{cw * .45:.0f}" height="12" fill="#FFFFFF"/>'
                        f'<rect x="{cx}" y="{cy + 18}" width="{cw}" height="5" fill="#DDE6F5"/></g>')

    # title over the sky
    body.append(mc_pixel("CONTRIBUTION WORLD", 28, 22, 4))
    body.append(mc_text(28, 74, f"{recent['totalContributions']:,} contributions · {active} active days"
                        f" · taller = busier · synced {stamp}", 12.5, "#FFFFFF"))
    # legend
    lx = W - 420
    leg = []
    for i, (m, nm) in enumerate(zip(MATERIAL[1:], MATERIAL_NAME[1:])):
        ic = mc.icon(m, 56)
        leg.append(mc.image(mc.png_uri(ic), lx + i * 84, 88, 28, 28))
        leg.append(mc_text(lx + i * 84 + 32, 108, nm, 11, "#FFFFFF"))
    body.append(mc_text(lx - 10, 108, "less", 11, "#FFFFFF", "end"))
    body.append("".join(leg))
    body.append(mc_text(lx + 3 * 84 + 94, 108, "more", 11, "#FFFFFF"))

    # month labels painted on the dirt band of the front cut
    last = None
    for w, wk in enumerate(weeks):
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last and w < n - 2:
            x, y = P(w + .2, 7, -1.62)
            body.append(mc_text(x, y, first.strftime("%b").upper(), 11, "#FFFFFF", weight=700))
            last = first.month
    for d, nm in ((1, "MON"), (3, "WED"), (5, "FRI")):
        x, y = P(0, d + .75, 0)
        body.append(mc_text(x - 8, y, nm, 10.5, "#FFFFFF", "end", 700))

    # today's beacon and the best-day marker
    for w, wd, day in days:
        if day["date"] == latest:
            bx, by = P(w + .5, wd + .5, stack(day["contributionCount"]))
            top = 30
            body.append(f'<g class="beam"><rect x="{bx - 7:.1f}" y="{top}" width="14" height="{by - top:.1f}"'
                        f' fill="#9FFFF2" opacity=".18"/><rect x="{bx - 2.5:.1f}" y="{top}" width="5"'
                        f' height="{by - top:.1f}" fill="#DFFFFB" opacity=".85"/></g>')
            body.append(f'<g class="bob">{chip(min(bx, W - 70), top + 6, "today", AQUA, 12)}</g>')
        if day["date"] == peak[2]["date"]:
            px_, py_ = P(w + .5, wd + .5, stack(day["contributionCount"]))
            lbl = f"best day · {day['contributionCount']} on {short(day['date'])}"
            ly = max(sky_h + 34, py_ - 40)
            body.append(f'<rect x="{px_ - 1:.1f}" y="{ly:.1f}" width="2" height="{py_ - ly - 2:.1f}" fill="{YELLOW}"/>')
            body.append(chip(min(max(px_, 150), W - 150), ly, lbl, YELLOW, 12))

    # plaque
    body.append(mc_text(28, h_px - 34, f"seed  {LOGIN.lower()}", 11, "#FFFFFF"))
    body.append(mc_text(28, h_px - 18, f"biome commits · {n}w × 7d", 11, "#FFFFFF"))
    frame = ('<rect x="1" y="1" width="{0}" height="{1}" fill="none" stroke="#000" stroke-width="2"/>'
             .format(w_px - 2, h_px - 2))
    return svg(w_px, h_px, "".join(body) + frame, css=CSS,
               label=(f"Contribution world: {recent['totalContributions']:,} contributions over the last 12 months,"
                      f" {active} active days, best day {peak[2]['contributionCount']} on {short(peak[2]['date'])}"))


# ------------------------------------------------------------- player stats card
XP_PER = 5          # level L needs XP_PER * L^2 contributions
STATS_H = 500


def level(total):
    lv = int(math.sqrt(total / XP_PER))
    lo, hi = XP_PER * lv * lv, XP_PER * (lv + 1) ** 2
    return lv, (total - lo) / (hi - lo), hi - total


STATS_CSS = ("@keyframes xp{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
             ".xp{animation:xp 1.8s .3s cubic-bezier(.2,.9,.3,1) both;transform-box:fill-box;transform-origin:left}"
             "@keyframes beat{0%,100%{transform:scale(1)}10%{transform:scale(1.2)}20%{transform:scale(1)}}"
             ".beat{animation:beat 1.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}")


def stats_card(created, recent, all_days):
    today = dt.datetime.now(TZ).date()
    cur, cur_range, longest, best_range = streaks(all_days, today)
    total = sum(all_days.values())
    lv, frac, need = level(total)
    days = [d for wk in recent["weeks"] for d in wk["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"])
    peak = max(days, key=lambda d: d["contributionCount"])
    w, h = HALF, STATS_H
    out = [card_frame(w, h), label(24, 38, "Player Statistics")]

    # hearts = current streak (one per day, ten max), the last one beats
    for i in range(10):
        full = i < min(cur, 10)
        hh = heart(26 + i * 26, 56, 3, full)
        out.append(f'<g class="beat">{hh}</g>' if full and i == min(cur, 10) - 1 else hh)
    out.append(label(w - 24, 72, f"streak {cur}d", 13, LABEL, "end"))

    # XP bar + level
    bx, by, bw = 26, 124, w - 52
    out.append(rect(bx - 2, by - 2, bw + 4, 14, "#000000"))
    out.append(rect(bx, by, bw, 10, "#2B2B2B"))
    out.append(rect(bx, by, bw * max(frac, .01), 10, "#7EFC20", extra=' class="xp"'))
    out.append(rect(bx, by, bw * max(frac, .01), 3, "#C8FF8C", extra=' class="xp"'))
    for k in range(1, 18):
        out.append(rect(bx + bw * k / 18, by, 2, 10, "#000000", .5))
    lvs = str(lv)
    lw = pixel_width(lvs, 3)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        out.append(pixel_text(lvs, (w - lw) / 2 + dx, by - 30 + dy, 3, "#000000"))
    out.append(pixel_text(lvs, (w - lw) / 2, by - 30, 3, "#80FF20"))
    out.append(label(w / 2, by + 34, f"level {lv} · {need:,} xp to level {lv + 1} · 1 xp = 1 contribution",
                     11.5, LABEL, "middle", 400))

    # the stat list, like the game's Statistics screen
    rows = [("grass", "Total contributions", f"{total:,}",
             f"since {dt.date.fromisoformat(created[:10]).strftime('%b %Y')}"),
            ("planks", "Last 12 months", f"{recent['totalContributions']:,}", f"{active} active days"),
            ("gold_block", "Current streak", f"{cur} days",
             f"{short(cur_range[0])} – {short(cur_range[1])}" if cur else "start one today"),
            ("emerald_block", "Longest streak", f"{longest} days",
             f"{short(best_range[0])} – {short(best_range[1])}"),
            ("diamond_block", "Best day", f"{peak['contributionCount']}", short(peak["date"]))]
    y0 = 192
    out.append(inset(18, y0 - 8, w - 36, len(rows) * 56 + 12, "#8B8B8B"))
    for i, (blk, name, val, sub) in enumerate(rows):
        y = y0 + i * 56
        if i % 2:
            out.append(rect(20, y - 4, w - 40, 56, "#000000", .06))
        out.append(mc.image(mc.png_uri(mc.icon(blk, 80)), 32, y + 4, 40, 40))
        out.append(mc_text(86, y + 22, name, 15, "#FFFFFF", weight=700))
        out.append(mc_text(86, y + 42, sub, 12, "#E0E0E0"))
        out.append(mc_text(w - 36, y + 34, val, 22, YELLOW, "end", 700))
    return svg(w, h, "".join(out), css=STATS_CSS,
               label=(f"Player statistics: level {lv}, {total:,} lifetime contributions, current streak {cur} days,"
                      f" longest {longest} days, best day {peak['contributionCount']}"))


if __name__ == "__main__":
    from theme import ASSETS
    ASSETS.mkdir(parents=True, exist_ok=True)
    created, recent, all_days = fetch()
    stamp = dt.datetime.now(TZ).strftime("%d %b %Y %H:%M WIB")
    for name in ("dark", "light"):
        (ASSETS / f"world-{name}.svg").write_text(render(name, created, recent, all_days, stamp), encoding="utf-8")
        print("wrote", f"world-{name}.svg")
    (ASSETS / "stats.svg").write_text(stats_card(created, recent, all_days), encoding="utf-8")
    print("wrote stats.svg")
