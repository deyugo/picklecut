"""Score report (<name>.score.txt) and the snap fields it relies on, across all
four builds (ttcut zh / EN, picklecut zh / EN).

  - snaps carry served / servedNum / gameNo for every point
  - rally_highlights attributes a highlight to the rally it falls in
  - score_report lists game results, an unfinished game, per-point rows
    with server / winner / score, highlight stars, adjust and game rows
  - picklecut marks side-outs; ttcut doubles shows #1 / #2
  - zh and EN builds agree on the numbers (text differs)

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


TT = {"zh": load("ttcut_v2_4.py", "rep_tt_zh"), "en": load("ttcut_v2_4_EN.py", "rep_tt_en")}
PC = {"zh": load("picklecut_v1_1.py", "rep_pc_zh"), "en": load("picklecut_v1_1_EN.py", "rep_pc_en")}


def ev(seq, t0=0.0):
    out, t = [], t0
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
    return ev("".join("s" + c for c in seq))


def doc_of(events, **fmt):
    f = dict(pointsPerGame=11, deuce="standard", cap=12)
    f.update(fmt)
    return dict(events=sorted(events, key=lambda e: e["t"]), fps=30,
                players={"A": "Ann", "B": "Bob"}, firstServer="A",
                pads={"tail": 1.0, "lead": 0.3}, format=f)


def report(mod, doc):
    pl = mod.plan(doc, {})
    return "\n".join(mod.score_report(pl, mod.doc_names(doc), "match.MOV"))


class SnapFields(unittest.TestCase):
    def test_ttcut_snaps(self):
        for m in TT.values():
            r = m.fold_full(rallies("A" * 11 + "B"), dict(target=11, deuce="standard", cap=12),
                            dict(games=[0, 0], points=[0, 0], scope="every"), 0)
            pts = [s for s in r["snaps"] if s]
            self.assertEqual([s["gameNo"] for s in pts], [1] * 11 + [2])
            self.assertEqual(pts[0]["served"], 0)
            self.assertEqual(pts[2]["served"], 1)          # B serves points 3-4
            self.assertEqual(pts[-1]["served"], 1)         # game 2: B serves first

    def test_picklecut_snaps(self):
        for m in PC.values():
            r = m.fold_full(rallies("BA"), dict(target=11, deuce="standard", cap=12,
                                                scoring="sideout", doubles=True),
                            dict(games=[0, 0], points=[0, 0], scope="every"), 0)
            pts = [s for s in r["snaps"] if s]
            self.assertEqual((pts[0]["served"], pts[0]["servedNum"]), (0, 2))   # 0-0-2 start
            self.assertEqual((pts[1]["served"], pts[1]["servedNum"]), (1, 1))   # after side-out
            self.assertEqual([s["gameNo"] for s in pts], [1, 1])


class RallyHighlights(unittest.TestCase):
    def test_attribution(self):
        for m in list(TT.values()) + list(PC.values()):
            events = rallies("AB") + [dict(t=15, type="highlight"), dict(t=41, type="highlight")]
            events.sort(key=lambda e: e["t"])
            pts = [i for i, e in enumerate(events) if e["type"] == "point"]
            self.assertEqual(m.rally_highlights(events), set(pts))
            self.assertEqual(m.rally_highlights([dict(t=1, type="highlight")]), set())


class TtcutReport(unittest.TestCase):
    def test_games_rows_and_markers(self):
        events = rallies("A" * 11 + "BA") + [dict(t=15, type="highlight"),
                                              dict(t=225, type="game"),
                                              dict(t=228, type="adjust", points={"A": 3}, server="B")]
        for lang, m in TT.items():
            txt = report(m, doc_of(events))
            self.assertIn("11" + "\u2013" + "0", txt)                # game 1 result 11–0
            self.assertRegex(txt, r"A 1 : 0 B")
            self.assertEqual(len(re.findall(r"^\s*\d+\s+0:", txt, re.M)), 13, lang)   # 13 point rows
            self.assertEqual(len(re.findall(r"^\s*\d+\s+0:.*★", txt, re.M)), 1, lang)   # one starred row
            self.assertIn("Ann", txt)
            self.assertIn("Bob", txt)
            self.assertIn("3", txt)                                      # adjust row shows points

    def test_doubles_server_numbers(self):
        events = rallies("AABBAA")
        for m in TT.values():
            txt = report(m, doc_of(events, side="doubles"))
            self.assertIn("A#1", txt)
            self.assertIn("B#1", txt)
            self.assertIn("A#2", txt)
            txt_s = report(m, doc_of(events))
            self.assertNotIn("#1", txt_s)

    def test_unfinished_game_listed(self):
        for m in TT.values():
            txt = report(m, doc_of(rallies("AAB")))
            self.assertIn("2" + "\u2013" + "1", txt)


class PicklecutReport(unittest.TestCase):
    def test_side_out_and_server_numbers(self):
        events = rallies("BAB")           # A#2 loses -> side-out; B#1 wins 1-0... etc.
        for lang, m in PC.items():
            txt = report(m, doc_of(events, scoring="sideout", side="doubles"))
            self.assertIn("A#2", txt)
            self.assertIn("B#1", txt)
            self.assertTrue(("換發" in txt) or ("side-out" in txt.lower()), lang)

    def test_rally_mode_no_side_out_marker(self):
        for m in PC.values():
            txt = report(m, doc_of(rallies("AB"), scoring="rally", side="singles"))
            self.assertNotIn("換發", txt)
            self.assertNotIn("side-out", txt.lower().split("\n", 6)[-1])   # only in the header line, if at all


class LanguageParity(unittest.TestCase):
    NUM = re.compile(r"\d+[\u2013:]\d+|0:\d\d:\d\d\.\d\d")

    def test_same_numbers(self):
        events = rallies("A" * 11 + "BBA") + [dict(t=15, type="highlight"),
                                               dict(t=240, type="adjust", games={"A": 2})]
        for pair, doc in ((TT, doc_of(events, side="doubles")),
                          (PC, doc_of(events, scoring="sideout", side="doubles"))):
            a, b = report(pair["zh"], doc), report(pair["en"], doc)
            self.assertEqual(self.NUM.findall(a), self.NUM.findall(b))
            self.assertEqual(a.count("★"), b.count("★"))


if __name__ == "__main__":
    unittest.main()
