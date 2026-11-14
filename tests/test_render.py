"""Every renderer, from fixture data: well-formed SVG, honest labels."""
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
import mc  # noqa: E402


def parse(svg):
    return ET.fromstring(svg)


class Textures(unittest.TestCase):
    def test_every_texture_is_16x16_rgb_and_deterministic(self):
        for name in mc.TEX:
            a = mc.TEX[name]()
            self.assertEqual(a.shape, (16, 16, 3), name)
            self.assertTrue((a == mc.TEX[name]()).all(), name)

    def test_every_block_names_known_textures(self):
        for kind, faces in mc.BLOCKS.items():
            for f in faces:
                self.assertIn(f, mc.TEX, kind)


class Panels(unittest.TestCase):
    def test_static_panels_parse(self):
        for svg in (P.intro(), P.about(), P.stack(), P.footer(), P.news_header("now", 12),
                    P.loading(590, 540, "Player stats")):
            parse(svg)
        for slug, lab, _, fill in P.LINKS:
            parse(P.button(slug, lab, fill))

    def test_stack_lists_every_item(self):
        svg = P.stack()
        for items in P.STACK.values():
            for _, lab in items:
                self.assertIn(lab, svg)


class Activity(unittest.TestCase):
    def setUp(self):
        self.d = fixtures.activity(today=dt.datetime.now(A.TZ).date())

    def test_calendar_and_stats_parse(self):
        parse(A.calendar(self.d["created"], self.d["recent"], self.d["all_days"], "now"))
        parse(A.stats_card(self.d["created"], self.d["recent"], self.d["all_days"]))

    def test_level_curve(self):
        self.assertEqual(A.level(0)[0], 0)
        lv, frac, need = A.level(2595)
        self.assertEqual(lv, 22)
        self.assertTrue(0 <= frac < 1)
        self.assertEqual(need, A.XP_PER * 23 ** 2 - 2595)

    def test_every_level_has_a_block_face(self):
        for name in A.FACE[1:]:
            self.assertIn(name, mc.TEX)


class Log(unittest.TestCase):
    def test_render_parses_and_names_the_newest_commit(self):
        commits = fixtures.commits()
        svg = L.render(commits, "now")
        parse(svg)
        self.assertIn(commits[0]["message"][:20], svg)

    def test_empty_log_still_renders(self):
        parse(L.render([], "now"))

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

    def test_conventional_prefix_becomes_a_tag(self):
        self.assertEqual(L.kind("feat(ui): x")[0], "FEAT")
        self.assertEqual(L.kind("plain message")[0], "COMMIT")
        self.assertEqual(L.body_of("fix: rounding"), "rounding")
        self.assertEqual(L.body_of("plain: message"), "plain: message")

    def test_markup_in_a_commit_message_is_escaped(self):
        c = fixtures.commits()
        c[0]["message"] = "feat: <script>alert(1)</script> & more"
        svg = L.render(c, "now")
        parse(svg)
        self.assertNotIn("<script>", svg)


if __name__ == "__main__":
    unittest.main()
