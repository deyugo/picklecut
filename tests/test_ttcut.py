"""Tests for ttcut V2.4 (table tennis) — the features ported back from
picklecut V1.1 plus a guard that the table-tennis scoring did not move.

Loads both language builds directly from their files and checks:
  - serve rotation (two serves each, one at deuce) is unchanged
  - adjust events: games / points / server overrides, rotation restart,
    games-only correction while a game is pending
  - highlight_ranges: rally attribution, merging, edge cases
  - plan(): caption / highlight / adjust events do not disturb the let
    (serve→serve) adjacency test; highlights render scope; hl key
  - build_ass(): captions are burned in, re-timed across cuts, escaped,
    and dropped when they fall entirely inside a cut
  - EN / zh-TW builds produce identical fold, plan and ASS output
    (apart from the version comment line)

Run from the repo root:  python -m unittest discover -s tests -v
"""

import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(fname, modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(ROOT, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ZH = load("ttcut_v2_4.py", "ttcut_zh")
EN = load("ttcut_v2_4_EN.py", "ttcut_en")

FMT = dict(target=11, deuce="standard", cap=12)
START0 = dict(games=[0, 0], points=[0, 0], scope="every")
LEAD, TAIL = 0.3, 1.0


def ev(seq, t0=0.0, step=10.0):
    """Compact event builder: 'sAsBg' -> serve, point A, serve, point B, game."""
    out, t = [], t0
    for ch in seq:
        t += step
        if ch == "s":
            out.append(dict(t=t, type="serve"))
        elif ch in "AB":
            out.append(dict(t=t, type="point", winner=ch))
        elif ch == "g":
            out.append(dict(t=t, type="game"))
    return out


def rallies(seq):
    return ev("".join("s" + c for c in seq))


def doc_of(events, **kw):
    d = dict(events=events, fps=30, players={"A": "A", "B": "B"},
             firstServer="A", pads={"tail": TAIL, "lead": LEAD})
    d.update(kw)
    return d


class ServeRotationUnchanged(unittest.TestCase):
    def test_two_serves_each(self):
        cur = ZH.fold_full(rallies("AAB"), FMT, START0, 0)["cur"]
        self.assertEqual((cur["a"], cur["b"], cur["server"]), (2, 1, 1))
        cur = ZH.fold_full(rallies("AABB"), FMT, START0, 0)["cur"]
        self.assertEqual(cur["server"], 0)

    def test_one_serve_each_at_deuce(self):
        seq = "A" * 10 + "B" * 10          # 10-10
        cur = ZH.fold_full(rallies(seq), FMT, START0, 0)["cur"]
        srv = cur["server"]
        cur2 = ZH.fold_full(rallies(seq + "A"), FMT, START0, 0)["cur"]
        self.assertEqual(cur2["server"], 1 - srv)

    def test_states_are_seven_tuples(self):
        st = ZH.fold_full(rallies("A"), FMT, START0, 0)["states"]
        self.assertTrue(all(len(s) == 7 for s in st))
        self.assertTrue(all(s[6] == 1 for s in st))           # singles: player 1 always


class AdjustEvents(unittest.TestCase):
    def test_points_and_server_override(self):
        events = rallies("AA") + [dict(t=45, type="adjust",
                                       points={"A": 5, "B": 3}, server="B")]
        r = ZH.fold_full(events, FMT, START0, 0)
        self.assertEqual(r["states"][-1][:5], (45, 0, 0, 5, 3))
        self.assertEqual(r["cur"]["server"], 1)
        self.assertIsNone(r["snaps"][-1])

    def test_rotation_restarts_from_named_server(self):
        # After the correction B serves; B keeps serving for two points.
        events = rallies("AA") + [dict(t=45, type="adjust", server="B")] \
            + ev("sA", t0=45)
        cur = ZH.fold_full(events, FMT, START0, 0)["cur"]
        self.assertEqual(cur["server"], 1)
        events += ev("sA", t0=65)
        cur = ZH.fold_full(events, FMT, START0, 0)["cur"]
        self.assertEqual(cur["server"], 0)

    def test_partial_points_override_keeps_other_side(self):
        events = rallies("AAB") + [dict(t=99, type="adjust", points={"B": 7})]
        cur = ZH.fold_full(events, FMT, START0, 0)["cur"]
        self.assertEqual((cur["a"], cur["b"]), (2, 7))

    def test_games_only_while_pending_starts_next_game_normally(self):
        events = rallies("A" * 11)                          # 11-0, game to A
        events.append(dict(t=999, type="adjust", games={"A": 2}))
        events += ev("sB", t0=1000)
        cur = ZH.fold_full(events, FMT, START0, 0)["cur"]
        self.assertEqual((cur["gA"], cur["gB"]), (2, 0))
        self.assertEqual((cur["a"], cur["b"]), (0, 1))     # new game, not 11-1
        self.assertEqual(cur["gameNo"], 3)

    def test_points_override_while_pending_continues_that_game(self):
        events = rallies("A" * 11)
        events.append(dict(t=999, type="adjust", points={"A": 9, "B": 9}))
        events += ev("sA", t0=1000)
        cur = ZH.fold_full(events, FMT, START0, 0)["cur"]
        self.assertEqual((cur["a"], cur["b"]), (10, 9))
        self.assertEqual(cur["gA"], 1)                      # first game still counted once

    def test_empty_adjust_is_a_noop_state(self):
        events = rallies("A") + [dict(t=15, type="adjust")]
        r = ZH.fold_full(events, FMT, START0, 0)
        self.assertEqual(r["states"][-1][:5], (15, 0, 0, 1, 0))
        self.assertEqual(r["cur"]["server"], 0)


FMT_D = dict(FMT, doubles=True)


class Doubles(unittest.TestCase):
    def seq(self, s, first=0, fmt=FMT_D):
        return [(st[5], st[6]) for st in ZH.fold_full(rallies(s), fmt, START0, first)["states"]]

    def test_rotation_A1_B1_A2_B2(self):
        self.assertEqual(self.seq("AABBAABB"),
                         [(0, 1), (0, 1), (1, 1), (1, 1), (0, 2), (0, 2), (1, 2), (1, 2), (0, 1)])

    def test_first_server_B(self):
        self.assertEqual(self.seq("AAB", first=1)[:4], [(1, 1), (1, 1), (0, 1), (0, 1)])

    def test_singles_is_always_player_one(self):
        self.assertTrue(all(n == 1 for _, n in self.seq("AABBAABB", fmt=FMT)))

    def test_new_game_restarts_at_player_one(self):
        cur = ZH.fold_full(rallies("A" * 11), FMT_D, START0, 0)["cur"]
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 1))
        cur = ZH.fold_full(rallies("A" * 11 + "B"), FMT_D, START0, 0)["cur"]
        self.assertEqual((cur["server"], cur["serverNum"]), (1, 1))

    def test_deuce_keeps_rotating_players(self):
        seq = "A" * 10 + "B" * 10                                    # 10-10
        base = ZH.fold_full(rallies(seq), FMT_D, START0, 0)["states"][-1]
        nxt = ZH.fold_full(rallies(seq + "A"), FMT_D, START0, 0)["states"][-1]
        self.assertNotEqual(base[5], nxt[5])                          # one serve each now
        self.assertIn(nxt[6], (1, 2))

    def test_adjust_server_num(self):
        # A has served one point (still A's turn): switch A to player 2
        events = rallies("A") + [dict(t=25, type="adjust", serverNum=2)]
        r = ZH.fold_full(events, FMT_D, START0, 0)
        self.assertEqual((r["cur"]["server"], r["cur"]["serverNum"]), (0, 2))
        # A#2 finishes the turn, B#1 serves two, then A comes back with player 1
        events += ev("sAsBsBsA", t0=25)
        st = ZH.fold_full(events, FMT_D, START0, 0)["states"]
        self.assertEqual([x[5:] for x in st[-4:]], [(1, 1), (1, 1), (0, 1), (0, 1)])
        # serverNum is ignored in singles
        r = ZH.fold_full(rallies("AA") + [dict(t=45, type="adjust", serverNum=2)], FMT, START0, 0)
        self.assertEqual(r["cur"]["serverNum"], 1)

    def test_ass_serve_dots(self):
        pl = ZH.plan(doc_of(rallies("AABB"), format=dict(pointsPerGame=11, deuce="standard",
                                                          cap=12, side="doubles")), {})
        ass = ZH.build_ass(pl["scoring"]["states"], pl["src2out"], pl["total"], ["A", "B"], 1920, 1080)
        dots = [l.split(",,")[-1] for l in ass.splitlines() if "●" in l or "●" in l]
        self.assertTrue(any(d.endswith("●●") for d in dots))
        pl = ZH.plan(doc_of(rallies("AABB")), {})
        ass = ZH.build_ass(pl["scoring"]["states"], pl["src2out"], pl["total"], ["A", "B"], 1920, 1080)
        dots = [l.split(",,")[-1] for l in ass.splitlines() if "●" in l]
        self.assertTrue(dots and all(d.endswith("}●") for d in dots))


class HighlightRanges(unittest.TestCase):
    def test_attributed_to_preceding_serve_during_or_after_rally(self):
        events = rallies("AB")                               # s10 A20 s30 B40
        for t in (15, 20, 25):                               # mid-rally / at / after
            evs = sorted(events + [dict(t=t, type="highlight")], key=lambda e: e["t"])
            self.assertEqual(ZH.highlight_ranges(evs, LEAD, TAIL),
                             [(10 - LEAD, 20 + TAIL)])

    def test_overlapping_ranges_merge(self):
        events = rallies("AB") + [dict(t=15, type="highlight"),
                                  dict(t=35, type="highlight")]
        events.sort(key=lambda e: e["t"])
        self.assertEqual(ZH.highlight_ranges(events, LEAD, TAIL),
                         [(10 - LEAD, 20 + TAIL), (30 - LEAD, 40 + TAIL)])
        # tail of rally 1 (21.0) touching lead of rally 2 (29.7)? no — but
        # a big tail merges them
        self.assertEqual(ZH.highlight_ranges(events, LEAD, 12.0),
                         [(10 - LEAD, 40 + 12.0)])

    def test_highlight_before_first_serve_or_without_point_is_ignored(self):
        events = [dict(t=5, type="highlight")] + rallies("A") \
            + [dict(t=30, type="serve"), dict(t=35, type="highlight")]
        self.assertEqual(ZH.highlight_ranges(events, LEAD, TAIL),
                         [])  # first is before any serve; last serve has no point
        events2 = [dict(t=5, type="highlight")] + rallies("A") \
            + [dict(t=25, type="highlight")]
        self.assertEqual(ZH.highlight_ranges(events2, LEAD, TAIL),
                         [(10 - LEAD, 20 + TAIL)])

    def test_never_negative_start(self):
        events = [dict(t=0.1, type="serve"), dict(t=5, type="point", winner="A"),
                  dict(t=3, type="highlight")]
        events.sort(key=lambda e: e["t"])
        self.assertEqual(ZH.highlight_ranges(events, LEAD, TAIL)[0][0], 0.0)


class Plan(unittest.TestCase):
    def test_non_cut_events_do_not_break_let_detection(self):
        base = ev("ssA")                                     # let at 10, serve 20, point 30
        want = ZH.plan(doc_of(base), dict(min_cut=2.0, cut_lets=True))["cuts"]
        self.assertEqual(len(want), 1)
        for extra in (dict(t=15, type="caption", text="c", dur=1),
                      dict(t=15, type="highlight"),
                      dict(t=15, type="adjust", points={"A": 1})):
            evs = sorted(base + [extra], key=lambda e: e["t"])
            got = ZH.plan(doc_of(evs), dict(min_cut=2.0, cut_lets=True))["cuts"]
            self.assertEqual(got, want, extra["type"])

    def test_hl_key_always_present(self):
        pl = ZH.plan(doc_of(rallies("A")), {})
        self.assertEqual(pl["hl"], [])
        pl = ZH.plan(doc_of([]), {})
        self.assertFalse(pl["ok"])
        self.assertEqual(pl["hl"], [])

    def test_highlights_scope(self):
        events = rallies("ABA") + [dict(t=15, type="highlight"),
                                   dict(t=55, type="highlight")]
        events.sort(key=lambda e: e["t"])
        pl = ZH.plan(doc_of(events), dict(scope="highlights"))
        self.assertTrue(pl["ok"])
        self.assertEqual(pl["keeps"], [(10 - LEAD, 20 + TAIL), (50 - LEAD, 60 + TAIL)])
        self.assertEqual(pl["cuts"], [])
        self.assertAlmostEqual(pl["total"], 2 * (10 + LEAD + TAIL))
        # scoreboard mapper: a time inside the second rally maps after the first
        self.assertAlmostEqual(pl["src2out"](55.0), (10 + LEAD + TAIL) + (55 - (50 - LEAD)))

    def test_highlights_scope_without_marks_fails_with_reason(self):
        pl = ZH.plan(doc_of(rallies("A")), dict(scope="highlights"))
        self.assertFalse(pl["ok"])
        self.assertTrue(pl["reason"])
        self.assertEqual(pl["keeps"], [])

    def test_full_scope_ignores_highlights_for_cutting(self):
        events = rallies("AB") + [dict(t=15, type="highlight")]
        events.sort(key=lambda e: e["t"])
        a = ZH.plan(doc_of(events), dict(min_cut=2.0))
        b = ZH.plan(doc_of(rallies("AB")), dict(min_cut=2.0))
        self.assertEqual(a["keeps"], b["keeps"])
        self.assertEqual(a["hl"], [(10 - LEAD, 20 + TAIL)])


class Captions(unittest.TestCase):
    def ass(self, mod, captions, events=None):
        pl = mod.plan(doc_of(events or rallies("AB")), dict(min_cut=2.0))
        return mod.build_ass(pl["scoring"]["states"], pl["src2out"], pl["total"],
                             ["A", "B"], 1920, 1080, captions=captions)

    def test_cap_style_and_dialogue(self):
        ass = self.ass(ZH, [(12.0, 3.0, "hello")])
        self.assertIn("Style: Cap,", ass)
        caps = [l for l in ass.splitlines() if ",Cap," in l]
        self.assertEqual(len(caps), 1)
        self.assertTrue(caps[0].endswith(",hello"))
        # 12.0 source -> 12.0 - (10 - LEAD) output
        self.assertIn("0:00:02.30,0:00:05.30", caps[0])

    def test_braces_and_newlines_are_escaped(self):
        ass = self.ass(ZH, [(12.0, 3.0, "a{b}\nc")])
        caps = [l for l in ass.splitlines() if ",Cap," in l]
        self.assertTrue(caps[0].endswith(r",a(b)\Nc"))

    def test_caption_inside_cut_is_dropped_and_across_cut_is_retimed(self):
        # rallies("AB"): keep 9.7-21.0, cut 21.0-29.7, keep 29.7-41.0
        ass = self.ass(ZH, [(23.0, 3.0, "gone")])
        self.assertFalse([l for l in ass.splitlines() if ",Cap," in l])
        ass = self.ass(ZH, [(20.0, 15.0, "spans")])
        caps = [l for l in ass.splitlines() if ",Cap," in l]
        self.assertEqual(len(caps), 1)
        # starts at out 10.3, ends at src 35 -> out 11.3 + 5.3 = 16.6
        self.assertIn("0:00:10.30,0:00:16.60", caps[0])

    def test_no_captions_leaves_ass_unchanged_except_style_line(self):
        a = self.ass(ZH, [])
        b = self.ass(ZH, ())
        self.assertEqual(a, b)
        self.assertFalse([l for l in a.splitlines() if ",Cap," in l])


class LanguageParity(unittest.TestCase):
    EVENTS = sorted(rallies("AABBA") + [
        dict(t=15, type="highlight"),
        dict(t=33, type="caption", text="x{y}", dur=2.5),
        dict(t=66, type="adjust", points={"A": 7}, games={"B": 1}, server="B"),
        dict(t=95, type="highlight"),
    ], key=lambda e: e["t"])

    def test_fold_identical(self):
        self.assertEqual(ZH.fold_full(self.EVENTS, FMT, START0, 0),
                         EN.fold_full(self.EVENTS, FMT, START0, 0))

    def test_highlights_identical(self):
        self.assertEqual(ZH.highlight_ranges(self.EVENTS, LEAD, TAIL),
                         EN.highlight_ranges(self.EVENTS, LEAD, TAIL))

    def test_plan_identical(self):
        for opt in ({}, dict(scope="highlights"), dict(cut_lets=True)):
            a = ZH.plan(doc_of(self.EVENTS), opt)
            b = EN.plan(doc_of(self.EVENTS), opt)
            for k in ("ok", "keeps", "hl", "total", "head", "end"):
                self.assertEqual(a[k], b[k], k)
            # cut tuples carry a language-specific reason label in [2]
            for k in ("cuts", "dropped"):
                self.assertEqual([c[:2] for c in a[k]], [c[:2] for c in b[k]], k)

    def test_ass_identical_apart_from_version_comment(self):
        def strip(s):
            return "\n".join(l for l in s.splitlines() if not l.startswith("; "))
        caps = [(33.0, 2.5, "x{y}")]
        outs = []
        for mod in (ZH, EN):
            pl = mod.plan(doc_of(self.EVENTS), dict(min_cut=2.0))
            outs.append(strip(mod.build_ass(pl["scoring"]["states"], pl["src2out"],
                                            pl["total"], ["A", "B"], 1920, 1080,
                                            captions=caps)))
        self.assertEqual(outs[0], outs[1])

    def test_versions_match(self):
        self.assertEqual(ZH.VERSION.split("-")[0], EN.VERSION.split("-")[0])


class JoinCli(unittest.TestCase):
    def test_join_needs_two_files(self):
        with self.assertRaises(SystemExit):
            ZH.join_videos(["only_one.mp4"], None, None)
        with self.assertRaises(SystemExit):
            EN.join_videos(["only_one.mp4"], None, None)


if __name__ == "__main__":
    unittest.main()
