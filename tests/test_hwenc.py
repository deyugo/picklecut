"""Hardware-encoder detection and encoder / hwaccel selection, all four builds
(ttcut zh / EN, picklecut zh / EN).

  - detect_hw_encoders(None) is empty and default_encoder(None) is the
    platform fallback (HW_ENCODER)
  - with a real ffmpeg: the detected list is a subset of the candidates,
    is cached, and default_encoder prefers it
  - build_render: default encoder follows detection, an explicit --encoder
    wins, --quality max forces libx264, --hwaccel qsv adds the output-format
    flag that keeps the CPU subtitles filter working
  - all four builds agree

Run from the repo root:  python -m unittest discover -s tests -v
"""

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(fname, modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(ROOT, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MODS = {
    "ttcut_zh": load("ttcut_v2_4.py", "hw_ttcut_zh"),
    "ttcut_en": load("ttcut_v2_4_EN.py", "hw_ttcut_en"),
    "pickle_zh": load("picklecut_v1_1.py", "hw_pickle_zh"),
    "pickle_en": load("picklecut_v1_1_EN.py", "hw_pickle_en"),
}
FFMPEG = shutil.which("ffmpeg")


class Detection(unittest.TestCase):
    def test_no_ffmpeg(self):
        for name, m in MODS.items():
            self.assertEqual(m.detect_hw_encoders(None), [], name)
            self.assertEqual(m.default_encoder(None), m.HW_ENCODER, name)

    def test_candidates_agree_across_builds(self):
        cands = {tuple(m.HW_CANDIDATES) for m in MODS.values()}
        self.assertEqual(len(cands), 1)
        for c in next(iter(cands)):
            self.assertTrue(c.startswith("h264_"), c)

    @unittest.skipUnless(FFMPEG, "ffmpeg not on PATH")
    def test_real_detection_subset_cached_and_preferred(self):
        results = set()
        for name, m in MODS.items():
            r = m.detect_hw_encoders(FFMPEG)
            self.assertTrue(set(r) <= set(m.HW_CANDIDATES), name)
            self.assertIs(m.detect_hw_encoders(FFMPEG), r, "not cached")
            self.assertEqual(m.default_encoder(FFMPEG), r[0] if r else m.HW_ENCODER, name)
            results.add(tuple(r))
        self.assertEqual(len(results), 1, "builds disagree on detected encoders")


@unittest.skipUnless(FFMPEG, "ffmpeg not on PATH")
class RenderCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="hwenc_")
        cls.video = os.path.join(cls.tmp, "clip.mp4")
        subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "testsrc2=size=128x72:rate=30",
                        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest", cls.video], check=True)
        probe = os.path.join(os.path.dirname(FFMPEG),
                             "ffprobe.exe" if os.name == "nt" else "ffprobe")
        cls.ffprobe = probe if os.path.isfile(probe) else "ffprobe"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def cmd(self, m, opt):
        events = [dict(t=0.2, type="serve"), dict(t=1.0, type="point", winner="A")]
        doc = dict(events=events, fps=30, players={"A": "A", "B": "B"},
                   firstServer="A", pads={"tail": 0.3, "lead": 0.1})
        pl = m.plan(doc, dict(opt, min_cut=2.0))
        self.assertTrue(pl["ok"], pl["reason"])
        cmd, workdir, _ = m.build_render(doc, pl, self.video,
                                         os.path.join(self.tmp, "out.mp4"),
                                         opt, FFMPEG, self.ffprobe, log=lambda *a: None)
        self.assertEqual(os.path.normcase(workdir), os.path.normcase(self.tmp))
        return cmd

    @staticmethod
    def after(cmd, flag):
        return cmd[cmd.index(flag) + 1] if flag in cmd else None

    def test_default_encoder_follows_detection(self):
        for name, m in MODS.items():
            cmd = self.cmd(m, dict(quality="high"))
            self.assertEqual(self.after(cmd, "-c:v"), m.default_encoder(FFMPEG), name)

    def test_explicit_encoder_wins_and_max_forces_cpu(self):
        for name, m in MODS.items():
            self.assertEqual(self.after(self.cmd(m, dict(quality="high", encoder="libx264")),
                                        "-c:v"), "libx264", name)
            self.assertEqual(self.after(self.cmd(m, dict(quality="max")), "-c:v"),
                             "libx264", name)

    def test_hwaccel_auto_and_qsv(self):
        for name, m in MODS.items():
            cmd = self.cmd(m, dict(quality="high"))
            if m.IS_MAC:
                self.assertEqual(self.after(cmd, "-hwaccel"), "videotoolbox", name)
            else:
                self.assertNotIn("-hwaccel", cmd, name)
            cmd = self.cmd(m, dict(quality="high", hwaccel="qsv"))
            self.assertEqual(self.after(cmd, "-hwaccel"), "qsv", name)
            self.assertEqual(self.after(cmd, "-hwaccel_output_format"), "nv12", name)
            cmd = self.cmd(m, dict(quality="high", hwaccel="d3d11va"))
            self.assertEqual(self.after(cmd, "-hwaccel"), "d3d11va", name)
            self.assertNotIn("-hwaccel_output_format", cmd, name)


if __name__ == "__main__":
    unittest.main()
