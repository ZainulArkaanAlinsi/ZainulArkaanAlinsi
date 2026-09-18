"""Parser tests for scripts/build_news.py — fixtures only, no network."""
import datetime as dt
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import build_news as N

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Laravel News</title>
<item><title>Laravel 12 ships queue batching</title><link>https://laravel-news.com/a</link>
<description>&lt;p&gt;Batches can now be chained without a custom dispatcher, and failures
report per job instead of collapsing the whole batch.&lt;/p&gt;</description>
<pubDate>Tue, 16 Sep 2025 09:00:00 +0000</pubDate></item>
<item><title>Ancient post</title><link>https://laravel-news.com/old</link>
<description>Comments</description>
<pubDate>Tue, 01 Jan 2019 09:00:00 +0000</pubDate></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Next.js</title>
<entry><title>Next.js 16</title><link href="https://nextjs.org/blog/next-16"/>
<summary>Turbopack is the default bundler, caching moves behind an explicit API,
and the middleware contract changes for the first time since 13.</summary>
<published>2025-09-15T10:30:00Z</published></entry></feed>"""

HN = json.dumps({"hits": [
    {"title": "Show HN: a tiny SQLite clone", "url": "https://example.com/sqlite",
     "created_at": "2025-09-16T12:00:00.000Z", "objectID": "1",
     "points": 412, "num_comments": 189},
    {"title": "Ask HN: how do you review code?", "url": None,
     "created_at": "2025-09-16T11:00:00.000Z", "objectID": "42",
     "story_text": "I keep bouncing between leaving a pile of nits and rubber-stamping. "
                   "What does your team actually do on a normal pull request?"},
]}).encode()

DEVTO = json.dumps([
    {"title": "Tailwind tips &amp; tricks", "url": "https://dev.to/x",
     "published_at": "2025-09-16T08:00:00Z",
     "description": "Arbitrary values, container queries and the handful of plugins that "
                    "are worth the install on a real project."},
]).encode()


class Parsers(unittest.TestCase):
    def test_rss(self):
        items = N.feed_items(RSS)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0][0], "Laravel 12 ships queue batching")
        self.assertEqual(items[0][1], "https://laravel-news.com/a")
        self.assertEqual(items[0][2].year, 2025)
        self.assertIn("Batches can now be chained", N.clean(items[0][3]))

    def test_atom_uses_href_and_summary(self):
        title, link, stamp, summary = N.feed_items(ATOM)[0]
        self.assertEqual(title, "Next.js 16")
        self.assertEqual(link, "https://nextjs.org/blog/next-16")
        self.assertIsNotNone(stamp.tzinfo)
        self.assertIn("Turbopack", summary)

    def test_hn_falls_back_to_the_discussion(self):
        items = N.hn_items(HN)
        self.assertEqual(items[1][1], "https://news.ycombinator.com/item?id=42")

    def test_hn_link_post_gets_a_stats_blurb(self):
        summary = N.hn_items(HN)[0][3]
        self.assertIn("412 points", summary)
        self.assertIn("189 comments", summary)
        self.assertIn("example.com", summary)

    def test_hn_text_post_keeps_its_own_text(self):
        self.assertIn("rubber-stamping", N.hn_items(HN)[1][3])

    def test_devto(self):
        title, url, stamp, summary = N.devto_items(DEVTO)[0]
        self.assertEqual(url, "https://dev.to/x")
        self.assertEqual(N.clean(title), "Tailwind tips & tricks")
        self.assertIn("container queries", summary)

    def test_malformed_xml_raises_not_hangs(self):
        with self.assertRaises(Exception):
            N.feed_items(b"<rss><channel><item>")


class Text(unittest.TestCase):
    def test_clean_strips_markup_and_entities(self):
        self.assertEqual(N.clean("<b>Go</b> 1.25 &amp;   friends"), "Go 1.25 & friends")

    def test_h_escapes_for_html_not_markdown(self):
        self.assertEqual(N.h('a & b <c> "d"'), "a &amp; b &lt;c&gt; &quot;d&quot;")

    def test_trim_cuts_on_a_word_boundary(self):
        out = N.trim("the quick brown fox jumps over the lazy dog", 20)
        self.assertTrue(out.endswith("\u2026"))
        self.assertLessEqual(len(out), 21)
        self.assertNotIn("jum\u2026", out)

    def test_blurb_rejects_boilerplate_and_echoes(self):
        self.assertEqual(N.blurb("Comments", "Some headline"), "")
        self.assertEqual(N.blurb("Next.js 16 is out", "Next.js 16 is out!"), "")
        good = "A real summary that runs long enough to actually tell you what the story says."
        self.assertEqual(N.blurb(good, "Unrelated headline"), good)

    def test_ago(self):
        now = dt.datetime(2025, 9, 16, 12, tzinfo=dt.timezone.utc)
        self.assertEqual(N.ago(now - dt.timedelta(minutes=5), now), "5m ago")
        self.assertEqual(N.ago(now - dt.timedelta(hours=5), now), "5h ago")
        self.assertEqual(N.ago(now - dt.timedelta(days=3), now), "3d ago")
        self.assertEqual(N.ago(now, now), "just now")

    def test_key_dedupes_across_punctuation(self):
        self.assertEqual(N.key("Next.js 16!"), N.key("next js 16"))


class Cards(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2025, 9, 16, 12, tzinfo=dt.timezone.utc)
        self.item = {"tag": "DEV", "url": "https://dev.to/x?a=1&b=2", "at": self.now - dt.timedelta(hours=2),
                     "title": "Tailwind tips & tricks", "blurb": "Arbitrary values and container queries."}

    def test_cell_carries_source_age_link_and_blurb(self):
        out = N.card(self.item, self.now)
        self.assertIn("<code>DEV</code>", out)
        self.assertIn("2h ago", out)
        self.assertIn('href="https://dev.to/x?a=1&amp;b=2"', out)
        self.assertIn("Tailwind tips &amp; tricks", out)
        self.assertIn("Arbitrary values and container queries.", out)

    def test_hostile_title_cannot_break_out_of_the_cell(self):
        evil = dict(self.item, title='"><script>alert(1)</script>', blurb='</td></tr></table><img src=x>')
        out = N.card(evil, self.now)
        self.assertNotIn("<script>", out)
        self.assertNotIn("<img", out)
        self.assertEqual(out.count("</td>"), 1)

    def test_missing_blurb_still_renders_a_cell(self):
        out = N.card(dict(self.item, blurb=""), self.now)
        self.assertIn("No summary", out)
        self.assertTrue(out.endswith("</td>"))

    def test_grid_pairs_rows_and_pads_an_odd_tail(self):
        items = [dict(self.item, title=f"t{i}") for i in range(5)]
        out = N.markdown(items, ["dev.to"], "now")
        self.assertEqual(out.count("<tr>"), 3)
        self.assertEqual(out.count("<td"), 6)          # 5 cards + 1 spacer
        self.assertIn('<td width="50%"></td>', out)
        self.assertTrue(out.startswith("<table>"))


class Splice(unittest.TestCase):
    def test_replaces_only_between_markers(self):
        doc = f"top\n{N.START}\n\nold\n\n{N.END}\nbottom\n"
        out = N.splice(doc, "new")
        self.assertIn("top", out)
        self.assertIn("bottom", out)
        self.assertIn("new", out)
        self.assertNotIn("old", out)
        self.assertEqual(out.count(N.START), 1)

    def test_missing_markers_is_an_error(self):
        with self.assertRaises(SystemExit):
            N.splice("no markers here", "new")

    def test_round_trips(self):
        doc = f"a\n{N.START}\n\nX\n\n{N.END}\nb\n"
        self.assertEqual(N.current_block(N.splice(doc, "X")), "X")


class Collect(unittest.TestCase):
    def setUp(self):
        self.real = N.get
        payload = {s["url"]: b"" for s in N.SOURCES}
        payload[N.SOURCES[0]["url"]] = HN
        payload[N.SOURCES[3]["url"]] = RSS
        payload[N.SOURCES[4]["url"]] = ATOM
        payload[N.SOURCES[2]["url"]] = DEVTO
        N.get = lambda url, timeout=25: payload[url] or (_ for _ in ()).throw(OSError("down"))
        N.MAX_AGE_DAYS = 100000          # fixtures are dated 2025

    def tearDown(self):
        N.get = self.real

    def test_dead_feeds_are_skipped_not_fatal(self):
        items, live, errors = N.collect()
        self.assertTrue(items)
        self.assertTrue(errors)
        self.assertIn("Hacker News", live)

    def test_per_source_cap_and_ordering(self):
        items, _, _ = N.collect()
        for src in {i["tag"] for i in items}:
            self.assertLessEqual(sum(1 for i in items if i["tag"] == src), N.PER_SOURCE)
        self.assertEqual(items, sorted(items, key=lambda i: i["at"], reverse=True))

    def test_only_http_urls_survive(self):
        for i in N.collect()[0]:
            self.assertTrue(i["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
