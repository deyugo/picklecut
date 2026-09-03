"""Scoring-engine tests for picklecut V1 (pickleball).

Loads both language builds directly from their files and checks:
  - doubles side-out rules (0-0-2 start, server #1 -> #2 -> side-out)
  - only the serving side scores; games end only on a serving-side point
  - win-by-2 and capped endings
  - singles side-out
  - rally mode (every rally scores, serve follows the winner)
  - game events, handicap, starting games, next-game server alternation
  - EN / zh-TW builds produce identical fold output and identical ASS
    (apart from the version comment line)

Run from the repo root:  python -m unittest discover -s tests -v
"""

import importlib.util
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(fname, modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(ROOT, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EN = load("picklecut_v1_1_EN.py", "picklecut_en")

FMT_DOUBLES = dict(target=11, deuce="standard", cap=12, scoring="sideout", doubles=True)
FMT_SINGLES = dict(target=11, deuce="standard", cap=12, scoring="sideout", doubles=False)
FMT_RALLY = dict(target=11, deuce="standard", cap=12, scoring="rally", doubles=True)
START0 = dict(games=[0, 0], points=[0, 0], scope="every")


def ev(seq):
    """Compact event builder: 'sABg' -> serve, point A, point B, game.
    Each rally is preceded by a serve so cut logic stays realistic."""
    out, t = [], 0.0
    for ch in seq:
        t += 10.0
        if ch == "s":
            out.append(dict(t=t, type="serve"))
        elif ch in "AB":
            out.append(dict(t=t, type="point", winner=ch))
        elif ch == "g":
            out.append(dict(t=t, type="game"))
    return out


def rallies(seq):
    """'AB' -> serve+rally-won-by-A, serve+rally-won-by-B, ..."""
    return ev("".join("s" + c for c in seq))


class DoublesSideOut(unittest.TestCase):
    def fold(self, seq, first_server=0, fmt=None, start=None):
        return EN.fold_full(rallies(seq), fmt or FMT_DOUBLES,
                            start or START0, first_server)

    def test_initial_state_is_0_0_2(self):
        r = EN.fold_full([], FMT_DOUBLES, START0, 0)
        t, gA, gB, a, b, srv, num = r["states"][0]
        self.assertIsNone(t)
        self.assertEqual((a, b, srv, num), (0, 0, 0, 2))

    def test_receivers_win_first_rally_is_immediate_side_out(self):
        # Team A starts at server #2; losing the rally is a side-out, no point.
        r = self.fold("B")
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (0, 0))
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 1))
        self.assertFalse(r["snaps"][-1]["scored"])

    def test_serving_side_scores_and_keeps_server(self):
        r = self.fold("AA")     # A serves at #2 and wins twice
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (2, 0))
        self.assertEqual((cur["server"], cur["serverNum"]), (0, 2))

    def test_server1_then_server2_then_side_out(self):
        # A(#2) loses -> B at #1. B loses -> B at #2. B loses -> A at #1.
        r = self.fold("BAA")
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (0, 0))       # no one scored
        self.assertEqual((cur["server"], cur["serverNum"]), (0, 1))

    def test_receiver_rally_win_never_scores(self):
        # Winners chosen so the receiving side wins every rally: the serve
        # cycles A#2 -> B#1 -> B#2 -> A#1 -> A#2 and nobody ever scores.
        r = self.fold("BAAB")
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (0, 0))
        self.assertEqual((cur["server"], cur["serverNum"]), (0, 2))

    def test_game_ends_only_on_serving_side_point(self):
        # A wins 11 straight on serve: 11-0, game to A.
        r = self.fold("A" * 11)
        cur = r["cur"]
        self.assertEqual((cur["gA"], cur["gB"]), (1, 0))
        self.assertTrue(cur["pending"])
        # Next game: B serves first, back at #2.
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 2))

    # Serve transfer in the deuce sequences below: after a side scores on
    # serve, the other side needs two rally wins (server #1 -> #2 -> side-out)
    # before it can score itself. "A"*10 leaves A serving at 10-0; "B" is the
    # side-out; "B"*10 leaves B serving at 10-10; "AAA" walks the serve back
    # to A (#1 -> #2 -> side-out) and scores once.
    DEUCE_10_10_A11 = "A" * 10 + "B" + "B" * 10 + "AAA"

    def test_no_game_at_11_10(self):
        r = self.fold(self.DEUCE_10_10_A11)
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (11, 10))
        self.assertEqual((cur["gA"], cur["gB"]), (0, 0))

    def test_win_by_two_at_deuce(self):
        r = self.fold(self.DEUCE_10_10_A11 + "A")        # 12-10, two clear
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (12, 10))
        self.assertEqual((cur["gA"], cur["gB"]), (1, 0))

    def test_capped_ends_without_two_clear(self):
        fmt = dict(FMT_DOUBLES, deuce="capped", cap=12)
        # Walk the serve back to B at 11-10 and let B score to 11-11, then 11-12:
        # the cap ends the game one point clear, which standard would not.
        seq = self.DEUCE_10_10_A11 + "BBB" + "B"
        r = self.fold(seq, fmt=fmt)
        self.assertEqual((r["cur"]["a"], r["cur"]["b"]), (11, 12))
        self.assertEqual(r["cur"]["gB"], 1)

    def test_manual_game_event_resets_and_alternates_server(self):
        events = rallies("AA") + ev("g")
        r = EN.fold_full(events, FMT_DOUBLES, START0, 0)
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (0, 0))
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 2))

    def test_handicap_and_starting_games(self):
        start = dict(games=[1, 0], points=[5, 3], scope="every")
        r = EN.fold_full([], FMT_DOUBLES, start, 0)
        t, gA, gB, a, b, srv, num = r["states"][0]
        self.assertEqual((gA, gB, a, b), (1, 0, 5, 3))
        self.assertEqual(num, 2)

    def test_states_are_seven_tuples(self):
        r = self.fold("AB")
        for st in r["states"]:
            self.assertEqual(len(st), 7)

    def test_start_server_number_continuation(self):
        # A video that picks up mid-game with the serving team on server #1:
        # a lost rally goes to the partner (#2), not straight to a side-out.
        start = dict(games=[1, 0], points=[5, 3], scope="first", serverNum=1)
        r = EN.fold_full(rallies("B"), FMT_DOUBLES, start, 0)
        cur = r["cur"]
        self.assertEqual((cur["server"], cur["serverNum"]), (0, 2))
        self.assertEqual((cur["a"], cur["b"]), (5, 3))

    def test_start_server_number_resets_next_game(self):
        # The override applies to the opening state only; a fresh game goes
        # back to the 0-0-2 start.
        start = dict(games=[0, 0], points=[0, 0], scope="every", serverNum=1)
        events = rallies("A") + ev("g")
        r = EN.fold_full(events, FMT_DOUBLES, start, 0)
        self.assertEqual(r["cur"]["serverNum"], 2)


class SinglesSideOut(unittest.TestCase):
    def fold(self, seq, first_server=0):
        return EN.fold_full(rallies(seq), FMT_SINGLES, START0, first_server)

    def test_no_server_numbers(self):
        r = self.fold("")
        self.assertEqual(r["states"][0][6], 1)

    def test_side_out_passes_serve_directly(self):
        r = self.fold("B")    # server A loses -> B serves, no point
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (0, 0))
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 1))

    def test_server_scores(self):
        r = self.fold("AAB")   # A scores twice, then loses serve
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (2, 0))
        self.assertEqual(cur["server"], 1)


class RallyScoring(unittest.TestCase):
    def fold(self, seq, first_server=0):
        return EN.fold_full(rallies(seq), FMT_RALLY, START0, first_server)

    def test_every_rally_scores(self):
        r = self.fold("ABAB")
        self.assertEqual((r["cur"]["a"], r["cur"]["b"]), (2, 2))

    def test_serve_follows_winner(self):
        r = self.fold("B")
        self.assertEqual(r["cur"]["server"], 1)
        r = self.fold("BA")
        self.assertEqual(r["cur"]["server"], 0)

    def test_game_end_and_win_by_two(self):
        r = self.fold("A" * 10 + "B" * 10 + "AA")
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (12, 10))
        self.assertEqual(cur["gA"], 1)


class AdjustEvents(unittest.TestCase):
    def test_adjust_overrides_only_given_fields(self):
        events = rallies("AA") + [
            dict(t=100.0, type="adjust", points=dict(A=7, B=4),
                 server="B", serverNum=1),
            dict(t=110.0, type="serve"),
            dict(t=118.0, type="point", winner="B"),
        ]
        # After the correction B serves at #1 with 7-4; B winning scores.
        r = EN.fold_full(events, FMT_DOUBLES, START0, 0)
        cur = r["cur"]
        self.assertEqual((cur["a"], cur["b"]), (7, 5))
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 1))

    def test_adjust_games_mid_match(self):
        events = [dict(t=5.0, type="adjust", games=dict(A=1, B=1))] + rallies("A")
        r = EN.fold_full(events, FMT_DOUBLES, START0, 0)
        self.assertEqual((r["cur"]["gA"], r["cur"]["gB"]), (1, 1))
        self.assertEqual(r["cur"]["gameNo"], 3)


class HighlightPlan(unittest.TestCase):
    DOC = dict(
        players=dict(A="A", B="B"), firstServer="A", fps=30,
        format=dict(pointsPerGame=11, deuce="standard", cap=12,
                    scoring="sideout", side="doubles"),
        start=dict(games=dict(A=0, B=0), points=dict(A=0, B=0),
                   handicapScope="every"),
        pads=dict(tail=1.0, lead=0.5),
        events=[
            dict(t=10.0, type="serve"),
            dict(t=18.0, type="point", winner="A"),
            dict(t=30.0, type="serve"),
            dict(t=33.0, type="highlight"),           # marks rally 2
            dict(t=39.0, type="point", winner="B"),
            dict(t=55.0, type="serve"),
            dict(t=61.0, type="point", winner="B"),
        ])

    def test_highlight_scope_keeps_only_marked_rally(self):
        pl = EN.plan(self.DOC, dict(min_cut=2.0, scope="highlights"))
        self.assertTrue(pl["ok"])
        self.assertEqual(pl["keeps"], [(29.5, 40.0)])   # serve-lead .. point+tail

    def test_highlight_after_rally_end_belongs_to_it(self):
        doc = dict(self.DOC)
        doc["events"] = [dict(e) for e in self.DOC["events"]
                         if e["type"] != "highlight"]
        doc["events"].append(dict(t=42.0, type="highlight"))  # after rally 2 ended
        doc["events"].sort(key=lambda e: e["t"])
        pl = EN.plan(doc, dict(min_cut=2.0, scope="highlights"))
        self.assertEqual(pl["keeps"], [(29.5, 40.0)])

    def test_no_marks_fails_cleanly(self):
        doc = dict(self.DOC)
        doc["events"] = [e for e in self.DOC["events"] if e["type"] != "highlight"]
        pl = EN.plan(doc, dict(min_cut=2.0, scope="highlights"))
        self.assertFalse(pl["ok"])

    def test_full_scope_ignores_highlight_marks(self):
        pl = EN.plan(self.DOC, dict(min_cut=2.0))
        self.assertTrue(pl["ok"])
        self.assertEqual(len(pl["cuts"]), 2)            # both inter-rally gaps cut
        self.assertEqual(pl["hl"], [(29.5, 40.0)])      # ranges still reported


class ReadFormat(unittest.TestCase):
    def test_defaults(self):
        fmt, start = EN.read_format({})
        self.assertEqual(fmt["scoring"], "sideout")
        self.assertTrue(fmt["doubles"])
        self.assertEqual(fmt["target"], 11)
        self.assertEqual(start["serverNum"], 0)

    def test_server_num_read(self):
        _, start = EN.read_format(dict(start=dict(serverNum=1)))
        self.assertEqual(start["serverNum"], 1)

    def test_explicit(self):
        fmt, _ = EN.read_format(dict(format=dict(
            pointsPerGame=15, scoring="rally", side="singles",
            deuce="capped", cap=17)))
        self.assertEqual(fmt["target"], 15)
        self.assertEqual(fmt["scoring"], "rally")
        self.assertFalse(fmt["doubles"])
        self.assertEqual((fmt["deuce"], fmt["cap"]), ("capped", 17))


class AssOutput(unittest.TestCase):
    def test_server_dots_present(self):
        r = EN.fold_full(rallies("AB"), FMT_DOUBLES, START0, 0)
        src2out = lambda t: t
        ass = EN.build_ass(r["states"], src2out, 100.0, ["Team A", "Team B"],
                           1920, 1080)
        self.assertIn("●", ass)

    def test_captions_rendered_and_sanitized(self):
        r = EN.fold_full(rallies("AB"), FMT_DOUBLES, START0, 0)
        src2out = lambda t: t
        ass = EN.build_ass(r["states"], src2out, 100.0, ["A", "B"], 1920, 1080,
                           captions=[(5.0, 3.0, "nice {rally}\nhere")])
        self.assertIn("Cap", ass)
        self.assertIn(r"nice (rally)\Nhere", ass)

    def test_caption_inside_cut_is_dropped(self):
        r = EN.fold_full(rallies("AB"), FMT_DOUBLES, START0, 0)
        collapse = lambda t: 0.0          # everything maps to one instant
        ass = EN.build_ass(r["states"], collapse, 100.0, ["A", "B"], 1920, 1080,
                           captions=[(5.0, 3.0, "gone")])
        self.assertNotIn("gone", ass)


class BuildParity(unittest.TestCase):
    """The zh-TW build must behave identically to the EN build."""

    @classmethod
    def setUpClass(cls):
        cls.zh = load("picklecut_v1_1.py", "picklecut_zh")

    def test_fold_parity(self):
        seqs = ["", "B", "AA", "BAA", "A" * 11,
                "A" * 10 + "B" + "B" * 10 + "A" + "A" * 2]
        for fmt in (FMT_DOUBLES, FMT_SINGLES, FMT_RALLY):
            for seq in seqs:
                a = EN.fold_full(rallies(seq), fmt, START0, 0)
                b = self.zh.fold_full(rallies(seq), fmt, START0, 0)
                self.assertEqual(a["states"], b["states"], (fmt, seq))
                self.assertEqual(a["cur"], b["cur"], (fmt, seq))
                self.assertEqual(a["snaps"], b["snaps"], (fmt, seq))

    def test_fold_parity_with_server_number(self):
        start = dict(games=[1, 0], points=[5, 3], scope="first", serverNum=1)
        a = EN.fold_full(rallies("BAAB"), FMT_DOUBLES, start, 0)
        b = self.zh.fold_full(rallies("BAAB"), FMT_DOUBLES, start, 0)
        self.assertEqual(a["states"], b["states"])
        self.assertEqual(a["cur"], b["cur"])

    def test_ass_parity_minus_version_line(self):
        r = EN.fold_full(rallies("A" * 5 + "B" * 3), FMT_DOUBLES, START0, 0)
        src2out = lambda t: t
        strip = lambda s: re.sub(r"^; .*$", "", s, flags=re.M)
        caps = [(12.0, 3.0, "開場 {test}")]
        a = EN.build_ass(r["states"], src2out, 200.0, ["甲隊", "乙隊"], 1920, 1080,
                         captions=caps)
        b = self.zh.build_ass(r["states"], src2out, 200.0, ["甲隊", "乙隊"], 1920, 1080,
                              captions=caps)
        self.assertEqual(strip(a), strip(b))


if __name__ == "__main__":
    unittest.main()
