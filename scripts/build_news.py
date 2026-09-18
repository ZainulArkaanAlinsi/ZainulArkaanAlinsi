"""Real programmer news, pulled from public feeds and written into the README.

Each source is fetched independently and capped, so one chatty feed cannot take
over the list and one dead feed cannot empty it. If too little comes back, the
block already in the README is left alone — a stale-but-real list beats a blank
one, and nothing here ever invents a headline.

    python scripts/build_news.py            # rewrite the README block
    python scripts/build_news.py --print    # just show what it would write
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import ASSETS, THEMES

ROOT = ASSETS.parent
README = ROOT / "README.md"
START, END = "<!-- NEWS:START -->", "<!-- NEWS:END -->"
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
UA = "ZainulArkaanAlinsi-profile-readme/1.0 (+https://github.com/ZainulArkaanAlinsi)"

LIMIT = 12          # stories shown
PER_SOURCE = 2      # most any single feed may contribute
SUMMARY_MIN = 55    # shorter than this is boilerplate ("Comments", "Read more")
SUMMARY_MAX = 190
MIN_OK = 4          # below this we keep whatever is already in the README
MAX_AGE_DAYS = 21

SOURCES = [
    {"tag": "HN", "name": "Hacker News", "kind": "hn",
     "url": "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30"},
    {"tag": "GITHUB", "name": "GitHub Blog", "kind": "feed", "url": "https://github.blog/feed/"},
    {"tag": "DEV", "name": "dev.to", "kind": "devto",
     "url": "https://dev.to/api/articles?per_page=20&top=2"},
    {"tag": "LARAVEL", "name": "Laravel News", "kind": "feed", "url": "https://feed.laravel-news.com/"},
    {"tag": "NEXT.JS", "name": "Next.js", "kind": "feed", "url": "https://nextjs.org/feed.xml"},
    {"tag": "FLUTTER", "name": "Flutter", "kind": "feed", "url": "https://medium.com/feed/flutter"},
    {"tag": "LOBSTERS", "name": "Lobsters", "kind": "feed", "url": "https://lobste.rs/rss"},
    {"tag": "FREECODECAMP", "name": "freeCodeCamp", "kind": "feed",
     "url": "https://www.freecodecamp.org/news/rss/"},
    {"tag": "STACKOVERFLOW", "name": "Stack Overflow Blog", "kind": "feed",
     "url": "https://stackoverflow.blog/feed/"},
]


# ----------------------------------------------------------------- fetch layer
def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def when(value):
    """RFC822 or ISO8601 -> aware datetime, or None."""
    if not value:
        return None
    value = value.strip()
    try:
        d = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        try:
            d = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d is None:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def tag_of(el):
    return el.tag.rsplit("}", 1)[-1]


SUMMARY_TAGS = ("description", "summary", "subtitle", "encoded", "content")


def feed_items(blob):
    """RSS 2.0 and Atom, namespace-agnostic."""
    root = ET.fromstring(blob)
    nodes = [e for e in root.iter() if tag_of(e) in ("item", "entry")]
    out = []
    for node in nodes:
        title = link = stamp = None
        blurbs = {}
        for child in node:
            name = tag_of(child)
            if name == "title" and not title:
                title = "".join(child.itertext())
            elif name == "link" and not link:
                link = (child.get("href") or child.text or "").strip()
            elif name in ("pubDate", "published", "updated", "date") and not stamp:
                stamp = child.text
            elif name in SUMMARY_TAGS and name not in blurbs:
                blurbs[name] = "".join(child.itertext())
        if title and link:
            # Prefer the short blurb; fall back to the body only if there is no blurb.
            summary = next((blurbs[k] for k in SUMMARY_TAGS if blurbs.get(k)), "")
            out.append((title, link, when(stamp), summary))
    return out


def hn_items(blob):
    """Link posts carry no text, so fall back to the numbers that make HN useful."""
    out = []
    for hit in json.loads(blob).get("hits", []):
        title = hit.get("title") or hit.get("story_title")
        if not title:
            continue
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        summary = hit.get("story_text") or hit.get("comment_text") or ""
        if not summary:
            pts, com = hit.get("points") or 0, hit.get("num_comments") or 0
            host = re.sub(r"^www\.", "", urllib.parse.urlparse(url).netloc)
            plural = lambda n, w: f"{n} {w}" if n == 1 else f"{n} {w}s"
            summary = (f"{plural(pts, 'point')} and {plural(com, 'comment')} on the Hacker News front page"
                       + (f" \u00b7 {host}" if host and "ycombinator" not in host else "")) if pts or com else ""
        out.append((title, url, when(hit.get("created_at")), summary))
    return out


def devto_items(blob):
    return [(a["title"], a["url"], when(a.get("published_at")), a.get("description") or "")
            for a in json.loads(blob) if a.get("title") and a.get("url")]


READERS = {"hn": hn_items, "devto": devto_items, "feed": feed_items}


# ------------------------------------------------------------------- normalise
def clean(s):
    """Feed text is markup, sometimes escaped twice. Unwrap it rather than
    stripping the entities out, which silently ate apostrophes."""
    s = s or ""
    for _ in range(2):
        s = re.sub(r"<[^>]+>", " ", s)
        s = html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


BOILERPLATE = (
    re.compile(r"\s*The post\b.*?appeared first on.*$", re.I | re.S),   # WordPress footer
    re.compile(r"\s*Continue reading\b.*$", re.I | re.S),
    re.compile(r"\s*(Read|Learn) more\b[^.]*\.?\s*$", re.I),
    re.compile(r"\s*\[(\u2026|\.\.\.)\]\s*$"),
)


def strip_boilerplate(s):
    for pattern in BOILERPLATE:
        s = pattern.sub("", s)
    return s.strip()


def h(s):
    """The cards are raw HTML, so escape for HTML rather than for Markdown."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def trim(s, limit):
    s = clean(s)
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:\u2013\u2014-")
    return cut + "\u2026"


def blurb(summary, title):
    """A summary worth printing: not boilerplate, not just the headline again."""
    s = trim(strip_boilerplate(clean(summary)), SUMMARY_MAX)
    if len(s) < SUMMARY_MIN or key(s)[:40] == key(title)[:40]:
        return ""
    return s


def key(title):
    return re.sub(r"[^a-z0-9]+", "", title.lower())[:60]


def ago(then, now):
    if not then:
        return ""
    mins = max(0, int((now - then).total_seconds() // 60))
    if mins < 60:
        return f"{mins}m ago" if mins else "just now"
    if mins < 60 * 24:
        return f"{mins // 60}h ago"
    return f"{mins // 1440}d ago"


def collect():
    now = dt.datetime.now(dt.timezone.utc)
    floor = now - dt.timedelta(days=MAX_AGE_DAYS)
    pool, seen, errors, live = [], set(), [], []
    for src in SOURCES:
        try:
            raw = READERS[src["kind"]](get(src["url"]))
        except Exception as exc:                                   # one bad feed must not sink the rest
            errors.append(f"{src['tag']}: {type(exc).__name__}")
            continue
        taken = 0
        raw = [(clean(t), u, d, b) for t, u, d, b in raw]
        raw = [r for r in raw if r[0] and r[1].startswith(("http://", "https://"))]
        raw.sort(key=lambda r: r[2] or floor, reverse=True)
        for title, url, stamp, summary in raw:
            if taken >= PER_SOURCE:
                break
            if stamp and stamp < floor:
                continue
            k = key(title)
            if not k or k in seen:
                continue
            seen.add(k)
            pool.append({"tag": src["tag"], "name": src["name"], "title": title,
                         "url": url, "at": stamp or now, "blurb": blurb(summary, title)})
            taken += 1
        if taken:
            live.append(src["name"])
    # The point of a card is to be readable in place, so a story that brought a
    # summary wins a slot over one that did not. Display order stays newest first.
    pool.sort(key=lambda i: i["at"], reverse=True)
    chosen = ([i for i in pool if i["blurb"]] + [i for i in pool if not i["blurb"]])[:LIMIT]
    chosen.sort(key=lambda i: i["at"], reverse=True)
    shown = [n for n in live if any(i["name"] == n for i in chosen)]
    return chosen, shown, errors


# ------------------------------------------------------------------- rendering
def card(item, now):
    """One story as a table cell: source, age, headline, and enough of the story
    to be worth reading without opening anything."""
    body = h(item["blurb"]) or "<i>No summary in this feed \u2014 open the link for the full story.</i>"
    return ('<td width="50%" valign="top">\n'
            f'<sub><code>{h(item["tag"])}</code>&nbsp; {ago(item["at"], now)}</sub><br>\n'
            f'<a href="{h(item["url"])}"><b>{h(trim(item["title"], 96))}</b></a>\n'
            f'<br><br>\n{body}\n'
            '</td>')


def markdown(items, live, stamp):
    now = dt.datetime.now(dt.timezone.utc)
    rows = ["<table>"]
    for a in range(0, len(items), 2):
        pair = items[a:a + 2]
        rows.append("<tr>")
        rows.extend(card(i, now) for i in pair)
        if len(pair) == 1:
            rows.append('<td width="50%"></td>')
        rows.append("</tr>")
    rows.append("</table>")
    sources = " \u00b7 ".join(live) if live else "\u2014"
    rows.append("")
    rows.append(f"<sub>Sources: {sources}. Refreshed automatically \u2014 last run {stamp}.</sub>")
    return "\n".join(rows)


EMPTY = ("_No stories yet \u2014 the cards fill themselves the first time the `profile` "
         "workflow runs._\n\n<sub>Sources: Hacker News \u00b7 GitHub Blog \u00b7 dev.to \u00b7 "
         "Laravel News \u00b7 Next.js \u00b7 Flutter \u00b7 Lobsters \u00b7 freeCodeCamp \u00b7 "
         "Stack Overflow Blog.</sub>")


def splice(text, block):
    if START not in text or END not in text:
        raise SystemExit(f"README is missing the {START} / {END} markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n\n{block}\n\n{END}{tail}"


def current_block(text):
    if START in text and END in text:
        return text.split(START, 1)[1].split(END, 1)[0].strip()
    return ""


def main():
    stamp = dt.datetime.now(TZ).strftime("%d %b %Y %H:%M WIB")
    items, live, errors = collect()
    for e in errors:
        print("skipped", e, file=sys.stderr)
    print(f"{len(items)} stories from {len(live)} sources", file=sys.stderr)

    text = README.read_text(encoding="utf-8") if README.exists() else ""
    if len(items) < MIN_OK:
        keep = current_block(text)
        print("too few stories; keeping the block already in the README", file=sys.stderr)
        block = keep if keep and "No stories yet" not in keep else EMPTY
    else:
        block = markdown(items, live, stamp)

    if "--print" in sys.argv:
        print(block)
        return
    README.write_text(splice(text, block), encoding="utf-8")
    from build_panels import news_header
    for name, tokens in THEMES.items():
        (ASSETS / f"news-{name}.svg").write_text(
            news_header(tokens, stamp, len(items) if len(items) >= MIN_OK else 0), encoding="utf-8")
    print("README news block updated", file=sys.stderr)


if __name__ == "__main__":
    main()
