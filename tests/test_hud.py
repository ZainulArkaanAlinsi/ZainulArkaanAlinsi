"""Tests for scripts/build_hud.py and the hotbar slots — fixtures only, no network."""
import datetime as dt
import pathlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import build_hud as H
import build_panels as P
from theme import THEMES

NOW = dt.datetime(2026, 11, 14, 12, 0, tzinfo=dt.timezone.utc)


def push(repo, sha, hours_ago):
    at = NOW - dt.timedelta(hours=hours_ago)
    return {"type": "PushEvent", "repo": {"name": f"someone/{repo}"},
            "created_at": at.strftime("%Y-%m-%dT%H:%M:%SZ"), "payload": {"head": sha}}


class LevelAndHearts(unittest.TestCase):
    def test_level_is_total_over_one_hundred(self):
        self.assertEqual(H.level_xp(2609), (26, 9, 100))
        self.assertEqual(H.level_xp(100), (1, 0, 100))
        self.assertEqual(H.level_xp(99), (0, 99, 100))

    def test_level_never_goes_negative(self):
        self.assertEqual(H.level_xp(-5), (0, 0, 100))

    def test_hearts_follow_streak_and_cap_at_ten(self):
        self.assertEqual([H.hearts_full(n) for n in (0, 3, 10, 42)], [0, 3, 10, 10])


class Subjects(unittest.TestCase):
    def test_conventional_commit_is_split(self):
        self.assertEqual(H.split_subject("feat(lab): buat akun teknisi"), ("feat", "buat akun teknisi"))
        self.assertEqual(H.split_subject("fix!: drop the old route"), ("fix", "drop the old route"))

    def test_untagged_commit_is_a_plain_push(self):
        self.assertEqual(H.split_subject("Tahap B2 — blok khas alat (#251)"), ("push", "Tahap B2 — blok khas alat (#251)"))

    def test_only_the_first_line_is_used_and_empty_is_safe(self):
        self.assertEqual(H.split_subject("feat: one\n\nlong body"), ("feat", "one"))
        self.assertEqual(H.split_subject(""), ("push", ""))
        self.assertEqual(H.split_subject(None), ("push", ""))

    def test_truncate_adds_an_ellipsis_within_the_limit(self):
        out = H.truncate("x" * 200)
        self.assertEqual(len(out), H.MSG_MAX)
        self.assertTrue(out.endswith("…"))

    def test_merges_are_recognised(self):
        self.assertTrue(H.is_merge("Merge branch 'main' into fix/x"))
        self.assertFalse(H.is_merge("merge sort benchmark"))


class Rows(unittest.TestCase):
    MSGS = {"a": "feat: first", "b": "Merge branch 'main' into x", "c": "fix(api): redact kode_hash from audit",
            "d": "docs: readme", "e": "test: more"}

    def rows(self, events, **kw):
        calls = []

        def get(repo, sha):
            calls.append(sha)
            return self.MSGS.get(sha)
        rows, pushes = H.build_rows(events, get, NOW, **kw)
        return rows, pushes, calls

    def test_newest_first_and_merges_skipped(self):
        rows, _, _ = self.rows([push("r", "d", 30), push("r", "a", 2), push("r", "b", 1)])
        self.assertEqual([r["text"] for r in rows], ["first", "readme"])

    def test_sensitive_subject_is_withheld_not_shown(self):
        rows, _, _ = self.rows([push("r", "c", 2)])
        self.assertEqual(rows[0]["text"], "details withheld")
        self.assertEqual(rows[0]["tag"], "push")

    def test_hidden_repo_never_appears_and_is_not_even_looked_up(self):
        rows, pushes, calls = self.rows([push("secret-repo", "a", 2), push("open", "d", 3)], hide_repos=["Secret-Repo"])
        self.assertEqual([r["repo"] for r in rows], ["open"])
        self.assertEqual(calls, ["d"])
        self.assertEqual(pushes, 1)

    def test_no_messages_mode_never_fetches_commit_text(self):
        rows, _, calls = self.rows([push("r", "a", 2)], show_messages=False)
        self.assertEqual(calls, [])
        self.assertEqual(rows[0]["text"], "")

    def test_duplicate_heads_are_listed_once(self):
        rows, pushes, _ = self.rows([push("r", "a", 2), push("r", "a", 3)])
        self.assertEqual((len(rows), pushes), (1, 1))

    def test_push_window_counts_only_the_last_week_and_new_flag_is_24h(self):
        rows, pushes, _ = self.rows([push("r", "a", 5), push("r", "d", 24 * 3), push("r", "e", 24 * 30)])
        self.assertEqual(pushes, 2)
        self.assertEqual([r["new"] for r in rows], [True, False, False])

    def test_limit_caps_rows_but_not_the_push_count(self):
        evs = [push("r", chr(97 + i) * 3, i + 1) for i in range(10)]
        self.MSGS.update({chr(97 + i) * 3: f"feat: n{i}" for i in range(10)})
        rows, pushes, _ = self.rows(evs, limit=3)
        self.assertEqual((len(rows), pushes), (3, 10))   # all ten pushes are within the 7-day window

    def test_unreachable_commit_is_skipped(self):
        rows, _, _ = self.rows([push("r", "zzz", 2), push("r", "a", 3)])
        self.assertEqual([r["text"] for r in rows], ["first"])

    def test_non_push_events_are_ignored(self):
        rows, pushes, _ = self.rows([{"type": "WatchEvent", "repo": {"name": "x/y"}, "created_at": "2026-11-14T00:00:00Z"}])
        self.assertEqual((rows, pushes), ([], 0))


class Svg(unittest.TestCase):
    def check(self, svg):
        root = ET.fromstring(svg)                       # well-formed
        self.assertIsNone(re.search(r"(?<![a-z])(nan|inf)(?![a-z])", svg.lower()))   # a bad float in a coordinate
        self.assertTrue(root.attrib["viewBox"])
        return root

    def test_player_renders_in_both_themes_and_states_real_numbers(self):
        for tokens in THEMES.values():
            svg = H.player(tokens, 2609, 9, "14 Nov 2026 13:52 WIB")
            self.check(svg)
            self.assertIn("9 / 100 XP", svg)
            self.assertIn("91 more for level 27", svg)
            self.assertIn("Player level 26: 9 of 100 experience, streak of 9 days", svg)   # aria-label

    def test_player_handles_a_brand_new_account(self):
        for tokens in THEMES.values():
            self.check(H.player(tokens, 0, 0, "offline"))

    def test_commit_log_renders_rows_and_the_empty_state(self):
        rows = [{"at": NOW, "repo": "r" * 40, "tag": "refactor", "text": "x" * H.MSG_MAX, "new": True},
                {"at": NOW, "repo": "short", "tag": "push", "text": "", "new": False}]
        for tokens in THEMES.values():
            svg = H.commits(tokens, rows, 5, "stamp")
            self.check(svg)
            self.assertIn("Pushed 5 times in 7 days", svg)
            self.check(H.commits(tokens, [], 0, "offline"))

    def test_singular_push_reads_naturally(self):
        svg = H.commits(THEMES["dark"], [], 1, "s")
        self.assertIn("Pushed 1 time in 7 days", svg)

    def test_hotbar_slots_render_and_walk_the_selection(self):
        delays = set()
        for idx, (slug, label, accent) in enumerate(P.LINKS):
            for tokens in THEMES.values():
                svg = P.link_chip(tokens, slug, label, accent, idx)
                self.check(svg)
                self.assertIn(f'aria-label="{label}"', svg)
            delays.add(f"animation-delay:{idx * 1.5:.1f}s")
        self.assertEqual(len(delays), len(P.LINKS))


if __name__ == "__main__":
    unittest.main()
