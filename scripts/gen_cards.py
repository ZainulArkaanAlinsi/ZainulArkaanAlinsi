"""About + GitHub stats cards for the profile README (monochrome editorial).

Stdlib only so the daily GitHub Action needs no installs:
    GITHUB_TOKEN=... python scripts/gen_cards.py [assets_dir]

Reads the embedded font subsets from scripts/fonts.css (written by gen_profile.py).
Everything is visible on the first frame; loops animate transform/opacity only.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
ROOT = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "assets"
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB

BG, INK, MUTED, DIM, LINE = "#0a0a0a", "#fafafa", "#a3a3a3", "#525252", "#262626"
SHADES = ["#fafafa", "#c4c4c4", "#8f8f8f", "#636363", "#404040"]
W = 1200

CSS = (ROOT / "fonts.css").read_text(encoding="utf-8") + f"""
.m{{font-family:Mono,ui-monospace,Consolas,monospace}}
.s{{font-family:Serif,Georgia,serif}}
.si{{font-family:SerifI,Georgia,serif;font-style:italic}}
.cap{{font-family:Mono,ui-monospace,monospace;font-size:11px;letter-spacing:2.6px;fill:{MUTED}}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
@keyframes pulse{{50%{{opacity:.2}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(h, label, body, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{CSS}{extra_css}</style>'
            f'<rect width="{W}" height="{h}" fill="{BG}"/>{body}</svg>')


def attr_fill(on):
    return f' fill="{INK}"' if on else ""


# ------------------------------------------------------------------ about
def about():
    H = 600
    statement = [
        ("I build ", "full-stack", " products"),
        ("that turn clean code into", "", ""),
        ("", "real-world impact.", ""),
    ]
    lines = "".join(
        f'<text x="0" y="{140 + i * 60}" class="s" font-size="56" fill="{INK}" letter-spacing="-1" style="white-space:pre">'
        f'{escape(a)}<tspan class="si" fill="{MUTED}">{escape(b)}</tspan>{escape(c)}</text>'
        for i, (a, b, c) in enumerate(statement)
    )
    para = [
        "Student at IDN Boarding School — a program growing the next",
        "generation of tech leaders. I ship web apps with Laravel, Next.js",
        "and Tailwind CSS, and I'm going deep into Flutter for mobile.",
    ]
    para_svg = "".join(
        f'<text x="0" y="{328 + i * 32}" class="s" font-size="23" fill="{MUTED}">{escape(t)}</text>'
        for i, t in enumerate(para)
    )

    steps = [("JUL 2024", "First commit"), ("NOW", "Laravel · Next.js"), ("NEXT", "Flutter, deeper")]
    tl_y, tl_w = 486, 626
    timeline = [f'<line x1="0" y1="{tl_y}" x2="{tl_w}" y2="{tl_y}" stroke="{LINE}"/>',
                f'<circle cx="0" cy="{tl_y}" r="2.5" fill="{INK}" class="run"/>']
    for i, (k, v) in enumerate(steps):
        x = i * (tl_w / 2)
        anchor = ("start", "middle", "end")[i]
        timeline.append(
            f'<circle cx="{x:.0f}" cy="{tl_y}" r="5" fill="{BG}" stroke="{INK}" stroke-width="1.5"/>'
            f'<text x="{x:.0f}" y="{tl_y - 20}" class="cap" text-anchor="{anchor}"{attr_fill(k == "NOW")}>{k}</text>'
            f'<text x="{x:.0f}" y="{tl_y + 42}" class="s" font-size="24" fill="{INK}" text-anchor="{anchor}">{escape(v)}</text>'
        )
    timeline.append(f'<circle cx="{tl_w / 2:.0f}" cy="{tl_y}" r="2.5" fill="{INK}" class="pulse"/>')

    spec = [
        ("ROLE", "Full-Stack Developer"),
        ("SCHOOL", "IDN Boarding School"),
        ("WEB", "Laravel · Next.js · Tailwind"),
        ("MOBILE", "Flutter · React Native"),
        ("LANGUAGES", "PHP · TypeScript · Dart"),
        ("BASED IN", "Indonesia"),
        ("STATUS", "Open to collaborate"),
    ]
    sx, row = 760, 70
    spec_svg = [f'<text x="{sx}" y="36" class="cap" fill="{INK}">SPEC SHEET</text>',
                f'<text x="{W}" y="36" class="cap" text-anchor="end">№ 01</text>',
                f'<line x1="{sx}" y1="56" x2="{W}" y2="56" stroke="{INK}" stroke-opacity=".6"/>']
    for i, (k, v) in enumerate(spec):
        y = 56 + row * (i + 1)
        live = k == "STATUS"
        spec_svg.append(
            (f'<circle cx="{sx + 4}" cy="{y - 30}" r="3.5" fill="{INK}" class="pulse"/>' if live else "")
            + f'<text x="{sx + (16 if live else 0)}" y="{y - 26}" class="cap"{attr_fill(live)}>{k}</text>'
            f'<text x="{W}" y="{y - 22}" class="s" font-size="25" fill="{INK}" text-anchor="end">{escape(v)}</text>'
            f'<line x1="{sx}" y1="{y}" x2="{W}" y2="{y}" stroke="{LINE}"/>'
        )

    body = (f'<text x="0" y="36" class="cap" fill="{INK}">PROFILE — STATEMENT</text>'
            f'<text x="690" y="36" class="cap" text-anchor="end">WHO I AM</text>'
            f'<line x1="0" y1="56" x2="690" y2="56" stroke="{INK}" stroke-opacity=".6"/>'
            f'{lines}{para_svg}<g transform="translate(7,0)">{"".join(timeline)}</g>{"".join(spec_svg)}')
    css = (f".run{{animation:run 5s cubic-bezier(.65,0,.35,1) infinite}}"
           f"@keyframes run{{0%{{transform:translateX(0)}}80%,100%{{transform:translateX({tl_w}px)}}}}")
    (OUT / "about.svg").write_text(svg(H, "About Zainul Arkaan Alinsi", body, css), encoding="utf-8")


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
    return payload["data"]


def fetch():
    base = gql("""query($login:String!){ user(login:$login){
        createdAt
        repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){
          nodes{ languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } }
        all: repositories(ownerAffiliations:OWNER, privacy:PUBLIC){ totalCount }
        contributionsCollection{ contributionYears
          commitContributionsByRepository(maxRepositories:100){ repository{ primaryLanguage{ name } } contributions{ totalCount } } } } }""",
               login=LOGIN)["user"]

    days = {}
    for year in base["contributionsCollection"]["contributionYears"]:
        cal = gql("""query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){
            contributionsCollection(from:$from,to:$to){ contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }""",
                  login=LOGIN, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
        for week in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    by_code = Counter()
    for repo in base["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            by_code[edge["node"]["name"]] += edge["size"]
    by_commit = Counter()
    for item in base["contributionsCollection"]["commitContributionsByRepository"]:
        lang = (item["repository"]["primaryLanguage"] or {}).get("name")
        if lang:
            by_commit[lang] += item["contributions"]["totalCount"]

    return {"created": base["createdAt"], "repos": base["all"]["totalCount"], "days": days,
            "by_code": dict(by_code), "by_commit": dict(by_commit)}


def streaks(days, today):
    longest, run, start, best = 0, 0, None, (None, None)
    for d in sorted(k for k in days if k <= today.isoformat()):
        if days[d] > 0:
            run += 1
            start = start or d
            if run > longest:
                longest, best = run, (start, d)
        else:
            run, start = 0, None
    cursor = today
    if days.get(cursor.isoformat(), 0) == 0:
        cursor -= dt.timedelta(days=1)          # today isn't over yet
    end, cur = cursor, 0
    while days.get(cursor.isoformat(), 0) > 0:
        cur += 1
        cursor -= dt.timedelta(days=1)
    return cur, (cursor + dt.timedelta(days=1), end), longest, best


# ------------------------------------------------------------------ stats
def fmt_day(d):
    if isinstance(d, str):
        d = dt.date.fromisoformat(d)
    return d.strftime("%b %d").upper() if d else "—"


def plural(n, word):
    return f" {word}" if n == 1 else f" {word}s"


def stats(data):
    H = 920
    today = dt.datetime.now(TZ).date()
    days = data["days"]
    total = sum(days.values())
    cur, cur_range, longest, best = streaks(days, today)
    since = dt.date.fromisoformat(data["created"][:10])

    kpis = [
        ("CONTRIBUTIONS", f"{total:,}", "", f"SINCE {since.strftime('%b %Y').upper()}"),
        ("CURRENT STREAK", str(cur), plural(cur, "day"),
         f"{fmt_day(cur_range[0])} — {fmt_day(cur_range[1])}" if cur else "START ONE TODAY"),
        ("LONGEST STREAK", str(longest), plural(longest, "day"), f"{fmt_day(best[0])} — {fmt_day(best[1])}"),
        ("PUBLIC REPOS", str(data["repos"]), "", "AND COUNTING"),
    ]
    col = W / 4
    kpi_svg = []
    for i, (label, num, unit, sub) in enumerate(kpis):
        x = i * col + (0 if i == 0 else 30)
        live = label == "CURRENT STREAK"
        if i:
            kpi_svg.append(f'<line x1="{i * col:.0f}" y1="84" x2="{i * col:.0f}" y2="250" stroke="{LINE}"/>')
        kpi_svg.append(
            (f'<circle cx="{x + 4}" cy="104" r="3.5" fill="{INK}" class="pulse"/>' if live else "")
            + f'<text x="{x + (16 if live else 0)}" y="108" class="cap"{attr_fill(live)}>{label}</text>'
            f'<text x="{x - 4}" y="206" class="s" font-size="104" fill="{INK}" letter-spacing="-3">{num}'
            f'<tspan class="si" font-size="32" fill="{MUTED}" letter-spacing="0">{unit}</tspan></text>'
            f'<text x="{x}" y="244" class="m" font-size="11" letter-spacing="1.6" fill="{DIM}">{escape(sub)}</text>'
        )

    # weekly bars over the last 52 weeks, Sunday-start like GitHub's calendar
    last_sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    start = last_sunday - dt.timedelta(weeks=51)
    weeks = [(start + dt.timedelta(weeks=w),
              sum(days.get((start + dt.timedelta(weeks=w, days=k)).isoformat(), 0) for k in range(7)))
             for w in range(52)]
    peak_i = max(range(52), key=lambda i: weeks[i][1])
    top = max(1, weeks[peak_i][1])
    cy0, ch, gap = 560, 200, 6
    bw = (W - gap * 51) / 52
    bars, months, last_month = [], [], weeks[0][0].month
    for i, (ws, n) in enumerate(weeks):
        x = i * (bw + gap)
        h = max(2, n / top * ch)
        r = n / top
        shade = INK if i == peak_i and n else SHADES[1] if r > .5 else SHADES[2] if r > .15 else SHADES[3] if n else LINE
        bars.append(f'<rect x="{x:.1f}" y="{cy0 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{shade}"/>')
        if ws.month != last_month:
            months.append(f'<text x="{x:.1f}" y="{cy0 + 26}" class="m" font-size="10" letter-spacing="1.4" fill="{DIM}">{ws.strftime("%b").upper()}</text>')
            last_month = ws.month
    px = peak_i * (bw + gap) + bw / 2
    peak_y = cy0 - max(2, top / top * ch)
    year_total = sum(n for _, n in weeks)
    chart = (f'<text x="0" y="318" class="cap" fill="{INK}">CONTRIBUTIONS · LAST 52 WEEKS</text>'
             f'<text x="{W}" y="318" class="cap" text-anchor="end">{year_total:,} IN THE LAST YEAR</text>'
             + "".join(f'<line x1="0" y1="{cy0 - ch * f:.0f}" x2="{W}" y2="{cy0 - ch * f:.0f}" stroke="{LINE}" stroke-dasharray="2 6"/>' for f in (.5, 1))
             + "".join(bars)
             + f'<line x1="0" y1="{cy0}" x2="{W}" y2="{cy0}" stroke="{DIM}"/>'
             + "".join(months)
             + f'<text x="{px - 10:.1f}" y="{peak_y - 14:.1f}" class="m" font-size="11" letter-spacing="1.4" fill="{INK}" text-anchor="end">PEAK · {top} ·  WEEK OF {fmt_day(weeks[peak_i][0])}</text>'
             + f'<rect x="-120" y="{cy0 - ch}" width="120" height="{ch}" fill="url(#scan)" class="scan"/>')

    def lang_block(x0, title, counter, note):
        items = counter.most_common()
        tot = sum(counter.values()) or 1
        rows = items[:5]
        rest = sum(v for _, v in items[5:])
        if rest:
            rows.append(("Other", rest))
        width = 540
        out = [f'<text x="{x0}" y="652" class="cap" fill="{INK}">{title}</text>',
               f'<text x="{x0 + width}" y="652" class="cap" text-anchor="end">{note}</text>']
        cx = x0
        for i, (_, v) in enumerate(rows):
            w = max(2, v / tot * (width - 3 * (len(rows) - 1)))
            out.append(f'<rect x="{cx:.1f}" y="672" width="{w:.1f}" height="12" fill="{SHADES[min(i, 4)]}"/>')
            cx += w + 3
        for i, (name, v) in enumerate(rows):
            y = 728 + i * 32
            out.append(
                f'<text x="{x0}" y="{y}" class="m" font-size="11" letter-spacing="1.4" fill="{DIM}">0{i + 1}</text>'
                f'<rect x="{x0 + 34}" y="{y - 10}" width="10" height="10" fill="{SHADES[min(i, 4)]}"/>'
                f'<text x="{x0 + 56}" y="{y + 1}" class="s" font-size="24" fill="{INK}">{escape(name)}</text>'
                f'<line x1="{x0 + 240}" y1="{y - 4}" x2="{x0 + width - 76}" y2="{y - 4}" stroke="{LINE}" stroke-dasharray="1 5"/>'
                f'<text x="{x0 + width}" y="{y}" class="m" font-size="13" letter-spacing="1" fill="{MUTED}" text-anchor="end">{v / tot * 100:.1f}%</text>'
            )
        return "".join(out)

    langs = (f'<line x1="0" y1="612" x2="{W}" y2="612" stroke="{LINE}"/>'
             + lang_block(0, "LANGUAGES · BY CODE", Counter(data["by_code"]), "PUBLIC REPOS")
             + f'<line x1="600" y1="636" x2="600" y2="{H - 20}" stroke="{LINE}"/>'
             + lang_block(660, "LANGUAGES · BY COMMITS", Counter(data["by_commit"]), "LAST 12 MONTHS"))

    body = (f'<defs><linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
            f'<text x="0" y="36" class="cap" fill="{INK}">GITHUB · @{LOGIN.upper()}</text>'
            f'<text x="{W}" y="36" class="cap" text-anchor="end">UPDATED {today.strftime("%d %b %Y").upper()} · WIB</text>'
            f'<line x1="0" y1="56" x2="{W}" y2="56" stroke="{INK}" stroke-opacity=".6"/>'
            + "".join(kpi_svg)
            + f'<line x1="0" y1="278" x2="{W}" y2="278" stroke="{LINE}"/>'
            + chart + langs)
    css = (f".scan{{animation:scan 6s cubic-bezier(.6,0,.4,1) infinite}}"
           f"@keyframes scan{{0%{{transform:translateX(0)}}70%,100%{{transform:translateX({W + 120}px)}}}}")
    (OUT / "stats.svg").write_text(svg(H, f"GitHub stats for {LOGIN}", body, css), encoding="utf-8")
    return total, cur, longest


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    about()
    if os.environ.get("GITHUB_TOKEN"):
        print("stats (total, current, longest):", stats(fetch()))
    print("cards written to", OUT)
