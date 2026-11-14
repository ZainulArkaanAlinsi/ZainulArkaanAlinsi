"""Contribution calendar + player stats, neo-brutalist with Minecraft blocks.

Calendar: the last twelve months as a grid of squares, like GitHub's own, but
every active day is a real Minecraft block face: grass, planks, gold, emerald
as GitHub's contribution level rises. Today is outlined and pulses; the best
day gets a sticker.

Stats: level (from lifetime contributions) with an XP bar, hearts for the
current streak, and the headline numbers in big flat boxes.

    GITHUB_TOKEN=... python scripts/build_activity.py
    PROFILE_FIXTURE=fixture.json python scripts/build_activity.py   # offline
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mc  # noqa: E402
from brut import (BLUE, CARD_H, HALF, INK, LIME, MUTED, ORANGE, PINK, W, WHITE, YELLOW,  # noqa: E402
                  box, card, heavy, mono, pixel_text, pixel_width, rect, sticker, svg, tab, text)
from PIL import Image  # noqa: E402

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
FACE = [None, "grass_top", "planks", "gold_block", "emerald_block"]   # texture per contribution level

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


# --------------------------------------------------------------------- calendar
CELL, GAP = 17, 3
CAL_CSS = ("@keyframes pop{0%{transform:scale(.2);opacity:0}100%{transform:none;opacity:1}}"
           ".pop{animation:pop .5s cubic-bezier(.3,1.6,.5,1) both;transform-box:fill-box;transform-origin:center}")


def grid_png(weeks):
    """Every active day's square as its block texture, drawn at 4x for crisp
    pixels; empty days stay transparent so the card shows through."""
    k = 4
    step = CELL + GAP
    img = Image.new("RGBA", (len(weeks) * step * k, 7 * step * k), (0, 0, 0, 0))
    faces = {}
    for w, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            lvl = LEVELS.index(d["contributionLevel"])
            if not lvl:
                continue
            if lvl not in faces:
                t = Image.fromarray(mc.tex(FACE[lvl])).resize((CELL * k, CELL * k), Image.NEAREST)
                edge = Image.new("RGBA", ((CELL + 0) * k, (CELL + 0) * k), (17, 17, 17, 255))
                edge.paste(t.resize(((CELL - 2) * k, (CELL - 2) * k), Image.NEAREST), (k, k))
                faces[lvl] = edge
            img.paste(faces[lvl], (w * step * k, d["weekday"] * step * k))
    return img


def calendar(created, recent, all_days, stamp):
    weeks = recent["weeks"]
    n = len(weeks)
    days = [(w, d["weekday"], d) for w, wk in enumerate(weeks) for d in wk["contributionDays"]]
    peak = max(days, key=lambda x: x[2]["contributionCount"])
    latest = max(d["date"] for _, _, d in days)
    active = sum(1 for _, _, d in days if d["contributionCount"])
    step = CELL + GAP
    gx, gy = 70, 150
    h = gy + 7 * step + 78
    out = [card(W, h)]
    out.append(tab(26, 24, "CONTRIBUTIONS")[0])
    out.append(heavy(26 + pixel_width("CONTRIBUTIONS", 3) + 50, 56, f"{recent['totalContributions']:,}", 34))
    out.append(text(26 + pixel_width("CONTRIBUTIONS", 3) + 52 + len(f"{recent['totalContributions']:,}") * 25, 56,
                    f"in the last year · {active} active days", 17, MUTED, weight=700))
    # legend
    lx = W - 360
    out.append(mono(lx - 10, 62, "LESS", 12, INK, "end", 800))
    for i in range(5):
        x = lx + i * 26
        if i == 0:
            out.append(box(x, 46, 20, 20, WHITE, sh=0, bw=2))
        else:
            ic = Image.fromarray(mc.tex(FACE[i])).resize((40, 40), Image.NEAREST)
            out.append(rect(x, 46, 20, 20, INK) + mc.image(mc.png_uri(ic), x + 2, 48, 16, 16))
    out.append(mono(lx + 5 * 26 + 4, 62, "MORE", 12, INK, weight=800))
    # empty squares, then the block faces on top
    empties = []
    for w, wd, d in days:
        if not d["contributionCount"]:
            empties.append(f'<rect x="{gx + w * step + 1}" y="{gy + wd * step + 1}" width="{CELL - 2}"'
                           f' height="{CELL - 2}" fill="{WHITE}" stroke="{INK}" stroke-opacity=".25"/>')
    out.append("".join(empties))
    out.append(mc.image(mc.png_uri(grid_png(weeks), 64), gx, gy, n * step, 7 * step))
    # month and weekday labels
    last = None
    for w, wk in enumerate(weeks):
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last and w < n - 1:
            out.append(mono(gx + w * step, gy - 12, first.strftime("%b").upper(), 12, INK, weight=800))
            last = first.month
    for d, nm in ((1, "MON"), (3, "WED"), (5, "FRI")):
        out.append(mono(gx - 10, gy + d * step + 13, nm, 11, MUTED, "end", 800))
    # today pulses; the best day gets a sticker
    for w, wd, d in days:
        x, y = gx + w * step, gy + wd * step
        if d["date"] == latest:
            out.append(f'<rect class="pulse" x="{x - 3}" y="{y - 3}" width="{CELL + 6}" height="{CELL + 6}"'
                       f' fill="none" stroke="{PINK}" stroke-width="3"/>')
        if d["date"] == peak[2]["date"]:
            out.append(f'<rect x="{x - 3}" y="{y - 3}" width="{CELL + 6}" height="{CELL + 6}" fill="none"'
                       f' stroke="{INK}" stroke-width="3"/>')
            sx = min(max(x, 160), W - 170)
            out.append(f'<line x1="{x + CELL / 2}" y1="{y + CELL + 3}" x2="{sx}" y2="{gy + 7 * step + 24}"'
                       f' stroke="{INK}" stroke-width="3"/>')
            out.append(sticker(sx, gy + 7 * step + 34,
                               f"BEST DAY: {d['contributionCount']} ON {short(d['date']).upper()}", YELLOW, -3, 14))
    out.append(mono(40, h - 26, f"today = pink outline · synced {stamp}", 12, MUTED, weight=600))
    return svg(W, h, "".join(out), css=CAL_CSS,
               label=(f"Contribution calendar: {recent['totalContributions']:,} contributions in the last year,"
                      f" {active} active days, best day {peak[2]['contributionCount']} on {short(peak[2]['date'])}"))


# ------------------------------------------------------------------ player stats
XP_PER = 5          # level L needs XP_PER * L^2 contributions


def level(total):
    lv = int(math.sqrt(total / XP_PER))
    lo, hi = XP_PER * lv * lv, XP_PER * (lv + 1) ** 2
    return lv, (total - lo) / (hi - lo), hi - total


STATS_CSS = ("@keyframes xp{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
             ".xp{animation:xp 1.8s .3s cubic-bezier(.2,.9,.3,1) both;transform-box:fill-box;transform-origin:left}")


def heart(x, y, k, full=True):
    rows = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    cells = "".join(f'<rect x="{x + c * k}" y="{y + r * k}" width="{k}" height="{k}"/>'
                    for r, row in enumerate(rows) for c, v in enumerate(row) if v == "1")
    if not full:
        return f'<g fill="{WHITE}" stroke="{INK}" stroke-width="1">{cells}</g>'
    return (f'<g fill="#E53935">{cells}</g>'
            f'<rect x="{x + k}" y="{y + k}" width="{k}" height="{k}" fill="#FFFFFF"/>')


def stats_card(created, recent, all_days):
    today = dt.datetime.now(TZ).date()
    cur, cur_range, longest, best_range = streaks(all_days, today)
    total = sum(all_days.values())
    lv, frac, need = level(total)
    days = [d for wk in recent["weeks"] for d in wk["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"])
    peak = max(days, key=lambda d: d["contributionCount"])
    w, h = HALF, CARD_H
    out = [card(w, h)]
    out.append(tab(26, 24, "PLAYER STATS")[0])
    out.append(sticker(w - 88, 46, f"BEST: {peak['contributionCount']}", PINK, 6, 15))
    # level badge + XP bar
    out.append(box(26, 86, 112, 104, LIME))
    out.append(pixel_text("LVL", 44, 100, 3, INK))
    out.append(heavy(82, 172, str(lv), 52, INK, "middle"))
    bx, by, bw = 160, 104, w - 160 - 34
    out.append(mono(bx, by - 6, "XP", 13, INK, weight=900))
    out.append(box(bx, by, bw, 30, WHITE, sh=4))
    out.append(rect(bx + 3, by + 3, (bw - 6) * max(frac, .01), 24, "#7EE04A", extra=' class="xp"'))
    for k in range(1, 12):
        out.append(rect(bx + bw * k / 12, by + 3, 2, 24, INK, .25))
    out.append(mono(bx, by + 56, f"{need:,} XP TO LVL {lv + 1}", 13, INK, weight=800))
    for i in range(10):
        out.append(heart(bx + i * 30, by + 70, 3.2, i < min(cur, 10)))
    # the headline numbers
    tiles = [("TOTAL", f"{total:,}", f"since {dt.date.fromisoformat(created[:10]).strftime('%b %Y')}", YELLOW),
             ("LAST 12 MONTHS", f"{recent['totalContributions']:,}", f"{active} active days", BLUE),
             ("CURRENT STREAK", f"{cur}d", f"{short(cur_range[0])} – {short(cur_range[1])}" if cur else "start today",
              PINK),
             ("LONGEST STREAK", f"{longest}d", f"{short(best_range[0])} – {short(best_range[1])}", ORANGE)]
    gw, gh = (w - 26 * 2 - 6 - 16) / 2, 118
    for i, (k, v, sub, c) in enumerate(tiles):
        x = 26 + (i % 2) * (gw + 16)
        y = 236 + (i // 2) * (gh + 18)
        out.append(box(x, y, gw, gh, c, sh=5))
        out.append(mono(x + 16, y + 28, k, 13, INK, weight=900))
        out.append(heavy(x + 16, y + 78, v, 40))
        out.append(text(x + 16, y + 102, sub, 14, INK, weight=600))
    return svg(w, h, "".join(out), css=STATS_CSS,
               label=(f"Player stats: level {lv}, {total:,} lifetime contributions, current streak {cur} days,"
                      f" longest {longest} days, best day {peak['contributionCount']}"))


if __name__ == "__main__":
    from theme import ASSETS
    ASSETS.mkdir(parents=True, exist_ok=True)
    created, recent, all_days = fetch()
    stamp = dt.datetime.now(TZ).strftime("%d %b %Y %H:%M WIB")
    (ASSETS / "calendar.svg").write_text(calendar(created, recent, all_days, stamp), encoding="utf-8")
    (ASSETS / "stats.svg").write_text(stats_card(created, recent, all_days), encoding="utf-8")
    print("wrote calendar.svg stats.svg")
