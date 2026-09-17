"""README cards below the hero: section headers, about, stack, stats, footer.

Stdlib only so the daily GitHub Action needs no installs:
    GITHUB_TOKEN=... python scripts/gen_cards.py [assets_dir]

Design: monochrome editorial base, one pastel accent per section (same
lightness, never mixed inside a section), ASCII cat mascots for a bit of fun.
Performance: text is visible on the first frame, loops only animate
transform/opacity, no masks or filters.
Reads fonts.css (from gen_profile.py) and icons.json (simple-icons paths).
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
ICONS = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))

BG, INK, MUTED, DIM, LINE, TILE = "#0a0a0a", "#fafafa", "#a3a3a3", "#5c5c5c", "#262626", "#121212"
LIME, LILAC, SKY, CORAL = "#c8f169", "#b8a6ff", "#7ccbff", "#ff906e"
W = 1200

CSS = (ROOT / "fonts.css").read_text(encoding="utf-8") + f"""
.m{{font-family:Mono,ui-monospace,Consolas,monospace}}
.s{{font-family:Serif,Georgia,serif}}
.si{{font-family:SerifI,Georgia,serif;font-style:italic}}
.cap{{font-family:Mono,ui-monospace,monospace;font-size:14px;letter-spacing:3px;fill:{MUTED}}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
@keyframes pulse{{50%{{opacity:.25}}}}
.blink{{animation:blink 4s steps(1) infinite}}
.blink2{{animation:blink2 4s steps(1) infinite}}
@keyframes blink{{0%,90%{{opacity:1}}92%,100%{{opacity:0}}}}
@keyframes blink2{{0%,90%{{opacity:0}}92%,100%{{opacity:1}}}}
.wobble{{animation:wobble 3.2s ease-in-out infinite}}
@keyframes wobble{{50%{{transform:rotate(3deg) translateY(-3px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(h, label, body, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{CSS}{extra_css}</style>'
            f'<rect width="{W}" height="{h}" fill="{BG}"/>{body}</svg>')


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


def fill(color):
    return f' fill="{color}"'


# ------------------------------------------------------------------ mascot
def cat(x, y, accent, mood="idle"):
    """3-line ASCII cat whose feet sit on y. Eyes blink; moods add props."""
    lh, fs = 19, 17
    eyes_open = "( o.o )" if mood != "sleep" else "( -.- )"
    eyes_shut = "( -.- )"
    top = y - lh * 2 - 6
    head = f'<text x="0" y="0" class="m" font-size="{fs}" fill="{INK}" style="white-space:pre"> /\\_/\\ </text>'
    face = (f'<text x="0" y="{lh}" class="m blink" font-size="{fs}" fill="{INK}" style="white-space:pre">{eyes_open}</text>'
            f'<text x="0" y="{lh}" class="m blink2" font-size="{fs}" fill="{INK}" style="white-space:pre">{eyes_shut}</text>')
    if mood == "walk":
        legs = (f'<text x="0" y="{lh * 2}" class="m stepA" font-size="{fs}" fill="{accent}" style="white-space:pre"> &gt; ^ &lt; </text>'
                f'<text x="0" y="{lh * 2}" class="m stepB" font-size="{fs}" fill="{accent}" style="white-space:pre"> &lt; ^ &gt; </text>')
    else:
        legs = f'<text x="0" y="{lh * 2}" class="m" font-size="{fs}" fill="{accent}" style="white-space:pre"> &gt; ^ &lt; </text>'
    return f'<g transform="translate({x},{top})">{head}{face}{legs}</g>'


WALK_STEPS = (".stepA{animation:stepA .5s steps(1) infinite}.stepB{animation:stepB .5s steps(1) infinite}"
              "@keyframes stepA{50%{opacity:0}}@keyframes stepB{0%{opacity:0}50%{opacity:1}}")


# ------------------------------------------------------------------ section headers
def section(slug, num, word, italic, label, accent, mood):
    H = 190
    base = 176
    parts = [
        f'<text x="-4" y="140" class="s" font-size="150" fill="none" stroke="{accent}" stroke-width="1.3" letter-spacing="-4">{num}</text>',
        f'<text x="210" y="112" class="s" font-size="72" fill="{INK}" letter-spacing="-1.5" style="white-space:pre">{escape(word)} <tspan class="si" fill="{accent}">{escape(italic)}</tspan></text>',
        f'<circle cx="216" cy="146" r="4" fill="{accent}" class="pulse"/>',
        f'<text x="232" y="151" class="cap">{escape(label)}</text>',
        f'<line x1="0" y1="{base}" x2="{W}" y2="{base}" stroke="{LINE}"/>',
        f'<rect x="0" y="{base - 1}" width="140" height="2" fill="{accent}" class="dash"/>',
    ]
    css = (f".dash{{animation:dash 7s cubic-bezier(.65,0,.35,1) infinite}}"
           f"@keyframes dash{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX({W - 140}px)}}}}")
    cx = 1040
    if mood == "walk":
        parts.append(f'<g class="walk">{cat(0, base - 3, accent, "walk")}</g>')
        css += (f".walk{{animation:walk 14s linear infinite}}"
                f"@keyframes walk{{0%{{transform:translate(620px,0)}}50%{{transform:translate({W - 90}px,0)}}50.01%{{transform:translate({W - 10}px,0) scaleX(-1)}}100%{{transform:translate(700px,0) scaleX(-1)}}}}"
                + WALK_STEPS)
    elif mood == "code":
        parts.append(cat(cx, base - 3, accent))
        parts.append(f'<g class="bob"><rect x="{cx - 78}" y="36" width="72" height="40" rx="12" fill="{accent}"/>'
                     f'<path d="M{cx - 22},76 l12,12 l2,-12 z" fill="{accent}"/>'
                     f'<text x="{cx - 42}" y="63" text-anchor="middle" class="m" font-size="18" font-weight="700" fill="{BG}">&lt;/&gt;</text></g>')
        css += ".bob{animation:bob 2.4s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-6px)}}"
    elif mood == "commit":
        parts.append(cat(cx, base - 3, accent))
        for i in range(3):
            parts.append(f'<text x="{cx + 20 + i * 26}" y="80" class="m up" style="animation-delay:{-i * 1.1:.1f}s" font-size="18" font-weight="700" fill="{accent}">+1</text>')
        css += ".up{animation:up 3.3s ease-out infinite}@keyframes up{0%{transform:translateY(24px);opacity:0}30%{opacity:1}100%{transform:translateY(-40px);opacity:0}}"
    elif mood == "sleep":
        parts.append(cat(cx, base - 3, accent, "sleep"))
        for i, (z, fs) in enumerate([("z", 16), ("Z", 22), ("Z", 28)]):
            parts.append(f'<text x="{cx + 84 + i * 18}" y="{110 - i * 22}" class="si zz" style="animation-delay:{-i * .9:.1f}s" font-size="{fs}" fill="{accent}">{z}</text>')
        css += ".zz{animation:zz 2.7s ease-in-out infinite}@keyframes zz{0%,100%{opacity:.15;transform:translateY(4px)}50%{opacity:1;transform:translateY(-4px)}}"
    write(f"section-{slug}.svg", svg(H, f"{num} {word} {italic}", "".join(parts), css))


def sticker(x, y, text, accent, rotate, w=None):
    w = w or len(text) * 10.6 + 34
    return (f'<g transform="translate({x},{y}) rotate({rotate})"><g class="wobble">'
            f'<rect x="0" y="0" width="{w:.0f}" height="40" rx="20" fill="{accent}"/>'
            f'<text x="{w / 2:.0f}" y="26" text-anchor="middle" class="m" font-size="15" font-weight="700" letter-spacing="1.2" fill="{BG}">{escape(text)}</text>'
            f'</g></g>')


# ------------------------------------------------------------------ about
def about():
    H, A = 720, LIME
    statement = [("I build ", "full-stack", " products"), ("that turn clean code into", "", ""), ("", "real-world impact.", "")]
    lines = "".join(
        f'<text x="0" y="{166 + i * 70}" class="s" font-size="64" fill="{INK}" letter-spacing="-1.5" style="white-space:pre">'
        f'{escape(a)}<tspan class="si" fill="{A}">{escape(b)}</tspan>{escape(c)}</text>'
        for i, (a, b, c) in enumerate(statement)
    )
    para = [
        "Student at IDN Boarding School, a program growing",
        "the next generation of tech leaders. I ship web apps",
        "with Laravel, Next.js and Tailwind CSS, and I'm going",
        "deep into Flutter for mobile.",
    ]
    para_svg = "".join(f'<text x="0" y="{380 + i * 36}" class="s" font-size="27" fill="{MUTED}">{escape(t)}</text>' for i, t in enumerate(para))

    steps = [("JUL 2024", "First commit"), ("NOW", "Laravel · Next.js"), ("NEXT", "Flutter, deeper")]
    tl_y, tl_w = 610, 680
    tl = [f'<line x1="0" y1="{tl_y}" x2="{tl_w}" y2="{tl_y}" stroke="{LINE}" stroke-width="2"/>',
          f'<rect x="0" y="{tl_y - 1}" width="{tl_w / 2:.0f}" height="2" fill="{A}"/>',
          f'<circle cx="0" cy="{tl_y}" r="4" fill="{A}" class="run"/>']
    for i, (k, v) in enumerate(steps):
        x = i * tl_w / 2
        anchor = ("start", "middle", "end")[i]
        done = i < 2
        tl.append(
            f'<circle cx="{x:.0f}" cy="{tl_y}" r="8" fill="{A if done else BG}" stroke="{A}" stroke-width="2"/>'
            f'<text x="{x:.0f}" y="{tl_y - 26}" class="cap" text-anchor="{anchor}"{fill(A) if k == "NOW" else ""}>{k}</text>'
            f'<text x="{x:.0f}" y="{tl_y + 52}" class="s" font-size="29" fill="{INK}" text-anchor="{anchor}">{escape(v)}</text>'
        )

    spec = [("ROLE", "Full-Stack Developer"), ("SCHOOL", "IDN Boarding School"), ("WEB", "Laravel · Next.js · Tailwind"),
            ("MOBILE", "Flutter · React Native"), ("LANGUAGES", "PHP · TypeScript · Dart"), ("BASED IN", "Indonesia"),
            ("STATUS", "Open to collaborate")]
    sx, row = 800, 88
    sp = [f'<text x="{sx}" y="44" class="cap"{fill(A)}>SPEC SHEET</text>',
          f'<text x="{W}" y="44" class="cap" text-anchor="end">№ 01</text>',
          f'<line x1="{sx}" y1="66" x2="{W}" y2="66" stroke="{A}" stroke-opacity=".7"/>']
    for i, (k, v) in enumerate(spec):
        y = 66 + row * (i + 1) - 14
        live = k == "STATUS"
        sp.append(
            (f'<circle cx="{sx + 5}" cy="{y - 38}" r="5" fill="{A}" class="pulse"/>' if live else "")
            + f'<text x="{sx + (20 if live else 0)}" y="{y - 33}" class="cap" font-size="13"{fill(A) if live else ""}>{k}</text>'
            f'<text x="{W}" y="{y - 29}" class="s" font-size="29" fill="{INK}" text-anchor="end">{escape(v)}</text>'
            f'<line x1="{sx}" y1="{y}" x2="{W}" y2="{y}" stroke="{LINE}"/>'
        )

    body = (f'<text x="0" y="44" class="cap"{fill(A)}>PROFILE — STATEMENT</text>'
            f'<text x="720" y="44" class="cap" text-anchor="end">HI THERE</text>'
            f'<line x1="0" y1="66" x2="720" y2="66" stroke="{A}" stroke-opacity=".7"/>'
            f'{lines}{sticker(552, 262, "HELLO, WORLD!", A, -7)}{para_svg}'
            f'<g transform="translate(10,0)">{"".join(tl)}</g>{"".join(sp)}')
    css = (f".run{{animation:run 4s cubic-bezier(.65,0,.35,1) infinite}}"
           f"@keyframes run{{0%{{transform:translateX(0);opacity:1}}85%{{transform:translateX({tl_w / 2:.0f}px);opacity:1}}100%{{transform:translateX({tl_w / 2:.0f}px);opacity:0}}}}")
    write("about.svg", svg(H, "About Zainul Arkaan Alinsi", body, css))


# ------------------------------------------------------------------ stack
STACK = [
    ("LANGUAGES", [("php", "PHP"), ("typescript", "TypeScript"), ("javascript", "JavaScript"), ("dart", "Dart"),
                   ("openjdk", "Java"), ("html5", "HTML"), ("css", "CSS"), ("powershell", "PowerShell")]),
    ("FRAMEWORKS", [("laravel", "Laravel"), ("nextdotjs", "Next.js"), ("react", "React"), ("vuedotjs", "Vue"),
                    ("tailwindcss", "Tailwind"), ("alpinedotjs", "Alpine.js"), ("flutter", "Flutter"),
                    ("nodedotjs", "Node.js"), ("react", "React Native")]),
    ("DATA & TOOLS", [("mysql", "MySQL"), ("sqlite", "SQLite"), ("firebase", "Firebase"), ("vercel", "Vercel"),
                      ("git", "Git"), ("github", "GitHub"), ("figma", "Figma"), ("postman", "Postman"),
                      ("gradle", "Gradle"), ("visualstudiocode", "VS Code"), ("jira", "Jira"), ("canva", "Canva")]),
]


def stack():
    H, A = 640, LILAC
    tile_h, gap = 100, 18
    total = sum(len(items) for _, items in STACK)
    slugs = sorted({s for _, it in STACK for s, _ in it})
    defs = "".join(f'<symbol id="i-{slug}" viewBox="0 0 24 24"><path d="{ICONS[slug]}"/></symbol>' for slug in slugs)
    rows, css = [], []
    for r, (label, items) in enumerate(STACK):
        y = 150 + r * 158
        tiles, x = [], 0
        for slug, name in items:
            w = 104 + len(name) * 14.5
            tiles.append(
                f'<g transform="translate({x:.0f},0)">'
                f'<rect width="{w:.0f}" height="{tile_h}" rx="18" fill="{TILE}" stroke="{LINE}"/>'
                f'<use href="#i-{slug}" x="26" y="31" width="38" height="38" fill="{INK}"/>'
                f'<text x="82" y="61" class="s" font-size="30" fill="{INK}">{escape(name)}</text>'
                f'<circle cx="{w - 16:.0f}" cy="16" r="3.5" fill="{A}"/></g>')
            x += w + gap
        seq_w = x
        strip = "".join(tiles)
        cls = f"row{r}"
        frames = (f"to{{transform:translateX(-{seq_w:.0f}px)}}" if r % 2 == 0
                  else f"from{{transform:translateX(-{seq_w:.0f}px)}}to{{transform:translateX(0)}}")
        css.append(f".{cls}{{animation:slide{r} {seq_w / 38:.1f}s linear infinite}}@keyframes slide{r}{{{frames}}}")
        rows.append(
            f'<text x="0" y="{y - 18}" class="cap"{fill(A) if r == 0 else ""}>0{r + 1} · {escape(label)}</text>'
            f'<text x="{W}" y="{y - 18}" class="cap" text-anchor="end">{len(items)} ITEMS  {"-&gt;" if r % 2 == 0 else "&lt;-"}</text>'
            f'<g transform="translate(0,{y})"><g class="{cls}">{strip}<g transform="translate({seq_w:.0f},0)">{strip}</g></g></g>')
    fades = (f'<defs>{defs}<linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="fr" x1="1" x2="0"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient></defs>')
    body = (fades
            + f'<text x="0" y="44" class="cap"{fill(A)}>TOOLBOX — {total} THINGS I BUILD WITH</text>'
            + f'<line x1="0" y1="66" x2="{W}" y2="66" stroke="{A}" stroke-opacity=".7"/>'
            + "".join(rows)
            + "".join(f'<rect x="0" y="{150 + r * 158 - 2}" width="110" height="{tile_h + 4}" fill="url(#fl)"/>'
                      f'<rect x="{W - 110}" y="{150 + r * 158 - 2}" width="110" height="{tile_h + 4}" fill="url(#fr)"/>' for r in range(len(STACK)))
            + sticker(W - 300, 18, "NOW LEARNING: FLUTTER", A, 4, w=280))
    write("stack.svg", svg(H, "Tech stack: PHP, TypeScript, Laravel, Next.js, Flutter and more", body, "".join(css)))


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
    H, A = 1080, SKY
    tints = [SKY, "#5aa6d9", "#4282b0", "#2f6186", "#22465f", "#3a3a3a"]
    today = dt.datetime.now(TZ).date()
    days = data["days"]
    total = sum(days.values())
    cur, cur_range, longest, best = streaks(days, today)
    since = dt.date.fromisoformat(data["created"][:10])

    kpis = [
        ("CONTRIBUTIONS", f"{total:,}", "", f"SINCE {since.strftime('%b %Y').upper()}"),
        ("CURRENT STREAK", str(cur), plural(cur, "day"), f"{fmt_day(cur_range[0])} — {fmt_day(cur_range[1])}" if cur else "START ONE TODAY"),
        ("LONGEST STREAK", str(longest), plural(longest, "day"), f"{fmt_day(best[0])} — {fmt_day(best[1])}"),
        ("PUBLIC REPOS", str(data["repos"]), "", "AND COUNTING"),
    ]
    col = W / 4
    kp = []
    for i, (label, num, unit, sub) in enumerate(kpis):
        x = i * col + (0 if i == 0 else 32)
        live = label == "CURRENT STREAK"
        if i:
            kp.append(f'<line x1="{i * col:.0f}" y1="100" x2="{i * col:.0f}" y2="290" stroke="{LINE}"/>')
        kp.append(
            (f'<circle cx="{x + 5}" cy="119" r="5" fill="{A}" class="pulse"/>' if live else "")
            + f'<text x="{x + (20 if live else 0)}" y="124" class="cap" font-size="13"{fill(A) if live else ""}>{label}</text>'
            f'<text x="{x - 4}" y="232" class="s" font-size="116" fill="{INK}" letter-spacing="-3">{num}'
            f'<tspan class="si" font-size="38" fill="{A}" letter-spacing="0">{unit}</tspan></text>'
            f'<text x="{x}" y="276" class="m" font-size="13" letter-spacing="1.8" fill="{MUTED}">{escape(sub)}</text>'
        )

    last_sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    start = last_sunday - dt.timedelta(weeks=51)
    weeks = [(start + dt.timedelta(weeks=w), sum(days.get((start + dt.timedelta(weeks=w, days=k)).isoformat(), 0) for k in range(7)))
             for w in range(52)]
    peak_i = max(range(52), key=lambda i: weeks[i][1])
    top = max(1, weeks[peak_i][1])
    cy0, ch, gap = 640, 230, 6
    bw = (W - gap * 51) / 52
    bars, months, last_month = [], [], weeks[0][0].month
    for i, (ws, n) in enumerate(weeks):
        x = i * (bw + gap)
        h = max(3, n / top * ch)
        r = n / top
        color = A if i in (peak_i, 51) and n else "#d4d4d4" if r > .5 else "#8f8f8f" if r > .15 else "#5c5c5c" if n else LINE
        bars.append(f'<rect x="{x:.1f}" y="{cy0 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{color}"/>')
        if ws.month != last_month:
            months.append(f'<text x="{x:.1f}" y="{cy0 + 32}" class="m" font-size="13" letter-spacing="1.6" fill="{DIM}">{ws.strftime("%b").upper()}</text>')
            last_month = ws.month
    px = peak_i * (bw + gap)
    lx = 51 * (bw + gap) + bw / 2
    ly = cy0 - max(3, weeks[51][1] / top * ch)
    chart = (f'<text x="0" y="362" class="cap"{fill(A)}>CONTRIBUTIONS · LAST 52 WEEKS</text>'
             f'<text x="{W}" y="362" class="cap" text-anchor="end">{sum(n for _, n in weeks):,} THIS YEAR</text>'
             + "".join(f'<line x1="0" y1="{cy0 - ch * f:.0f}" x2="{W}" y2="{cy0 - ch * f:.0f}" stroke="{LINE}" stroke-dasharray="2 7"/>' for f in (.5, 1))
             + "".join(bars)
             + f'<line x1="0" y1="{cy0}" x2="{W}" y2="{cy0}" stroke="{DIM}"/>'
             + "".join(months)
             + f'<text x="{px - 12:.1f}" y="{cy0 - ch + 14}" class="m" font-size="14" font-weight="700" letter-spacing="1.4" fill="{A}" text-anchor="end">PEAK · {top} · WEEK OF {fmt_day(weeks[peak_i][0])}</text>'
             + f'<text x="{lx:.1f}" y="{ly - 10:.1f}" class="m plus" font-size="14" font-weight="700" fill="{A}" text-anchor="middle">+1</text>'
             + f'<rect x="-140" y="{cy0 - ch}" width="140" height="{ch}" fill="url(#scan)" class="scan"/>')

    def lang_block(x0, title, counter, note):
        items = counter.most_common()
        tot = sum(counter.values()) or 1
        rows = items[:5]
        rest = sum(v for _, v in items[5:])
        if rest:
            rows.append(("Other", rest))
        width = 540
        out = [f'<text x="{x0}" y="752" class="cap"{fill(A)}>{title}</text>',
               f'<text x="{x0 + width}" y="752" class="cap" text-anchor="end" font-size="12">{note}</text>']
        cx = x0
        for i, (_, v) in enumerate(rows):
            w = max(3, v / tot * (width - 4 * (len(rows) - 1)))
            out.append(f'<rect x="{cx:.1f}" y="774" width="{w:.1f}" height="16" rx="3" fill="{tints[min(i, 5)]}"/>')
            cx += w + 4
        for i, (name, v) in enumerate(rows):
            y = 842 + i * 40
            out.append(
                f'<text x="{x0}" y="{y}" class="m" font-size="13" letter-spacing="1.4" fill="{DIM}">0{i + 1}</text>'
                f'<rect x="{x0 + 38}" y="{y - 13}" width="13" height="13" rx="3" fill="{tints[min(i, 5)]}"/>'
                f'<text x="{x0 + 64}" y="{y + 1}" class="s" font-size="30" fill="{INK}">{escape(name)}</text>'
                f'<line x1="{x0 + 250}" y1="{y - 5}" x2="{x0 + width - 90}" y2="{y - 5}" stroke="{LINE}" stroke-dasharray="1 6"/>'
                f'<text x="{x0 + width}" y="{y}" class="m" font-size="17" fill="{INK if i == 0 else MUTED}" text-anchor="end">{v / tot * 100:.1f}%</text>'
            )
        return "".join(out)

    langs = (f'<line x1="0" y1="700" x2="{W}" y2="700" stroke="{LINE}"/>'
             + lang_block(0, "LANGUAGES · BY CODE", Counter(data["by_code"]), "PUBLIC REPOS")
             + f'<line x1="600" y1="730" x2="600" y2="{H - 20}" stroke="{LINE}"/>'
             + lang_block(660, "LANGUAGES · BY COMMITS", Counter(data["by_commit"]), "LAST 12 MONTHS"))

    body = (f'<defs><linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{A}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{A}" stop-opacity=".12"/><stop offset="1" stop-color="{A}" stop-opacity="0"/></linearGradient></defs>'
            f'<text x="0" y="44" class="cap"{fill(A)}>GITHUB · @{LOGIN.upper()}</text>'
            f'<text x="{W}" y="44" class="cap" text-anchor="end">UPDATED {today.strftime("%d %b %Y").upper()}</text>'
            f'<line x1="0" y1="66" x2="{W}" y2="66" stroke="{A}" stroke-opacity=".7"/>'
            + "".join(kp)
            + f'<line x1="0" y1="320" x2="{W}" y2="320" stroke="{LINE}"/>'
            + chart + langs)
    css = (f".scan{{animation:scan 6s cubic-bezier(.6,0,.4,1) infinite}}"
           f"@keyframes scan{{0%{{transform:translateX(0)}}70%,100%{{transform:translateX({W + 140}px)}}}}"
           f".plus{{animation:plus 2.2s ease-out infinite}}@keyframes plus{{0%{{transform:translateY(8px);opacity:0}}30%{{opacity:1}}100%{{transform:translateY(-18px);opacity:0}}}}")
    write("stats.svg", svg(H, f"GitHub stats for {LOGIN}", body, css))
    return total, cur, longest


# ------------------------------------------------------------------ footer
def footer():
    H, A = 320, LIME
    words = ["THANKS FOR SCROLLING", "LET'S BUILD SOMETHING", "OPEN FOR COLLABORATION"]
    seq = "".join(f'<tspan fill="{MUTED}">{escape(w)}</tspan><tspan fill="{A}">   *   </tspan>' for w in words)
    seq_w = sum(len(w) + 7 for w in words) * (15 * 0.6 + 2.4)
    body = (f'<line x1="0" y1="1" x2="{W}" y2="1" stroke="{LINE}"/>'
            f'<text x="{W / 2}" y="124" text-anchor="middle" class="s" font-size="78" fill="{INK}" letter-spacing="-1.5">Thanks for <tspan class="si" fill="{A}">visiting</tspan><tspan class="blinkc" fill="{A}">_</tspan></text>'
            f'<text x="{W / 2}" y="172" text-anchor="middle" class="cap">© 2026 ZAINUL ARKAAN ALINSI · MADE WITH CARE IN INDONESIA</text>'
            f'<g class="walk">{cat(0, 250, A, "walk")}</g>'
            f'<line x1="0" y1="252" x2="{W}" y2="252" stroke="{LINE}"/>'
            f'<g transform="translate(0,{H - 28})"><g class="tick"><text class="m" font-size="15" letter-spacing="2.4" style="white-space:pre">{seq * 4}</text></g></g>')
    css = (f".tick{{animation:tick {seq_w / 45:.0f}s linear infinite}}@keyframes tick{{to{{transform:translateX(-{seq_w:.0f}px)}}}}"
           f".blinkc{{animation:bc 1.1s steps(1) infinite}}@keyframes bc{{50%{{opacity:0}}}}"
           f".walk{{animation:walk 18s linear infinite}}"
           f"@keyframes walk{{0%{{transform:translate(-90px,0)}}50%{{transform:translate({W}px,0)}}50.01%{{transform:translate({W + 80}px,0) scaleX(-1)}}100%{{transform:translate(-10px,0) scaleX(-1)}}}}"
           + WALK_STEPS)
    write("footer.svg", svg(H, "Thanks for visiting", body, css))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    section("about", "01", "About", "me", "WHO I AM, IN A NUTSHELL", LIME, "walk")
    section("stack", "02", "Tech", "stack", "TOOLS I REACH FOR", LILAC, "code")
    section("activity", "03", "GitHub", "activity", "LIVE NUMBERS, UPDATED DAILY", SKY, "commit")
    section("snake", "04", "Contribution", "graph", "WATCH IT EAT MY COMMITS", CORAL, "sleep")
    about()
    stack()
    footer()
    if os.environ.get("GITHUB_TOKEN"):
        print("stats (total, current, longest):", stats(fetch()))
    print("cards written to", OUT)
