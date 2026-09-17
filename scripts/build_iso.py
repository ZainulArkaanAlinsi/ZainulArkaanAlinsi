"""Isometric 3D contribution calendar (light + dark), GitHub's own palette.

Stdlib only, run daily by .github/workflows/iso.yml:
    GITHUB_TOKEN=... python scripts/build_iso.py assets
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "assets"

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
THEMES = {
    "light": {"cells": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"], "text": "#1f2328", "muted": "#656d76"},
    "dark": {"cells": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"], "text": "#e6edf3", "muted": "#8d96a0"},
}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"

# axonometric axes: weeks run right/down gently, weekdays run left/down
S = 17
WEEK = (S * 1.0, S * .3)
DAY = (-S * .62, S * .5)
MAX_H = 120


def fetch():
    query = """query($login:String!){ user(login:$login){ contributionsCollection{ contributionCalendar{
        totalContributions weeks{ contributionDays{ date weekday contributionCount contributionLevel } } } } } }"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def shade(hex_color, k):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c * k))) for c in (r, g, b))


def point(w, d, ox, oy, h=0.0):
    return ox + w * WEEK[0] + d * DAY[0], oy + w * WEEK[1] + d * DAY[1] - h


def poly(points, fill):
    return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="{fill}"/>'


def render(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"]
    days = [(w, d["weekday"], d) for w, week in enumerate(weeks) for d in week["contributionDays"]]
    top = max((d["contributionCount"] for _, _, d in days), default=1) or 1

    W, H = 1200, 470
    ox, oy = 100, 130
    gap = .14
    dim = .8 if theme == "light" else .72
    cubes = []
    for w, wd, day in sorted(days, key=lambda x: (x[0] + x[1], x[1])):
        n = day["contributionCount"]
        h = 3 + (n / top) ** .6 * MAX_H if n else 3
        base = t["cells"][LEVELS.index(day["contributionLevel"])]
        a, b = w + gap, wd + gap
        c, e = w + 1 - gap, wd + 1 - gap
        right = [point(c, b, ox, oy), point(c, e, ox, oy), point(c, e, ox, oy, h), point(c, b, ox, oy, h)]
        front = [point(a, e, ox, oy), point(c, e, ox, oy), point(c, e, ox, oy, h), point(a, e, ox, oy, h)]
        roof = [point(a, b, ox, oy, h), point(c, b, ox, oy, h), point(c, e, ox, oy, h), point(a, e, ox, oy, h)]
        cubes.append(poly(right, shade(base, dim)) + poly(front, shade(base, dim * .86)) + poly(roof, base))

    counts = [d["contributionCount"] for _, _, d in days]
    best = max(days, key=lambda x: x[2]["contributionCount"])[2]
    week_totals = [sum(d["contributionCount"] for d in wk["contributionDays"]) for wk in weeks]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    active = sum(1 for c in counts if c)
    best_day = dt.date.fromisoformat(best["date"]).strftime("%b %d, %Y")

    def stat(y, value, label):
        return (f'<text x="{W - 40}" y="{y}" text-anchor="end" font-family="{FONT}" font-size="30" font-weight="600" fill="{t["text"]}">{value}</text>'
                f'<text x="{W - 40}" y="{y + 24}" text-anchor="end" font-family="{FONT}" font-size="15" fill="{t["muted"]}">{label}</text>')

    stats = (f'<text x="{W - 40}" y="64" text-anchor="end" font-family="{FONT}" font-size="46" font-weight="700" fill="{t["text"]}">{cal["totalContributions"]:,}</text>'
             f'<text x="{W - 40}" y="92" text-anchor="end" font-family="{FONT}" font-size="17" fill="{t["muted"]}">contributions in the last year</text>'
             + stat(150, f"{best['contributionCount']}", f"best day · {best_day}")
             + stat(214, f"{max(week_totals)}", "busiest week")
             + stat(278, f"{longest} days", "longest streak this year")
             + stat(342, f"{active}", "active days"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="{cal["totalContributions"]:,} GitHub contributions in the last year, shown as a 3D isometric calendar">'
           f'<title>3D contribution calendar</title>{"".join(cubes)}{stats}</svg>')
    (OUT / f"contributions-3d-{theme}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    calendar = fetch()
    for name in THEMES:
        render(calendar, name)
    print("total:", calendar["totalContributions"])
