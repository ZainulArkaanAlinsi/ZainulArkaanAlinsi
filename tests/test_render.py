"""Every renderer, both themes, from fixture data: well-formed SVG, honest labels."""
import datetime as dt
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import build_activity as A  # noqa: E402
import build_log as L  # noqa: E402
import build_panels as P  # noqa: E402
import fixtures  # noqa: E402
from theme import THEMES  # noqa: E402


def parse(svg):
    return ET.fromstring(svg)


class Panels(unittest.TestCase):
    def test_every_static_panel_parses_in_both_themes(self):
        for t in THEMES.values():
            for fn in (P.about, P.stack_panel, P.footer, P.news_header):
                parse(fn(t))
            for i, (slug, label, sub, _) in enumerate(P.LINKS, 1):
                parse(P.link_chip(t, slug, label, sub, i))
            parse(P.loading(t, "The HUD", "~/hud"))


class Activity(unittest.TestCase):
    def setUp(self):
        d = fixtures.activity(today=dt.datetime.now(A.TZ).date())
        self.args = (d["created"], d["recent"], d["all_days"], "14 Nov 2026 02:39 WIB")

    def test_world_and_hud_parse(self):
        for name in THEMES:
            parse(A.render(name, *self.args))
            parse(A.hud(name, *self.args))

    def test_level_curve(self):
        self.assertEqual(A.level(0)[0], 0)
        lv, frac, need = A.level(2595)
        self.assertEqual(lv, 22)
        self.assertTrue(0 <= frac < 1)
        self.assertEqual(need, A.XP_PER * 23 ** 2 - 2595)


class Log(unittest.TestCase):
    def test_render_parses_and_names_the_newest_commit(self):
        commits = fixtures.commits()
        for name in THEMES:
            svg = L.render(name, commits, "now")
            parse(svg)
            self.assertIn(commits[0]["message"][:30], svg)

    def test_empty_log_still_renders(self):
        parse(L.render("dark", [], "now"))

    def test_flatten_sorts_newest_first_and_drops_bot_commits(self):
        node = lambda m, d: {"oid": "a" * 40, "messageHeadline": m, "committedDate": d, "additions": 1,
                             "deletions": 0}
        repos = [{"name": "r1", "primaryLanguage": None, "defaultBranchRef": {"target": {"history": {"nodes": [
                     node("chore: refresh profile assets", "2026-11-14T00:00:00Z"),
                     node("feat: a", "2026-11-12T00:00:00Z")]}}}},
                 {"name": "empty", "primaryLanguage": None, "defaultBranchRef": None},
                 {"name": "r2", "primaryLanguage": {"name": "PHP", "color": "#4F5D95"},
                  "defaultBranchRef": {"target": {"history": {"nodes": [node("fix: b", "2026-11-13T00:00:00Z")]}}}}]
        out = L.flatten(repos)
        self.assertEqual([c["message"] for c in out], ["fix: b", "feat: a"])
        self.assertEqual(out[0]["oid"], "aaaaaaa")

    def test_only_public_repositories_are_queried(self):
        self.assertIn("privacy:PUBLIC", L.QUERY)

    def test_markup_in_a_commit_message_is_escaped(self):
        c = fixtures.commits()
        c[0]["message"] = "feat: <script>alert(1)</script> & more"
        svg = L.render("dark", c, "now")
        parse(svg)
        self.assertNotIn("<script>", svg)

    def test_kind_reads_conventional_prefixes(self):
        self.assertEqual(L.kind("feat(ui): x"), "green")
        self.assertEqual(L.kind("fix: y"), "red")
        self.assertEqual(L.kind("plain message"), "muted")


if __name__ == "__main__":
    unittest.main()
