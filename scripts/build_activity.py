"""GitHub activity panel: stat row + isometric 3D contribution calendar (light/dark).

Stdlib only, refreshed daily by .github/workflows/activity.yml:
    GITHUB_TOKEN=... python scripts/build_activity.py assets
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "assets"
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
THEMES = {
    "light": {"cells": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"], "text": "#1f2328", "muted": "#656d76",
              "border": "#d0d7de", "side": .82, "front": .7},
    "dark": {"cells": ["#1c222b", "#0e4429", "#006d32", "#26a641", "#39d353"], "text": "#e6edf3", "muted": "#8d96a0",
             "border": "#30363d", "side": .7, "front": .56},
}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"

W = 1200
S = 20
WEEK = (S * .98, S * .2)     # weeks run right, gently down
DAY = (-S * .42, S * .6)     # weekdays run toward the viewer
MAX_H = 150

CAL = "contributionCalendar{ totalContributions weeks{ contributionDays{ date weekday contributionCount contributionLevel } } }"


# ------------------------------------------------------------------ data
def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def fetch():
    user = gql(f"query($login:String!){{ user(login:$login){{ createdAt contributionsCollection{{ contributionYears {CAL} }} }} }}", login=LOGIN)
    recent = user["contributionsCollection"]["contributionCalendar"]
    all_days = {}
    for year in user["contributionsCollection"]["contributionYears"]:
        cal = gql(f"query($login:String!,$from:DateTime!,$to:DateTime!){{ user(login:$login){{ contributionsCollection(from:$from,to:$to){{ {CAL} }} }} }}",
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


# ------------------------------------------------------------------ drawing
def shade(hex_color, k):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c * k))) for c in (r, g, b))


def pt(w, d, ox, oy, h=0.0):
    return ox + w * WEEK[0] + d * DAY[0], oy + w * WEEK[1] + d * DAY[1] - h


def poly(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="{fill}"{extra}/>'


def label(x, y, s, size, fill, anchor="start", weight=400):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>'


def render(theme, created, recent, all_days):
    t = THEMES[theme]
    today = dt.datetime.now(TZ).date()
    cur, cur_range, longest, best_range = streaks(all_days, today)
    weeks = recent["weeks"]
    days = [(w, d["weekday"], d) for w, wk in enumerate(weeks) for d in wk["contributionDays"]]
    peak = max(days, key=lambda x: x[2]["contributionCount"])
    top = max(1, peak[2]["contributionCount"])

    stats = [
        (f"{sum(all_days.values()):,}", "Total contributions", f"since {dt.date.fromisoformat(created[:10]).strftime('%b %Y')}"),
        (f"{recent['totalContributions']:,}", "Last 12 months", f"{sum(1 for _, _, d in days if d['contributionCount'])} active days"),
        (f"{cur}", "Current streak", f"{short(cur_range[0])} – {short(cur_range[1])}" if cur else "start one today"),
        (f"{longest}", "Longest streak", f"{short(best_range[0])} – {short(best_range[1])}"),
        (f"{top}", "Best day", short(peak[2]["date"])),
    ]
    pad, col = 36, (W - 72) / len(stats)
    row = []
    for i, (value, name, sub) in enumerate(stats):
        cx = pad + col * i + col / 2
        if i:
            row.append(f'<line x1="{pad + col * i:.0f}" y1="44" x2="{pad + col * i:.0f}" y2="132" stroke="{t["border"]}"/>')
        row.append(label(cx, 88, value, 38, t["text"], "middle", 600)
                   + label(cx, 114, name, 15, t["text"], "middle", 500)
                   + label(cx, 136, sub, 13, t["muted"], "middle"))
    top_block = "".join(row) + f'<line x1="{pad}" y1="170" x2="{W - pad}" y2="170" stroke="{t["border"]}"/>'

    ox, oy = 150, 300
    gap = .12
    latest_date = max(d["date"] for _, _, d in days)
    cubes = []
    for w, wd, day in sorted(days, key=lambda x: (x[0] + x[1], x[1])):
        n = day["contributionCount"]
        h = 4 + (n / top) ** .55 * MAX_H if n else 4
        base = t["cells"][LEVELS.index(day["contributionLevel"])]
        a, b, c, e = w + gap, wd + gap, w + 1 - gap, wd + 1 - gap
        side = [pt(c, b, ox, oy), pt(c, e, ox, oy), pt(c, e, ox, oy, h), pt(c, b, ox, oy, h)]
        front = [pt(a, e, ox, oy), pt(c, e, ox, oy), pt(c, e, ox, oy, h), pt(a, e, ox, oy, h)]
        roof = [pt(a, b, ox, oy, h), pt(c, b, ox, oy, h), pt(c, e, ox, oy, h), pt(a, e, ox, oy, h)]
        today_cls = ' class="today"' if day["date"] == latest_date else ""
        cubes.append(poly(side, shade(base, t["side"])) + poly(front, shade(base, t["front"])) + poly(roof, base, today_cls))

    months, last = [], None
    for w, wk in enumerate(weeks):
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last and w < len(weeks) - 2:
            x, y = pt(w + .5, 7.9, ox, oy)
            months.append(label(x, y + 14, first.strftime("%b"), 13, t["muted"], "middle"))
            last = first.month
    weekdays = ""
    for d, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        x, y = pt(0, d + .5, ox, oy)
        weekdays += label(x - 22, y + 5, name, 12, t["muted"], "end")

    px, py = pt(peak[0] + .5, peak[1] + .5, ox, oy, 4 + MAX_H)
    callout = (f'<line x1="{px:.1f}" y1="{py - 8:.1f}" x2="{px:.1f}" y2="{py - 34:.1f}" stroke="{t["muted"]}" stroke-width="1.2"/>'
               + label(px, py - 42, f"{top} contributions · {short(peak[2]['date'])}", 13, t["text"], "middle", 500))

    legend_x = W - pad - 170
    legend = (label(legend_x - 10, 212, "Less", 13, t["muted"], "end")
              + "".join(f'<rect x="{legend_x + i * 24}" y="200" width="16" height="16" rx="3" fill="{c}"/>' for i, c in enumerate(t["cells"]))
              + label(legend_x + 5 * 24 + 4, 212, "More", 13, t["muted"]))
    header = label(pad, 212, "Contribution calendar · last 12 months", 15, t["text"], weight=500) + legend

    H = int(pt(len(weeks), 7, ox, oy)[1] + 56)
    css = (".today{animation:today 2.4s ease-in-out infinite}"
           "@keyframes today{50%{opacity:.45}}"
           "@media (prefers-reduced-motion:reduce){.today{animation:none}}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="GitHub activity: {sum(all_days.values()):,} contributions, current streak {cur} days, longest streak {longest} days">'
           f'<title>GitHub activity</title><style>{css}</style>'
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="{t["border"]}"/>'
           f'{top_block}{header}{"".join(cubes)}{"".join(months)}{weekdays}{callout}</svg>')
    (OUT / f"activity-{theme}.svg").write_text(svg, encoding="utf-8")
    return H


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    created, recent, all_days = fetch()
    for name in THEMES:
        print(name, "height", render(name, created, recent, all_days))
