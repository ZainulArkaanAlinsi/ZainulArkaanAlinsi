"""Zine pages after the cover: about, toolkit, report card, footer, social stickers.

Stdlib only so the daily Action can refresh the report card:
    GITHUB_TOKEN=... python scripts/build_pages.py assets
Without a token the report card is skipped (everything else still builds).
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

import zine as z

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "assets"
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB


def write(name, svg):
    (OUT / name).write_text(svg, encoding="utf-8")


def hand(x, y, text, size=36, color=z.INK, rot=0, anchor="start", cls=""):
    return (f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot})"><text class="hand {cls}" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}">{escape(text)}</text></g>')


def typed(x, y, text, size=20, color=z.INK, anchor="start"):
    return f'<text x="{x:.0f}" y="{y:.0f}" class="tw" font-size="{size}" fill="{color}" text-anchor="{anchor}" style="white-space:pre">{escape(text)}</text>'


# ------------------------------------------------------------------ about
def about():
    W, H = 1200, 740
    lx, top = 132, 150
    lines = [("hi! i'm zainul :)", z.INK),
             ("a student at IDN Boarding School.", z.INK),
             ("i build full-stack web apps with", z.INK),
             ("laravel, next.js & tailwind css.", z.INK),
             ("right now: going deep into flutter", z.INK),
             ("goal -> write efficient code that", z.INK),
             ("makes a real impact.", z.INK),
             ("(and fewer bugs. mostly.)", z.PENCIL)]
    fs, step = 38, 48
    rules = "".join(f'<line x1="34" y1="{top + step * k}" x2="760" y2="{top + step * k}" stroke="{z.RULE}" stroke-width="1.4"/>' for k in range(12))
    holes = "".join(f'<circle cx="68" cy="{y}" r="12" fill="#d9d1c2" stroke="#bdb3a0"/>' for y in (180, 400, 620))

    def base(k):
        return top + step * (k + 1) - 10

    marks = (
        z.highlight(lx + z.text_w("i build ", "Hand", fs) - 4, base(2) - 28, z.text_w("full-stack web apps", "Hand", fs) + 8, 32, z.YELLOW)
        + z.scribble_circle(lx + z.text_w("right now: going deep into ", "Hand", fs) + z.text_w("flutter", "Hand", fs) / 2,
                            base(4) - 12, z.text_w("flutter", "Hand", fs) / 2 + 18, 26, seed=5)
        + z.squiggle(lx + z.text_w("makes a ", "Hand", fs), base(6) + 10, z.text_w("real impact", "Hand", fs), color=z.RED)
    )
    written = "".join(hand(lx, base(k), t, fs, c) for k, (t, c) in enumerate(lines))
    title, _ = z.ransom("ABOUT ME", lx - 4, 96, 58, seed=21)
    notebook = z.paper(24, 40, 750, 660, seed=8, color=z.PAPER_W, rot=-1.2, torn=(False, False, False, True),
                       extra=(rules + '<line x1="112" y1="44" x2="112" y2="696" stroke="#f08c8c" stroke-width="2"/>'
                              + holes + title + marks + written + z.typed_cat(610, 616, size=18, accent=z.RED)))

    facts = [("NAME", "Zainul A. A."), ("ROLE", "full-stack dev"), ("SCHOOL", "IDN Boarding"),
             ("STACK", "PHP / TS / Dart"), ("BASED", "Indonesia"), ("STATUS", "[x] open to collab")]
    card_lines = "".join(
        typed(830, 188 + i * 46, f"{k:<7}... {v}", 19) + f'<line x1="826" y1="{198 + i * 46}" x2="1150" y2="{198 + i * 46}" stroke="{z.RULE}"/>'
        for i, (k, v) in enumerate(facts))
    card = z.paper(806, 70, 364, 380, seed=13, color=z.PAPER_W, rot=2.5, torn=(False, False, False, False),
                   extra=(f'<line x1="806" y1="140" x2="1170" y2="140" stroke="#f08c8c" stroke-width="2"/>'
                          f'<text x="830" y="122" class="blk" font-size="30" fill="{z.INK}">FACT FILE</text>' + card_lines)) + z.tape(988, 74, 140, -4)

    xs = (842, 1004, 1138)
    labels = [("jul '24", "1st commit"), ("now", "laravel + next"), ("next", "flutter!")]
    timeline = (f'<path d="M830,626 C900,612 940,640 990,624 S1090,610 1150,628" fill="none" stroke="{z.INK}" stroke-width="3" stroke-linecap="round"/>'
                + "".join(f'<circle cx="{x}" cy="{626 if i != 1 else 624}" r="9" fill="{z.YELLOW if i == 1 else z.PAPER_W}" stroke="{z.INK}" stroke-width="3"/>'
                          + hand(x - 16 if i == 0 else x + 16 if i == 2 else x, 596, a, 24, z.RED if i == 1 else z.INK, anchor=("start", "middle", "end")[i])
                          + hand(x - 16 if i == 0 else x + 16 if i == 2 else x, 672, b, 24, anchor=("start", "middle", "end")[i])
                          for i, (x, (a, b)) in enumerate(zip(xs, labels))))
    scrap = z.paper(800, 500, 380, 210, seed=17, color=z.KRAFT, rot=-2.5, torn=(True, False, True, False),
                    extra=hand(822, 552, "the story so far", 32) + timeline)

    body = (notebook + card + scrap
            + z.circle_sticker(726, 84, 50, z.PINK, ["HELLO!"], rot=-14, size=17, cls="wob")
            + z.star(772, 478, 26, cls="spin"))
    write("about.svg", z.doc(W, H, "About me: student at IDN Boarding School, full-stack web developer learning Flutter", body, seed=2))


# ------------------------------------------------------------------ toolkit
TOOLS = [("laravel", "Laravel"), ("nextdotjs", "Next.js"), ("php", "PHP"), ("typescript", "TypeScript"), ("tailwindcss", "Tailwind"),
         ("javascript", "JavaScript"), None, None, ("react", "React"), ("dart", "Dart"),
         ("vuedotjs", "Vue"), ("nodedotjs", "Node.js"), ("mysql", "MySQL"), ("firebase", "Firebase"), ("html5", "HTML"),
         ("css", "CSS"), ("alpinedotjs", "Alpine.js"), ("react", "React Native"), ("git", "Git"), ("github", "GitHub"),
         ("figma", "Figma"), ("postman", "Postman"), ("vercel", "Vercel"), ("sqlite", "SQLite"), ("openjdk", "Java"),
         ("visualstudiocode", "VS Code"), ("gradle", "Gradle"), ("jira", "Jira"), ("canva", "Canva"), ("powershell", "PowerShell")]


def toolkit():
    W, H = 1200, 1000
    rng = random.Random(42)
    lid_x, lid_y, lid_w, lid_h = 40, 140, 1120, 830
    lid = (f'<rect x="{lid_x + 8}" y="{lid_y + 10}" width="{lid_w}" height="{lid_h}" rx="44" fill="#000" opacity=".4"/>'
           f'<rect x="{lid_x}" y="{lid_y}" width="{lid_w}" height="{lid_h}" rx="44" fill="#26262b" stroke="#3b3b42" stroke-width="3"/>'
           f'<rect x="{lid_x + 14}" y="{lid_y + 14}" width="{lid_w - 28}" height="{lid_h - 28}" rx="34" fill="none" stroke="#303036" stroke-width="2"/>')
    cols, rows = 5, 6
    cw, ch = (lid_w - 80) / cols, (lid_h - 90) / rows
    fills = [z.PAPER_W, z.YELLOW, z.PINK, z.LILAC, z.MINT, z.INK]
    stickers, wobbles, fave = [], {"Laravel", "Next.js", "Dart", "Figma"}, None
    for i, item in enumerate(TOOLS):
        if item is None:
            continue
        slug, name = item
        r, c = divmod(i, cols)
        cx = lid_x + 40 + cw * (c + .5) + rng.uniform(-12, 12)
        cy = lid_y + 50 + ch * (r + .5) + rng.uniform(-10, 10)
        rot = rng.uniform(-11, 11)
        color = fills[(i * 7 + rng.randrange(3)) % len(fills)]
        fg = z.PAPER_W if color == z.INK else z.INK
        cls = "wob" if name in wobbles else ""
        delay = -rng.uniform(0, 3)
        if len(name) <= 4 and rng.random() < .7:
            content = z.icon(slug, -19, -42, 38, fg) + f'<text y="30" text-anchor="middle" class="blk" font-size="21" fill="{fg}">{escape(name)}</text>'
            stickers.append(z.circle_sticker(cx, cy, 60, color, [], rot=rot, cls=cls, delay=delay).replace("</g></g>", content + "</g></g>", 1))
            continue
        fs = 22 if len(name) <= 9 else 19
        w, h = 24 + 34 + 12 + z.text_w(name, "Block", fs) + 24, 70
        content = z.icon(slug, -w / 2 + 24, -17, 34, fg) + f'<text x="{-w / 2 + 70:.0f}" y="{fs * .36:.0f}" class="blk" font-size="{fs}" fill="{fg}">{escape(name)}</text>'
        stickers.append(z.sticker(cx, cy, w, h, color, rot=rot, rx=rng.choice([10, 28]), content=content, cls=cls, delay=delay))
        if name == "Laravel":
            fave = (cx, cy, w)

    burst = z.starburst(lid_x + 40 + cw * 2, lid_y + 50 + ch * 1.5, 108, 86, 18, z.YELLOW, rot=-8, cls="wob", content=(
        f'<text y="-40" text-anchor="middle" class="hand" font-size="25" fill="{z.INK}">now learning</text>'
        + z.icon("flutter", -17, -24, 34) + f'<text y="44" text-anchor="middle" class="blk" font-size="26" fill="{z.INK}">FLUTTER!</text>'))

    fx, fy, fw = fave
    notes = (z.scribble_circle(fx, fy, fw / 2 + 24, 58, seed=9)
             + hand(fx + fw / 2 - 6, fy - 52, "fave!", 42, z.RED, rot=-12)
             + hand(lid_x + lid_w - 40, lid_y + lid_h - 26, "29 stickers & counting", 30, z.PAPER_W, rot=-2, anchor="end"))

    title, title_w = z.ransom("MY TOOLKIT", 48, 72, 64, seed=33)
    scrap = z.paper(90 + title_w, 40, 330, 72, seed=41, rot=3, torn=(True, True, True, True),
                    extra=hand(110 + title_w, 88, "stuff i use every day", 32))
    body = title + scrap + lid + "".join(stickers) + burst + notes + z.star(1128, 70, 30, color=z.PINK, cls="spin")
    write("toolkit.svg", z.doc(W, H, "My toolkit: Laravel, Next.js, PHP, TypeScript, Tailwind, React, Flutter and more", body, seed=4))


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
    by_code, by_commit = Counter(), Counter()
    for repo in base["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            by_code[edge["node"]["name"]] += edge["size"]
    for item in base["contributionsCollection"]["commitContributionsByRepository"]:
        lang = (item["repository"]["primaryLanguage"] or {}).get("name")
        if lang:
            by_commit[lang] += item["contributions"]["totalCount"]
    return {"created": base["createdAt"], "repos": base["all"]["totalCount"], "days": days, "by_code": by_code, "by_commit": by_commit}


def streaks(days, today):
    longest, run = 0, 0
    for d in sorted(k for k in days if k <= today.isoformat()):
        run = run + 1 if days[d] > 0 else 0
        longest = max(longest, run)
    cursor = today if days.get(today.isoformat(), 0) else today - dt.timedelta(days=1)  # today isn't over yet
    cur = 0
    while days.get(cursor.isoformat(), 0) > 0:
        cur += 1
        cursor -= dt.timedelta(days=1)
    return cur, longest


# ------------------------------------------------------------------ report card
def report(data):
    W, H = 1200, 1180
    today = dt.datetime.now(TZ).date()
    days = data["days"]
    total = sum(days.values())
    cur, longest = streaks(days, today)
    since = dt.date.fromisoformat(data["created"][:10])
    code, commits = data["by_code"], data["by_commit"]
    top_lang, top_bytes = code.most_common(1)[0]

    def days_word(n):
        return f"{n} day" if n == 1 else f"{n} days"

    rows = [("Contributions", f"{total:,}", "hardworking!"),
            ("Current streak", days_word(cur), "keep it going"),
            ("Longest streak", days_word(longest), "nice run!"),
            ("Public repos", str(data["repos"]), "busy builder"),
            ("Favourite subject", top_lang, f"{top_bytes / sum(code.values()) * 100:.0f}% of the code")]
    table = [typed(70, 232, "SUBJECT", 16, z.PENCIL), typed(520, 232, "SCORE", 16, z.PENCIL), typed(790, 232, "TEACHER'S NOTE", 16, z.PENCIL),
             f'<line x1="66" y1="246" x2="1134" y2="246" stroke="{z.INK}" stroke-width="2"/>']
    for i, (subject, score, note) in enumerate(rows):
        y = 310 + i * 76
        table.append(typed(70, y, subject, 27) + f'<text x="520" y="{y + 4}" class="blk" font-size="40" fill="{z.INK}">{escape(score)}</text>'
                     + hand(790, y + 2, note, 36, z.RED, rot=-2 if i % 2 else 1.5)
                     + f'<line x1="66" y1="{y + 30}" x2="1134" y2="{y + 30}" stroke="{z.INK}" stroke-opacity=".35" stroke-dasharray="4 6"/>')
        if subject == "Longest streak":
            sw = z.text_w(score, "Block", 40)
            table.append(z.scribble_circle(520 + sw / 2, y - 12, sw / 2 + 26, 36, seed=3))

    last_sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    start = last_sunday - dt.timedelta(weeks=51)
    weeks = [(start + dt.timedelta(weeks=w), sum(days.get((start + dt.timedelta(weeks=w, days=k)).isoformat(), 0) for k in range(7))) for w in range(52)]
    peak_i = max(range(52), key=lambda i: weeks[i][1])
    top = max(1, weeks[peak_i][1])
    cx0, cy0, cw, ch = 70, 920, 1060, 210
    bw = cw / 52 - 5
    bars, months, last_month = [], [], weeks[0][0].month
    for i, (ws, n) in enumerate(weeks):
        x = cx0 + i * (bw + 5)
        h = max(3, n / top * ch)
        fill = z.YELLOW if i == peak_i else "url(#hatch)"
        bars.append(f'<rect x="{x:.1f}" y="{cy0 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{fill}" stroke="{z.INK}" stroke-width="{1.6 if n else .8}"/>')
        if ws.month != last_month:
            months.append(typed(x, cy0 + 26, ws.strftime("%b").lower(), 15, z.PENCIL))
            last_month = ws.month
    px = cx0 + peak_i * (bw + 5) + bw / 2
    chart = (typed(70, 668, "ATTENDANCE -- contributions per week, last 52 weeks", 18)
             + f'<line x1="{cx0}" y1="{cy0}" x2="{cx0 + cw}" y2="{cy0}" stroke="{z.INK}" stroke-width="2.5"/>'
             + "".join(bars) + "".join(months)
             + hand(px - 150, cy0 - ch + 10, f"whoa! {top}", 40, z.RED, rot=-6)
             + z.arrow(px - 72, cy0 - ch + 18, px - 12, cy0 - ch + 4, bend=-16, color=z.RED, cls="bob"))

    def breakdown(y, label, counter):
        tot = sum(counter.values()) or 1
        items = counter.most_common(4)
        rest = tot - sum(v for _, v in items)
        if rest > 0:
            items.append(("other", rest))
        colors = [z.YELLOW, z.PINK, z.LILAC, z.MINT, z.PAPER_W]
        out, x = [typed(70, y - 16, label, 18)], 70
        for i, (name, v) in enumerate(items):
            w = v / tot * 1060
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="44" fill="{colors[i]}" stroke="{z.INK}" stroke-width="2.5"/>')
            text = f"{name} {v / tot * 100:.0f}%"
            if z.text_w(text, "Block", 15) < w - 16:
                out.append(f'<text x="{x + 10:.1f}" y="{y + 28}" class="blk" font-size="15" fill="{z.INK}">{escape(text)}</text>')
            x += w
        return "".join(out)

    langs = breakdown(1004, "SUBJECT BREAKDOWN -- by code", code) + breakdown(1094, "SUBJECT BREAKDOWN -- by commits, last 12 months", commits)

    title, title_w = z.ransom("REPORT CARD", 66, 104, 58, seed=51)
    header = (title
              + typed(1134, 82, "student: Zainul Arkaan Alinsi", 18, anchor="end")
              + typed(1134, 110, f"class: github, since {since.strftime('%b %Y').lower()}", 18, anchor="end")
              + typed(1134, 138, f"updated: {today.strftime('%d %b %Y').lower()}", 18, anchor="end")
              + f'<line x1="66" y1="168" x2="1134" y2="168" stroke="{z.INK}" stroke-width="3"/><line x1="66" y1="175" x2="1134" y2="175" stroke="{z.INK}"/>')
    hatch = (f'<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             f'<rect width="7" height="7" fill="{z.PAPER_W}"/><line x1="0" y1="0" x2="0" y2="7" stroke="{z.INK}" stroke-width="1.6"/></pattern></defs>')
    page = z.paper(30, 26, 1140, 1120, seed=61, rot=-.4, torn=(True, False, True, False),
                   extra=header + "".join(table) + chart + langs)
    body = (hatch + page
            + z.stamp(170 + title_w, 102, 62, "CERTIFIED BUILDER * CERTIFIED BUILDER * ", "A+", rot=-14, cls="wob")
            + z.tape(600, 30, 160, 2))
    write("report.svg", z.doc(W, H, f"GitHub report card: {total:,} contributions, longest streak {longest} days, {data['repos']} public repos", body, seed=6))
    return total, cur, longest


# ------------------------------------------------------------------ footer & socials
def footer():
    W, H = 1200, 360
    body = (z.paper(70, 50, 1060, 250, seed=71, rot=1, torn=(True, False, True, False),
                    extra=(hand(600, 172, "thanks for reading my zine!", 76, anchor="middle")
                           + z.squiggle(360, 196, 480, color=z.RED)
                           + typed(600, 250, "see you in issue #02  --  zainul", 22, z.PENCIL, anchor="middle")
                           + z.typed_cat(930, 232, size=18, accent=z.RED)))
            + z.tape(120, 70, 140, -30) + z.tape(1080, 64, 140, 26)
            + z.circle_sticker(1100, 270, 46, z.PINK, ["<3"], rot=10, size=30, cls="wob")
            + z.star(150, 280, 30, cls="spin"))
    write("footer.svg", z.doc(W, H, "Thanks for reading my zine!", body, seed=7))


SOCIALS = [("instagram", "Instagram", z.PINK, -3), ("linkedin", "LinkedIn", z.LILAC, 2), ("youtube", "YouTube", z.YELLOW, -2), ("gmail", "Email", z.MINT, 3)]


def socials():
    for slug, name, color, rot in SOCIALS:
        fs = 24
        w = 30 + 32 + 12 + z.text_w(name, "Block", fs) + 30
        content = z.icon(slug, -w / 2 + 30, -16, 32) + f'<text x="{-w / 2 + 74:.0f}" y="9" class="blk" font-size="{fs}" fill="{z.INK}">{escape(name)}</text>'
        body = z.sticker(160, 60, w, 68, color, rot=rot, rx=34, content=content)
        write(f"social-{slug}.svg", z.doc(320, 124, name, body, fonts=("Block",)))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    about()
    toolkit()
    footer()
    socials()
    if os.environ.get("GITHUB_TOKEN"):
        print("report (total, current, longest):", report(fetch()))
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
