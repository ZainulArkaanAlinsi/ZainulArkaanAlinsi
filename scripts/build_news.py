"""Real programmer news, pulled from public feeds and written into the README.

Each source is fetched independently and capped, so one chatty feed cannot take
over the list and one dead feed cannot empty it. If too little comes back, the
block already in the README is left alone — a stale-but-real list beats a blank
one, and nothing here ever invents a headline.

    python scripts/build_news.py            # rewrite the README block
    python scripts/build_news.py --print    # just show what it would write
"""
import datetime as dt
import json
import os
import re
import sys
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
PER_SOURCE = 3      # most any single feed may contribute
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


def feed_items(blob):
    """RSS 2.0 and Atom, namespace-agnostic."""
    root = ET.fromstring(blob)
    nodes = [e for e in root.iter() if tag_of(e) in ("item", "entry")]
    out = []
    for node in nodes:
        title = link = stamp = None
        for child in node:
            name = tag_of(child)
            if name == "title" and not title:
                title = "".join(child.itertext())
            elif name == "link" and not link:
                link = (child.get("href") or child.text or "").strip()
            elif name in ("pubDate", "published", "updated", "date") and not stamp:
                stamp = child.text
        if title and link:
            out.append((title, link, when(stamp)))
    return out


def hn_items(blob):
    out = []
    for hit in json.loads(blob).get("hits", []):
        title = hit.get("title") or hit.get("story_title")
        if not title:
            continue
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        out.append((title, url, when(hit.get("created_at"))))
    return out


def devto_items(blob):
    return [(a["title"], a["url"], when(a.get("published_at")))
            for a in json.loads(blob) if a.get("title") and a.get("url")]


READERS = {"hn": hn_items, "devto": devto_items, "feed": feed_items}


# ------------------------------------------------------------------- normalise
def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    for a, b in (("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'"), ("&apos;", "'"),
                 ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " "), ("&hellip;", "…")):
        s = s.replace(a, b)
    s = re.sub(r"&#x?[0-9a-fA-F]+;", "", s)
    return re.sub(r"\s+", " ", s).strip()


def md_escape(s):
    return re.sub(r"([\\`*_\[\]<>|])", r"\\\1", s)


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
        raw = [(clean(t), u, d) for t, u, d in raw]
        raw = [r for r in raw if r[0] and r[1].startswith(("http://", "https://"))]
        raw.sort(key=lambda r: r[2] or floor, reverse=True)
        for title, url, stamp in raw:
            if taken >= PER_SOURCE:
                break
            if stamp and stamp < floor:
                continue
            k = key(title)
            if not k or k in seen:
                continue
            seen.add(k)
            pool.append({"tag": src["tag"], "name": src["name"], "title": title,
                         "url": url, "at": stamp or now})
            taken += 1
        if taken:
            live.append(src["name"])
    pool.sort(key=lambda i: i["at"], reverse=True)
    return pool[:LIMIT], live, errors


# ------------------------------------------------------------------- rendering
def markdown(items, live, stamp):
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for i in items:
        title = md_escape(i["title"])
        if len(title) > 108:
            title = title[:105].rstrip() + "…"
        rows.append(f"- `{i['tag']}` &nbsp;[{title}]({i['url']}) &nbsp;<sub>{ago(i['at'], now)}</sub>")
    sources = " · ".join(live) if live else "—"
    rows.append("")
    rows.append(f"<sub>Sources: {sources}. Refreshed automatically — last run {stamp}.</sub>")
    return "\n".join(rows)


EMPTY = ("- _No stories yet — the feed fills itself the first time the "
         "`profile` workflow runs._\n\n<sub>Sources: Hacker News · GitHub Blog · dev.to · "
         "Laravel News · Next.js · Flutter · Lobsters.</sub>")


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
