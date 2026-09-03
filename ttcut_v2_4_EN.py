#!/usr/bin/env python3
"""
ttcut V2 — table tennis match video: tag rallies, cut the ball-chasing, burn in a
persistent scoreboard. One tool, start to finish.

Copyright (c) 2026 MikaDD (Taiwan)
Released under the MIT Licence. See the LICENSE file for the full terms.

Written with the assistance of Anthropic Claude.
This tool calls ffmpeg as an external program; it neither contains nor
distributes ffmpeg itself. ffmpeg is licensed separately -- get it from
https://ffmpeg.org

Versioning
    small changes +0.1 (V1 -> V1.1 -> V1.2 ...)
    architectural or output-format changes bump the whole number (V2)

Changelog
    V2.4-EN 2026-09-02
        - Interface and output features ported back from picklecut V1.1;
          the table-tennis scoring rules are unchanged
        - Drag & drop: drop a video anywhere in the window and start tagging
          immediately (the frame rate is auto-estimated during 1x playback);
          the native dialog opens once at render time to confirm where the
          file lives, because browsers never reveal a dropped file's path.
          Dropping a .tags.json loads it as tags.
        - Arrow keys now step 1 second (Shift = 5 s, Alt = one frame), and
          they keep working right after using the scrub bar or speed buttons
          (focus no longer swallows them)
        - Captions: type a line, press the button (or Enter) and it is
          burned into the output bottom-centre at the current time for the
          chosen number of seconds; stored in the JSON as caption events and
          re-timed automatically across cuts
        - Multi-video matches: --join losslessly concatenates rendered parts
          (stream copy)
        - Timeline strip under the transport (LosslessCut-style): bright =
          kept, dark = cut, gold = highlighted rallies, ticks = serves,
          click to jump
        - Score correction ("fix" bar under the scoreboard): insert an
          adjust event at the current time that overrides only the filled-in
          fields (games / points / server); scoring continues from there and
          the serve rotation restarts when a server is given. Stored in the
          JSON as adjust events
        - Every event row gained a retime button that moves the tag to the
          current playback position - no delete-and-retag
        - Highlights: H marks the current rally; the render scope select
          outputs the full match, only the highlights, or both files in one
          go (CLI: --highlights)
        - The command line tolerates a Notepad BOM in the tags JSON
        - GPU: hardware encoders (NVENC / Quick Sync / AMF / VideoToolbox)
          are detected at startup by actually test-encoding a few frames;
          without --encoder the first working one is the default. The UI
          gains an "encoder" select (auto / each detected encoder / CPU).
          --quality max still forces CPU libx264
        - Fixed --hwaccel qsv crashing ffmpeg when combined with the
          subtitles filter (adds -hwaccel_output_format); --hwaccel now
          also accepts d3d11va / dxva2
        - Scoreboard shows the server: a serve-dot column right of the
          points; new "Doubles" mode marks which player of the pair is up
          (● / ●● = first / second; the serve passes to the other player
          each time a pair regains it, every game starts at #1; the
          receiver swap at 5 in the deciding game is entered via the fix
          bar's "#"). Tags JSON gains format.side; adjust events may
          carry serverNum
        - Score sheet: rendering writes <name>.score.txt next to the video
          (game results and a point log: time, game, server, winner, score,
          ★ highlight); "Export score" button in the UI; --dry-run prints it
    V2.3-EN 2026-09-01
        - New --listen flag: also accept connections from the local network,
          so other devices on the same Wi-Fi can open the UI (with a printed
          LAN URL and a security warning). Default stays 127.0.0.1 only.
        - Double-click launchers (ttcut_EN.bat / ttcut_EN.command) and
          PyInstaller build scripts added alongside, in the repo
    V2.2-EN 2026-08-30
        - English interface build of V2.2. Same scoring, cutting and rendering
          behaviour; only user-facing text and comments changed.
        - Default player names are now "Player A" / "Player B"
    V2.2 2026-08-30
        - Wider number fields: pad seconds (0.5, 1.0) and frame rate (29.97)
          used to get clipped
    V2.1 2026-08-30
        - Scoreboard accent colour is configurable: the point digits and the
          bar to the left of the names change together
        - The colour is stored in the tags JSON as scoreboard.accent, so it
          travels with the file across machines
        - New --accent flag on the command line, which wins over the JSON value
        - With no colour given, the generated .ass is byte-identical to V2;
          every other colour is untouched
    V2  2026-08-24
        - Merged into a single tool: run it and it starts a server, opens the
          browser, and one button turns your tags into a finished video
        - Scoring lives in Python only (/fold); the tagger's JS copy is gone
          -- rule changes now happen in one place, no JS/Python cross-checking
        - Serve-rotation logic moved out of JS into the same fold()
        - Fixed the mismatch between tagger and ttcut on the minimum cut length
          (0.15s shown, 2.0s actually cut). Both now use one value, adjustable
          in the interface
        - Video is served by Python with HTTP Range support, so scrubbing and
          Safari playback work
        - The video path comes from a native file dialog opened by Python
          (browsers never hand over the real path)
        - ffmpeg -progress drives a real progress bar; rendering runs in the
          background and does not block the UI
        - Unchanged: JSON export/import and the command-line render path both
          behave exactly as in V1.22
    V1.22 2026-08-20
        - Starting game count (for one video per game, continuing a match)
        - Starting score / handicap, applied every game or first game only
        - Capped mode: after 10:10 the first to 12 wins, no need to win by two
        - JSON gains format / start blocks; older files fall back to defaults
    V1.2 2026-08-20
        - Fixed a fatal bug: the V1.1 refactor dropped -c:v, so ffmpeg had been
          silently falling back to the default libx264
        - Added --hwaccel; videotoolbox hardware decoding is on by default on Mac
        - --hdr keep falls back automatically on non-HDR sources
        - libx264/libx265 switch to bitrate mode when --bitrate is given
    V1.1 2026-08-20
        - Scoreboard: game count became "filled chip + dark digits"
        - Quality: frame rate follows the source, bitrate derived from
          resolution x frame rate, three --quality tiers, HDR detection
    V1  2026-08-20  first working version

Usage:
    python3 ttcut_v2_4_EN.py                                    <- open the UI (the usual way)
    python3 ttcut_v2_4_EN.py IMG_1496.tags.json IMG_1496.MOV    <- render from the command line
    python3 ttcut_v2_4_EN.py tags.json video.MOV --quality max --dry-run
    python3 ttcut_v2_4_EN.py --join g1.cut.mp4 g2.cut.mp4 -o match.mp4

Requirements:
    Python 3.8+ and ffmpeg (not bundled, install it yourself)
    Mac    : brew install ffmpeg
             check with: ffmpeg -filters | grep subtitles
    Windows: drop ffmpeg.exe next to this script, or point --ffmpeg at its folder
"""

import argparse, json, mimetypes, os, platform, re, shutil, socket
import subprocess, sys, threading, time, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

VERSION = "V2.4-EN"

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# ─────────────────────────────────────────── Layout (authored at 1920x1080, scales automatically)

BASE_W, BASE_H = 1920, 1080
PAD_L, PAD_B   = 64, 64
PANEL_W        = 532          # one extra column right of the points: the serve dots
ROW_H          = 54
COL_GAMES_X    = 312          # left edge of the games column (relative to the panel)
COL_POINTS_X   = 392          # left edge of the points column
FS_NUM         = 44           # games and points share one type size
COL_SERVE_X    = 480          # left edge of the serve-dot column
FS_DOT         = 17           # serve dots (● / ●●)

C_PANEL    = "&H40250A&"      # deep blue panel (ASS is BGR)
C_ACCENT   = "&H187AFF&"      # orange #FF7A18
C_NAME     = "&HF9F2EA&"      # near white
C_GAMES_BG = "&HEDE3D6&"      # games chip: a light block against the dark panel
C_GAMES    = "&H40250A&"      # games digits: dark blue on the light chip
C_POINTS   = "&H187AFF&"      # points: orange digits on the dark panel
C_RULE     = "&H6E4820&"      # divider lines

A_PANEL, A_CHIP, A_RULE = 0x1E, 0x00, 0x40    # 0x00 fully opaque -> 0xFF fully transparent

DEFAULT_ACCENT = "#FF7A18"    # accent shared by the point digits and the bar beside the names


def ass_colour(hex_rgb, fallback=C_ACCENT):
    """Convert #RRGGBB to ASS &HBBGGRR&. ASS is BGR; get the order wrong and
    every colour comes out wrong."""
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", (hex_rgb or "").strip())
    if not m:
        return fallback
    s = m.group(1).upper()
    return f"&H{s[4:6]}{s[2:4]}{s[0:2]}&"

# Fonts that actually ship on each platform (CJK-capable, so Chinese names
# in the tags JSON still render correctly)
FONT_NAME = ("PingFang TC" if IS_MAC else
             "Microsoft JhengHei" if IS_WIN else "Noto Sans CJK TC")
FONT_NUM  = ("Helvetica Neue" if IS_MAC else
             "Segoe UI" if IS_WIN else "DejaVu Sans")

# Hardware encoder per platform
HW_ENCODER = "h264_videotoolbox" if IS_MAC else "libx264"
HW_CANDIDATES = (["h264_videotoolbox"] if IS_MAC else
                 ["h264_nvenc", "h264_qsv", "h264_amf"] if IS_WIN else
                 ["h264_nvenc", "h264_qsv"])
_HW_CACHE = {}


def detect_hw_encoders(ffmpeg):
    """Test-encode three frames with each candidate hardware encoder and return
    the ones that work. An encoder listed by ffmpeg -encoders does not mean the
    card is actually in this machine, so a real test encode is required.
    Cached per ffmpeg path; the UI's /state and the render share the result."""
    if not ffmpeg:
        return []
    if ffmpeg in _HW_CACHE:
        return _HW_CACHE[ffmpeg]
    ok = []
    for enc in HW_CANDIDATES:
        try:
            r = subprocess.run(
                [ffmpeg, "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", "color=size=64x64:rate=30",
                 "-frames:v", "3", "-c:v", enc, "-f", "null", "-"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            if r.returncode == 0:
                ok.append(enc)
        except Exception:
            pass
    _HW_CACHE[ffmpeg] = ok
    return ok


def default_encoder(ffmpeg):
    """Default when --encoder is not given: the first working hardware encoder,
    else HW_ENCODER (videotoolbox on Mac, CPU libx264 elsewhere)."""
    hw = detect_hw_encoders(ffmpeg)
    return hw[0] if hw else HW_ENCODER

# Three --quality tiers: bitrate multiplier / CRF / x264 preset / force software encoding
QUALITY = {
    "fast": dict(scale=0.70, crf=21, preset="veryfast", force_sw=False),
    "high": dict(scale=1.00, crf=18, preset="medium",   force_sw=False),
    "max":  dict(scale=1.40, crf=16, preset="slow",     force_sw=True),
}

DEFAULT_MIN_CUT = 2.0         # anything shorter than this is left alone, to avoid pointless jump cuts


# ─────────────────────────────────────────── Scoring (the single source of truth)

def fold_full(events, fmt, start, first_server=0):
    """Fold the event stream into scoreboard states. This is the only scoring
    implementation in the project; the UI and the CLI both go through it.

    fmt   = dict(target, deuce='standard'|'capped', cap, doubles=True|False)
    start = dict(games=(gA, gB), points=(a, b), scope='every'|'first')
    first_server = 0(A) / 1(B)

    Returns dict:
        states  [(source time, gA, gB, a, b, server, serverNum), ...]  for the
                ASS scoreboard; the first entry has time None. serverNum is
                the player of the pair who is up in doubles (1 or 2), always
                1 in singles
        snaps   same length as events; a dict for point events (including who
                served the point: served / servedNum, and its game: gameNo),
                None otherwise
        cur     current state, including who serves next and the server number

    Serve rotation counts only points actually played, so handicap starting
    points do not shift the rotation; once both sides reach target-1 (deuce)
    the serve changes every point.
    Doubles: each time a pair regains the serve the other player of that pair
    serves (A1 -> B1 -> A2 -> B2 ...); every game restarts at each pair's #1.
    The receiver swap at 5 in the deciding game is not automatic - insert an
    adjust event with "#" for it.

    An adjust event (the UI's "fix" bar) overrides only the fields it
    carries: games, points, server. Giving a server restarts the serve
    rotation; changing only the games (not the points) leaves a just-finished
    game waiting for the next point to reset as usual. caption / highlight
    events do not affect scoring.
    """
    T, mode, cap = fmt["target"], fmt["deuce"], fmt["cap"]
    doubles = bool(fmt.get("doubles", False))
    gA, gB = start["games"]
    sp, scope = list(start["points"]), start["scope"]

    def init_pts(gi):
        return list(sp) if (scope == "every" or gi == 0) else [0, 0]

    gi = 0
    a, b = init_pts(0)
    nxt = [1, 1]                           # doubles: each pair's next player to serve

    def take(side):
        # The player who is up when a pair takes the serve: the two alternate
        # in doubles, always 1 in singles
        if not doubles:
            return 1
        n = nxt[side]
        nxt[side] = 3 - n
        return n

    server, served_in_turn = first_server, 0
    snum = take(server)
    pending = False                        # end of game: keep the score on screen until the next point
    states = [(None, gA, gB, a, b, server, snum)]   # opening state; its timestamp is filled in later
    snaps = []

    def is_deuce():
        return a >= T - 1 and b >= T - 1

    def game_over():
        hi, lo = max(a, b), min(a, b)
        if mode == "capped" and hi >= cap:      # after 10:10 the first to cap wins, no win-by-two
            return True
        return hi >= T and hi - lo >= 2          # standard: 11 points and two clear

    for e in events:
        if e["type"] == "game":
            gi += 1
            a, b = init_pts(gi)
            server, served_in_turn = (first_server + gi) % 2, 0
            nxt[:] = [1, 1]
            snum = take(server)
            pending = False
            states.append((e["t"], gA, gB, a, b, server, snum))
            snaps.append(None)
            continue
        if e["type"] == "adjust":
            # Manual correction: override only the fields the event carries;
            # scoring continues from the corrected state
            g = e.get("games", {}) or {}
            p = e.get("points", {}) or {}
            gA, gB = int(g.get("A", gA)), int(g.get("B", gB))
            if p:
                a, b = int(p.get("A", a)), int(p.get("B", b))
                pending = False
            if e.get("server") in ("A", "B"):
                server, served_in_turn = (0 if e["server"] == "A" else 1), 0
                snum = take(server)
            if doubles and e.get("serverNum") in (1, 2):
                snum = e["serverNum"]
                nxt[server] = 3 - snum
            states.append((e["t"], gA, gB, a, b, server, snum))
            snaps.append(None)
            continue
        if e["type"] != "point":
            snaps.append(None)
            continue
        if pending:
            gi += 1
            a, b = init_pts(gi)
            pending = False
        served, served_num, game_no = server, snum, gA + gB + 1
        if e["winner"] == "A":
            a += 1
        else:
            b += 1
        won = game_over()
        snaps.append(dict(a=a, b=b, won=won,
                          served=served, servedNum=served_num, gameNo=game_no,
                          gA=gA + (1 if won and a > b else 0),
                          gB=gB + (1 if won and b > a else 0)))
        if won:
            if a > b:
                gA += 1
            else:
                gB += 1
            pending = True
            server, served_in_turn = (first_server + gi + 1) % 2, 0   # other side serves first next game
            nxt[:] = [1, 1]
            snum = take(server)
        else:
            served_in_turn += 1
            if served_in_turn >= (1 if is_deuce() else 2):
                server, served_in_turn = 1 - server, 0
                snum = take(server)
        states.append((e["t"], gA, gB, a, b, server, snum))

    cur = dict(a=a, b=b, gA=gA, gB=gB, gi=gi, server=server, serverNum=snum,
               pending=pending, gameNo=gA + gB + 1 - (1 if pending else 0))
    return dict(states=states, snaps=snaps, cur=cur)


def fold(events, fmt, start):
    """State sequence for the ASS scoreboard (identical output to V1.22 fold())."""
    return fold_full(events, fmt, start)["states"]


def read_format(doc):
    """Read match format and starting score from JSON; older files without
    these fields fall back to defaults."""
    f = doc.get("format", {}) or {}
    target = int(f.get("pointsPerGame", doc.get("pointsPerGame", 11)))
    mode = f.get("deuce", "standard")
    cap = int(f.get("cap", target + 1))
    st = doc.get("start", {}) or {}
    g = st.get("games", {}) or {}
    p = st.get("points", {}) or {}
    fmt = dict(target=target, deuce=mode, cap=cap,
               doubles=f.get("side", "singles") == "doubles")
    start = dict(games=[int(g.get("A", 0)), int(g.get("B", 0))],
                 points=[int(p.get("A", 0)), int(p.get("B", 0))],
                 scope=st.get("handicapScope", "every"))
    return fmt, start


# ─────────────────────────────────────────── Cut ranges

def build_cuts(events, tail, lead, min_cut, cut_lets, let_tail):
    """point -> next serve = cut. serve -> serve (a let) = kept by default,
    optionally cut as well."""
    cuts = []
    for i, e in enumerate(events):
        if e["type"] == "point":
            nxt = next((x for x in events[i + 1:] if x["type"] == "serve"), None)
            if nxt:
                cuts.append((e["t"] + tail, nxt["t"] - lead, "ball retrieval after point"))
        elif e["type"] == "serve" and cut_lets:
            nxt = events[i + 1] if i + 1 < len(events) else None
            if nxt and nxt["type"] == "serve":
                cuts.append((e["t"] + let_tail, nxt["t"] - lead, "ball retrieval after let"))

    kept, dropped = [], []
    for f, t, why in cuts:
        (kept if t - f >= min_cut else dropped).append((f, t, why))
    return sorted(kept), sorted(dropped)


def highlight_ranges(events, lead, tail):
    """Source-time ranges of the rallies marked with a highlight event.
    A highlight belongs to the rally started by the most recent serve at or
    before it, so pressing H during the rally or right after it ends both
    land on the same rally. Overlapping ranges are merged."""
    serves = [e for e in events if e["type"] == "serve"]
    rngs = []
    for h in (e for e in events if e["type"] == "highlight"):
        sv = None
        for s in serves:
            if s["t"] <= h["t"]:
                sv = s
            else:
                break
        if sv is None:
            continue
        pt = next((x for x in events
                   if x["type"] == "point" and x["t"] >= sv["t"]), None)
        if pt is None:
            continue
        rngs.append((max(0.0, sv["t"] - lead), pt["t"] + tail))
    rngs.sort()
    merged = []
    for s, e2 in rngs:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e2))
        else:
            merged.append((s, e2))
    return merged


def keeps_from_cuts(head, end, cuts):
    """The complement of the cuts is what we keep."""
    segs, cur = [], head
    for f, t, _ in cuts:
        if f > cur:
            segs.append((cur, min(f, end)))
        cur = max(cur, t)
        if cur >= end:
            break
    if cur < end:
        segs.append((cur, end))
    return [(s, e) for s, e in segs if e - s > 0.04]


def make_mapper(keeps):
    """Source time -> output time. Times inside a cut snap to the start of
    the next kept segment."""
    acc, table = 0.0, []
    for s, e in keeps:
        table.append((s, e, acc))
        acc += e - s
    total = acc

    def src2out(t):
        for s, e, base in table:
            if t < s:
                return base
            if t <= e:
                return base + (t - s)
        return total

    return src2out, total


# ─────────────────────────────────────────── ASS scoreboard

def ts(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def rect(x, y, w, h, colour, alpha, layer=0):
    """Filled rectangle. \\alpha must come before \\1a, otherwise it overrides it."""
    tags = (f"\\an7\\pos({x},{y})\\p1\\bord0\\shad0"
            f"\\alpha&H00&\\1c{colour}\\1a&H{alpha:02X}&")
    return layer, f"{{{tags}}}m 0 0 l {w} 0 l {w} {h} l 0 {h}"


def build_ass(states, src2out, total, names, width, height,
              font_name=FONT_NAME, font_num=FONT_NUM, accent=None,
              captions=()):
    # The point digits and the bar beside the names share one colour
    c_accent = c_points = accent or C_ACCENT
    k = min(width / BASE_W, height / BASE_H)
    S = lambda v: round(v * k)                        # scale
    x0 = S(PAD_L)
    y0 = height - S(PAD_B) - S(ROW_H * 2)
    pw, rh = S(PANEL_W), S(ROW_H)
    row_y = (y0 + rh // 2, y0 + rh + rh // 2)
    name_x = x0 + S(28)
    gx, gw = x0 + S(COL_GAMES_X), S(COL_POINTS_X) - S(COL_GAMES_X)
    games_cx = gx + gw // 2
    points_cx = x0 + S(COL_POINTS_X) + (S(COL_SERVE_X) - S(COL_POINTS_X)) // 2
    serve_cx = x0 + S(COL_SERVE_X) + (pw - S(COL_SERVE_X)) // 2
    fs = S(FS_NUM)
    fs_dot = S(FS_DOT)

    head = f"""[Script Info]
; ttcut {VERSION}
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Nm,{font_name},{S(29)},{C_NAME},{C_NAME},&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
Style: Nu,{font_num},{fs},{c_points},{c_points},&H00000000&,&H00000000&,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Gfx,Arial,20,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Cap,{font_name},{S(34)},{C_NAME},{C_NAME},&H00000000&,&H96000000&,0,0,0,0,100,100,0,0,1,{max(1, S(2))},{max(1, S(1))},2,0,0,{S(46)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []
    add = lambda layer, style, a, b, txt: lines.append(
        f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{txt}")

    # ── Panel, games chips, accent bar, dividers (on screen for the whole film)
    # Within one layer things stack in the order written, so the dividers come
    # last in order to sit on top of the chips
    for layer, d in [
        rect(x0, y0, pw, rh * 2, C_PANEL, A_PANEL),                    # panel
        rect(gx, y0, gw, rh, C_GAMES_BG, A_CHIP),                      # games chip (top)
        rect(gx, y0 + rh, gw, rh, C_GAMES_BG, A_CHIP),                 # games chip (bottom)
        rect(x0, y0, S(5), rh * 2, c_accent, 0x00),                    # accent bar
        rect(x0, y0 + rh, pw, max(1, S(2)), C_RULE, A_RULE),           # horizontal divider
        rect(gx, y0, max(1, S(2)), rh * 2, C_RULE, A_RULE),
        rect(x0 + S(COL_POINTS_X), y0, max(1, S(2)), rh * 2, C_RULE, A_RULE),
        rect(x0 + S(COL_SERVE_X), y0, max(1, S(2)), rh * 2, C_RULE, A_RULE),
    ]:
        add(layer, "Gfx", 0, total, d)

    # ── Player names (always on screen)
    for i, nm in enumerate(names):
        add(1, "Nm", 0, total,
            f"{{\\an4\\pos({name_x},{row_y[i]})\\1c{C_NAME}}}{nm}")

    # ── Games and points (change with events): same size and weight, told
    # apart by the background behind them
    stamped = [(0.0, *states[0][1:])] if states[0][0] is None else []
    stamped += [(src2out(t), *rest) for t, *rest in states if t is not None]

    for i, (t, gA, gB, a, b, srv, snum) in enumerate(stamped):
        end = stamped[i + 1][0] if i + 1 < len(stamped) else total
        if end - t < 0.02:
            continue
        for row, (g, p) in enumerate(((gA, a), (gB, b))):
            add(2, "Nu", t, end,
                f"{{\\an5\\pos({games_cx},{row_y[row]})\\fs{fs}\\b1\\1c{C_GAMES}}}{g}")
            add(2, "Nu", t, end,
                f"{{\\an5\\pos({points_cx},{row_y[row]})\\fs{fs}\\b1\\1c{c_points}}}{p}")
        if srv is not None:          # serving side gets one accent dot, the second player of a pair two
            add(2, "Nu", t, end,
                f"{{\\an5\\pos({serve_cx},{row_y[srv]})\\fs{fs_dot}\\b0\\1c{c_accent}}}"
                + "●" * max(1, snum or 1))

    # ── Captions (burned bottom-centre, re-timed across the cuts)
    for ct, cdur, ctext in captions:
        a2, b2 = src2out(ct), src2out(ct + max(0.5, cdur))
        if b2 - a2 < 0.02:
            continue                      # the caption fell entirely inside a cut
        safe = str(ctext).replace("{", "(").replace("}", ")").replace("\n", r"\N")
        add(3, "Cap", a2, min(b2, total), safe)

    return head + "\n".join(lines) + "\n"


# ─────────────────────────────────────────── ffmpeg

def find_ffmpeg(explicit, *hint_dirs):
    """Look for ffmpeg in order: explicit path -> PATH -> next to the script
    or the video -> common Windows install locations."""
    exe = "ffmpeg.exe" if IS_WIN else "ffmpeg"
    if explicit:
        p = os.path.abspath(explicit)
        if os.path.isdir(p):
            p = os.path.join(p, exe)
        return p if os.path.isfile(p) else None
    found = shutil.which("ffmpeg")
    if found:
        return found
    cands = [os.path.dirname(os.path.abspath(__file__)), *hint_dirs]
    if IS_WIN:
        cands += [r"C:\ffmpeg\bin", r"C:\Program Files\ffmpeg\bin",
                  os.path.expanduser(r"~\ffmpeg\bin"),
                  os.path.expanduser(r"~\scoop\shims")]
    for d in cands:
        if not d:
            continue
        p = os.path.join(d, exe)
        if os.path.isfile(p):
            return p
    return None


def probe(path, ff="ffprobe"):
    """Return a dict of source specs, or None if it cannot be read."""
    try:
        out = subprocess.run(
            [ff, "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,avg_frame_rate,r_frame_rate,pix_fmt,codec_name,"
             "color_transfer,color_primaries,bit_rate:format=bit_rate,duration",
             "-of", "json", path],
            capture_output=True, text=True, check=True).stdout
        d = json.loads(out)
        s = d["streams"][0]

        def rate(x):
            try:
                n, den = str(x).split("/")
                return float(n) / float(den) if float(den) else 0.0
            except Exception:
                return 0.0

        frac = s.get("avg_frame_rate") or "0/0"
        if rate(frac) <= 0:
            frac = s.get("r_frame_rate") or "0/0"
        br = s.get("bit_rate") or d.get("format", {}).get("bit_rate")
        dur = d.get("format", {}).get("duration")
        return {
            "w": int(s["width"]), "h": int(s["height"]),
            "fps": rate(frac), "fps_frac": frac if rate(frac) > 0 else None,
            "pix_fmt": s.get("pix_fmt", ""), "codec": s.get("codec_name", ""),
            "trc": s.get("color_transfer", ""), "prim": s.get("color_primaries", ""),
            "bitrate": int(br) if br and str(br).isdigit() else None,
            "duration": float(dur) if dur else None,
        }
    except Exception:
        return None


def is_hdr(info):
    return bool(info) and info.get("trc") in ("arib-std-b67", "smpte2084")


def is_10bit(info):
    pf = (info or {}).get("pix_fmt", "")
    return "10" in pf or "p010" in pf or "12" in pf


def auto_bitrate(w, h, fps, scale=1.0):
    """Derive a bitrate from the pixel rate. Table tennis is high-motion, so
    this runs more generous than a general-purpose figure."""
    mpix_s = w * h * max(fps, 1) / 1e6          # 1080p30 ≈ 62 Mpix/s
    mbps = mpix_s * 0.30 * scale                # -> about 19 Mbps
    return f"{max(8.0, min(120.0, mbps)):.0f}M"


def video_encoder_args(enc, crf, preset, bitrate, pix_fmt, use_bitrate=False):
    """Every encoder spells its quality knobs differently; this translates them.
    The first pair must always be -c:v -- V1.1 dropped it and ffmpeg silently
    fell back to the default libx264."""
    c = ["-c:v", enc]
    if enc in ("libx264", "libx265"):
        q = (["-b:v", bitrate, "-maxrate", bitrate,
              "-bufsize", f"{float(bitrate[:-1]) * 2:.0f}M"] if use_bitrate
             else ["-crf", str(crf)])
        return c + ["-preset", preset, *q, "-pix_fmt", pix_fmt]
    if "videotoolbox" in enc:      # VideoToolbox has no CRF, bitrate only
        return c + ["-b:v", bitrate, "-maxrate", bitrate,
                    "-bufsize", f"{float(bitrate[:-1]) * 2:.0f}M", "-pix_fmt", pix_fmt]
    if "nvenc" in enc:
        return c + ["-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", str(crf),
                    "-b:v", "0", "-maxrate", bitrate, "-pix_fmt", pix_fmt]
    if "qsv" in enc:
        return c + ["-preset", "veryslow", "-global_quality", str(crf), "-pix_fmt", pix_fmt]
    if "amf" in enc:
        return c + ["-quality", "quality", "-rc", "cqp",
                    "-qp_i", str(crf), "-qp_p", str(crf), "-pix_fmt", pix_fmt]
    return c + ["-b:v", bitrate, "-pix_fmt", pix_fmt]


TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def filter_script(keeps, ass_name, fps, tonemap=False):
    """Filter the stream with select rather than trim+concat -- the latter
    buffers whole decoded segments in memory.
    fps first, to force a constant frame rate, otherwise iPhone VFR drifts audio
    out of sync.
    tone-map before subtitles, so the scoreboard colours are not dragged through
    the dynamic-range compression."""
    expr = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in keeps)
    esc = ass_name.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    v = [f"[0:v]fps={fps}", f"select='{expr}'", "setpts=N/FRAME_RATE/TB"]
    if tonemap:
        v.append(TONEMAP)
    return "".join([
        ",".join(v) + "[vc];",
        f"[0:a]aselect='{expr}',asetpts=N/SR/TB[ac];",
        f"[vc]subtitles='{esc}'[vout]",
    ])


def human_bitrate(b):
    return f"{b / 1e6:.1f} Mbps" if b else "unknown"


# ─────────────────────────────────────────── Planning (shared by UI and CLI)

class PlanError(Exception):
    pass


def plan(doc, opt):
    """Work out the cut plan from the tags JSON. Touches no ffmpeg, so the UI
    uses it for live preview too."""
    events = sorted(doc.get("events", []), key=lambda e: e["t"])
    pads = doc.get("pads", {}) or {}
    lead = opt.get("lead") if opt.get("lead") is not None else pads.get("lead", 1.4)
    tail = opt.get("tail") if opt.get("tail") is not None else pads.get("tail", 1.0)
    min_cut = opt.get("min_cut", DEFAULT_MIN_CUT)
    cut_lets = bool(opt.get("cut_lets", False))
    let_tail = opt.get("let_tail", 1.5)
    fmt, start = read_format(doc)
    first_server = 1 if doc.get("firstServer") == "B" else 0

    sc = fold_full(events, fmt, start, first_server)

    serves = [e for e in events if e["type"] == "serve"]
    points = [e for e in events if e["type"] == "point"]
    hl = highlight_ranges(events, lead, tail)
    if not serves or not points:
        return dict(ok=False, reason="No serve or point events, nothing to cut.",
                    scoring=sc, events=events, fmt=fmt, start=start,
                    cuts=[], dropped=[], keeps=[], hl=hl, total=0.0, span=0.0)

    if opt.get("scope") == "highlights":
        if not hl:
            return dict(ok=False,
                        reason="No highlight marks yet — press H during (or right after) a rally.",
                        scoring=sc, events=events, fmt=fmt, start=start,
                        cuts=[], dropped=[], keeps=[], hl=hl, total=0.0, span=0.0)
        keeps = list(hl)
        head, end = keeps[0][0], keeps[-1][1]
        src2out, total = make_mapper(keeps)
        return dict(ok=True, reason=None, scoring=sc, events=events,
                    fmt=fmt, start=start, lead=lead, tail=tail,
                    cuts=[], dropped=[], keeps=keeps, hl=hl,
                    src2out=src2out, total=total,
                    head=head, end=end, span=end - head,
                    serves=len(serves), points=len(points))

    head = serves[0]["t"] - lead
    end = points[-1]["t"] + tail
    # Only serve / point / game events shape the cuts; captions, highlights
    # and score corrections must not sit between two serves when the
    # let-adjacency check runs
    cut_events = [e for e in events if e.get("type") in ("serve", "point", "game")]
    cuts, dropped = build_cuts(cut_events, tail, lead, min_cut, cut_lets, let_tail)
    keeps = keeps_from_cuts(head, end, cuts)
    src2out, total = make_mapper(keeps)

    return dict(ok=True, reason=None, scoring=sc, events=events,
                fmt=fmt, start=start, lead=lead, tail=tail,
                cuts=cuts, dropped=dropped, keeps=keeps, hl=hl,
                src2out=src2out, total=total,
                head=head, end=end, span=end - head,
                serves=len(serves), points=len(points))


def build_render(doc, plan_d, video, out, opt, ffmpeg, ffprobe, log=print,
                 progress=False):
    """Write the .ass and the filter graph, assemble the ffmpeg command.
    Returns (cmd, workdir, info)."""
    q = QUALITY[opt.get("quality", "high")]
    crf = opt.get("crf") if opt.get("crf") is not None else q["crf"]
    preset = opt.get("preset") or q["preset"]
    stem = os.path.splitext(out)[0]
    names = [doc.get("players", {}).get("A", "A"), doc.get("players", {}).get("B", "B")]

    info = probe(video, ffprobe)
    if opt.get("size"):
        w, h = (int(x) for x in str(opt["size"]).lower().split("x"))
    elif info:
        w, h = info["w"], info["h"]
    else:
        w, h = BASE_W, BASE_H
        log("! Could not read the video resolution; laying out the scoreboard for 1920x1080.")

    # ── Frame rate: follows the source by default. Fast table tennis motion
    # should not be casually dropped to 30.
    fps_opt = opt.get("fps", "source")
    if fps_opt and fps_opt != "source":
        fps_val, fps_arg = float(fps_opt), str(fps_opt)
    elif info and info["fps_frac"]:
        fps_val, fps_arg = info["fps"], info["fps_frac"]
    else:
        fps_val, fps_arg = float(doc.get("fps", 30)), str(doc.get("fps", 30))

    # ── Encoder and HDR
    enc = opt.get("encoder") or ("libx264" if q["force_sw"] else default_encoder(ffmpeg))
    hdr = is_hdr(info)
    mode = opt.get("hdr", "auto")
    if mode == "auto":
        mode = "keep" if (hdr and "hevc" in enc) else ("tonemap" if hdr else "ignore")
    if mode == "keep" and not hdr:
        log("! Source is not HDR, so --hdr keep means nothing; ignored.")
        mode = "ignore"
    if mode == "keep" and "hevc" not in enc:
        log("! --hdr keep needs an HEVC encoder; falling back to tone-map.")
        mode = "tonemap"
    tonemap = mode == "tonemap" and hdr
    pix_fmt = "p010le" if mode == "keep" else "yuv420p"

    bitrate = opt.get("bitrate") or auto_bitrate(w, h, fps_val, q["scale"])
    sw_bitrate = bool(opt.get("bitrate")) and enc in ("libx264", "libx265")

    hw = opt.get("hwaccel", "auto")
    if hw == "auto":
        hw = "videotoolbox" if IS_MAC else "none"

    # ── Quality readout: tells you at a glance whether the source or the
    # transcode is the bottleneck
    if info:
        depth = "10-bit" if is_10bit(info) else "8-bit"
        hdr_tag = f" · {info['trc']} HDR" if hdr else ""
        log(f"Source    {info['w']}x{info['h']} · {info['fps']:.2f} fps · "
            f"{info['codec']} · {depth}{hdr_tag} · {human_bitrate(info['bitrate'])}")
    log(f"Output    {w}x{h} · {fps_val:.2f} fps · {enc} · {pix_fmt}"
        f"{' · tone-mapped to SDR' if tonemap else ''}")
    log(f"Quality   {opt.get('quality', 'high')} · "
        + ("CRF " + str(crf) + f" · preset {preset}"
           if enc in ("libx264", "libx265") and not sw_bitrate
           else "target bitrate " + bitrate)
        + (f" · hw decode {hw}" if hw != "none" else ""))
    if info and info["bitrate"]:
        src_mbps = info["bitrate"] / 1e6
        if enc not in ("libx264", "libx265") or sw_bitrate:
            tgt = float(bitrate.rstrip("M"))
            if tgt < src_mbps * 0.8:
                log(f"! Target bitrate is below the source ({tgt:.0f}M < {src_mbps:.0f}M); "
                    f"to preserve quality try --bitrate {src_mbps * 1.2:.0f}M or quality max")
        if src_mbps < 12 and w * h >= 1920 * 1080:
            log(f"! Source is only {src_mbps:.0f} Mbps, so quality is capped by the recording itself.")

    # ffmpeg runs inside the output folder and the filter only sees a bare
    # filename, so a Windows C:\ drive letter needs no escaping
    workdir = os.path.dirname(os.path.abspath(out)) or "."
    ass_name = os.path.basename(stem) + ".ass"
    flt_name = os.path.basename(stem) + ".filter.txt"

    # Accent: --accent wins, then the tags JSON, then the default orange
    accent_hex = (opt.get("accent")
                  or (doc.get("scoreboard", {}) or {}).get("accent")
                  or DEFAULT_ACCENT)

    captions = [(e["t"], float(e.get("dur", 3.0)), e.get("text", ""))
                for e in plan_d["events"]
                if e.get("type") == "caption" and str(e.get("text", "")).strip()]

    with open(os.path.join(workdir, ass_name), "w", encoding="utf-8") as f:
        f.write(build_ass(plan_d["scoring"]["states"], plan_d["src2out"],
                          plan_d["total"], names, w, h,
                          opt.get("font") or FONT_NAME, FONT_NUM,
                          ass_colour(accent_hex), captions))
    fgraph = filter_script(plan_d["keeps"], ass_name, fps_arg, tonemap)
    with open(os.path.join(workdir, flt_name), "w", encoding="utf-8") as f:
        f.write(fgraph)          # kept purely for debugging

    colour_tags = (["-color_primaries", "bt2020", "-color_trc", info["trc"],
                    "-colorspace", "bt2020nc"] if mode == "keep" else
                   ["-color_primaries", "bt709", "-color_trc", "bt709",
                    "-colorspace", "bt709"])
    tag = ["-tag:v", "hvc1"] if "hevc" in enc else []

    # Read only as far as the last kept segment, otherwise ffmpeg decodes the whole file
    cmd = [ffmpeg, "-y",
           *(["-progress", "pipe:1", "-nostats"] if progress else []),
           *(["-hwaccel", hw] if hw != "none" else []),
           *(["-hwaccel_output_format", "p010le" if is_10bit(info) else "nv12"]
             if hw == "qsv" else []),
           "-to", f"{plan_d['keeps'][-1][1] + 1:.3f}", "-i", os.path.abspath(video),
           "-filter_complex", fgraph,
           "-map", "[vout]", "-map", "[ac]",
           *video_encoder_args(enc, crf, preset, bitrate, pix_fmt, sw_bitrate),
           *colour_tags, *tag,
           "-c:a", "aac", "-b:a", "256k",
           "-metadata", f"comment=ttcut {VERSION}",
           "-movflags", "+faststart", os.path.basename(out)]
    return cmd, workdir, flt_name


def summary_lines(plan_d, opt, video):
    """Summary text shared by the CLI and the UI."""
    fmt, start = plan_d["fmt"], plan_d["start"]
    out = [f"Source    {os.path.basename(video)}",
           f"Tagged    {ts(plan_d['head'])} -> {ts(plan_d['end'])}   {plan_d['span']:.1f}s"]
    rule = ("standard deuce (win by 2)" if fmt["deuce"] == "standard"
            else f"capped (after 10:10, first to {fmt['cap']} wins)")
    bits = ["doubles" if fmt.get("doubles") else "singles", f"{fmt['target']} points per game", rule]
    if any(start["games"]):
        bits.append(f"starting games {start['games'][0]}:{start['games'][1]}")
    if any(start["points"]):
        sc = "every game" if start["scope"] == "every" else "first game only"
        bits.append(f"handicap {start['points'][0]}:{start['points'][1]} ({sc})")
    out.append(f"Format    {' · '.join(bits)}")
    sc = plan_d["scoring"]
    finals = [f"{s['a']}–{s['b']}" for s in sc["snaps"] if s and s["won"]]
    out.append(f"Games     A {sc['cur']['gA']} : {sc['cur']['gB']} B"
               + (f" ({', '.join(finals)})" if finals else ""))
    out.append(f"Events    {plan_d['points']} points · {plan_d['serves']} serves · "
               f"{plan_d['serves'] - plan_d['points']} lets")
    out.append(f"Padding   {plan_d['tail']}s after point · {plan_d['lead']}s before serve · "
               f"min cut {opt.get('min_cut', DEFAULT_MIN_CUT)}s"
               f"{' · lets cut too' if opt.get('cut_lets') else ''}")
    span, total = plan_d["span"], plan_d["total"]
    out.append(f"Removed   {len(plan_d['cuts'])} segments · {span - total:.1f}s")
    out.append(f"Result    {total:.1f}s   {(span - total) / span * 100:.0f}% shorter"
               if span > 0 else "Result    0s")
    return out


def doc_names(doc):
    p = doc.get("players", {}) or {}
    return [str(p.get("A", "A")), str(p.get("B", "B"))]


def rally_highlights(events):
    """Rallies marked by a highlight event: the set of indices (into events)
    of their point events. Same attribution rule as highlight_ranges (the
    rally started by the last serve before the highlight)."""
    marked = set()
    serves = [i for i, e in enumerate(events) if e["type"] == "serve"]
    for h in (e for e in events if e["type"] == "highlight"):
        sv = None
        for i in serves:
            if events[i]["t"] <= h["t"]:
                sv = i
            else:
                break
        if sv is None:
            continue
        pt = next((i for i in range(sv, len(events)) if events[i]["type"] == "point"), None)
        if pt is not None:
            marked.add(pt)
    return marked


def score_report(plan_d, names, video):
    """Score sheet (plain text): game results and a point-by-point log.
    Written next to the rendered video; the UI's "Export score" button and
    --dry-run use it too."""
    fmt, start, sc = plan_d["fmt"], plan_d["start"], plan_d["scoring"]
    events, snaps, cur = plan_d["events"], sc["snaps"], sc["cur"]
    doubles = bool(fmt.get("doubles"))
    marked = rally_highlights(events)

    def who(side, num):
        return "AB"[side] + (f"#{num}" if doubles and num else "")

    rule = "win by 2" if fmt["deuce"] == "standard" else f"capped at {fmt['cap']}"
    out = [f"ttcut {VERSION} score sheet",
           f"Source    {os.path.basename(video) if video else '—'}",
           f"A         {names[0]}",
           f"B         {names[1]}",
           f"Format    {'doubles' if doubles else 'singles'} · game to {fmt['target']} · {rule}"]
    if any(start["games"]) or any(start["points"]):
        out.append(f"Start     games {start['games'][0]}:{start['games'][1]} · "
                   f"points {start['points'][0]}:{start['points'][1]}")

    games, rows, n = [], [], 0
    for i, e in enumerate(events):
        s = snaps[i] if i < len(snaps) else None
        if e["type"] == "point" and s:
            n += 1
            if s["won"]:
                games.append((s["gameNo"], s["a"], s["b"]))
            rows.append((str(n), ts(e["t"]), str(s["gameNo"]),
                         who(s["served"], s.get("servedNum")), e["winner"],
                         f"{s['a']}–{s['b']}",
                         f"games {s['gA']}–{s['gB']}" if s["won"] else "",
                         "★" if i in marked else ""))
        elif e["type"] == "game":
            rows.append(("", ts(e["t"]), "", "", "", "New game", "", ""))
        elif e["type"] == "adjust":
            bits = []
            if e.get("games"):
                bits.append("games " + "–".join(str(e["games"].get(k, "·")) for k in "AB"))
            if e.get("points"):
                bits.append("points " + "–".join(str(e["points"].get(k, "·")) for k in "AB"))
            if e.get("server") or e.get("serverNum"):
                bits.append("serve " + str(e.get("server") or "")
                            + (f"#{e['serverNum']}" if e.get("serverNum") else ""))
            rows.append(("", ts(e["t"]), "", "", "", "Adjust " + " · ".join(bits), "", ""))

    out += ["", f"Games     A {cur['gA']} : {cur['gB']} B"]
    for g, a, b in games:
        out.append(f"  Game {g}    {a}–{b}")
    if not cur["pending"] and (cur["a"] or cur["b"]):
        out.append(f"  Game {cur['gameNo']}    {cur['a']}–{cur['b']} (in progress)")

    out += ["", "Point log (times are source-video times; ★ = highlight"
            + ("; Serve column #1/#2 = first / second player of the pair" if doubles else "") + ")",
            "   #  Time         G  Serve  Won  Score"]
    for r in rows:
        out.append(f"{r[0]:>4}  {r[1]:<10}  {r[2]:>2}  {r[3]:<5} {r[4]:<3}  "
                   f"{r[5]:<8} {r[6]:<8} {r[7]}".rstrip())
    return out


# ─────────────────────────────────────────── Native file dialog

_MAC_PICK = ('POSIX path of (choose file with prompt "Choose match video"'
             ' of type {"public.movie","public.video"})')

_TK_PICK = (
    "import sys,tkinter,tkinter.filedialog as fd\n"
    "r=tkinter.Tk();r.withdraw();r.attributes('-topmost',True)\n"
    "p=fd.askopenfilename(title='Choose match video',filetypes=["
    "('Video','*.mp4 *.mov *.MOV *.MP4 *.m4v *.avi *.mkv'),('All files','*.*')])\n"
    "sys.stdout.write(p or '')\n")


def native_pick_video():
    """Open the OS file dialog and return an absolute path, or None if the user
    cancels. A browser <input type=file> never exposes the real path, and ffmpeg
    needs one, hence this detour."""
    try:
        if IS_MAC:
            r = subprocess.run(["osascript", "-e", _MAC_PICK],
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                return None                      # user cancelled
            p = r.stdout.strip()
        else:
            r = subprocess.run([sys.executable, "-c", _TK_PICK],
                               capture_output=True, text=True, timeout=300)
            p = r.stdout.strip()
        return p if p and os.path.isfile(p) else None
    except Exception:
        return None


# ─────────────────────────────────────────── Server state

STATE = {
    "video": None,          # absolute path of the loaded video
    "ffmpeg": None,
    "ffprobe": "ffprobe",
    "job": None,            # render in progress
}
STATE_LOCK = threading.Lock()


class Job:
    def __init__(self, out, total):
        self.out = out
        self.total = max(total, 0.001)
        self.pct = 0.0
        self.state = "running"      # running / done / error / cancelled
        self.message = "Preparing…"
        self.log = []
        self.proc = None
        self.started = time.time()
        self.speed = ""

    def snapshot(self):
        el = time.time() - self.started
        eta = None
        if self.state == "running" and self.pct > 2:
            eta = el * (100 - self.pct) / self.pct
        return dict(state=self.state, pct=round(self.pct, 1),
                    message=self.message, out=self.out,
                    elapsed=round(el), eta=round(eta) if eta else None,
                    speed=self.speed, log=self.log[-12:])


_TIME_RE = re.compile(r"out_time=(\d+):(\d\d):(\d\d(?:\.\d+)?)")


def run_job(job, tasks):
    """Run one or more ffmpeg commands in sequence (e.g. the full match and
    the highlight reel), parsing -progress into one combined percentage.
    tasks = [(cmd, workdir, output_seconds), ...]. Runs on a background thread."""
    grand = sum(t[2] for t in tasks) or 0.001
    done_secs = 0.0
    for ti, (cmd, workdir, secs) in enumerate(tasks):
        try:
            job.proc = subprocess.Popen(
                cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", bufsize=1)
        except Exception as ex:
            job.state, job.message = "error", f"Could not start ffmpeg: {ex}"
            return

        err_tail = []

        def drain_err():
            for line in job.proc.stderr:
                line = line.rstrip()
                if line:
                    err_tail.append(line)
                    del err_tail[:-40]
        t = threading.Thread(target=drain_err, daemon=True)
        t.start()

        job.message = ("Encoding…" if len(tasks) == 1
                       else f"Encoding {ti + 1}/{len(tasks)}…")
        for line in job.proc.stdout:
            line = line.strip()
            m = _TIME_RE.search(line)
            if m:
                cur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                job.pct = min(99.5, (done_secs + min(cur, secs)) / grand * 100)
            elif line.startswith("speed="):
                job.speed = line.split("=", 1)[1].strip()

        job.proc.wait()
        t.join(timeout=2)

        if job.state == "cancelled":
            job.message = "Cancelled"
            return
        if job.proc.returncode != 0:
            job.state = "error"
            job.message = f"ffmpeg exited with code {job.proc.returncode}"
            job.log = err_tail[-12:]
            return
        done_secs += secs

    job.state, job.pct, job.message = "done", 100.0, "Done"


# ─────────────────────────────────────────── Embedded interface

HTML = r"""<meta charset="utf-8">
<title>ttcut __VERSION__ — table tennis rally tagging &amp; cutting</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{
    --table:#08203A; --table-2:#0F3055; --panel:#0C2A49;
    --line:#3D6B96; --line-soft:#20486E;
    --ink:#E9F2FA; --ink-dim:#8FB2CE;
    --ball:#FF7A18; --warn:#FFC24D; --good:#4ADE80; --bad:#FF6B6B;
    --score:#FF7A18;   /* scoreboard accent, follows the colour picker */
    --disp:"Avenir Next Condensed","Helvetica Neue Condensed","PingFang TC",system-ui,sans-serif;
    --body:"Helvetica Neue","PingFang TC",system-ui,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,monospace;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--table);color:var(--ink);
    font-family:var(--body);font-size:14px;-webkit-font-smoothing:antialiased}
  button,input,select{font:inherit;color:inherit}

  .shell{display:grid;grid-template-columns:1fr 336px;grid-template-rows:auto auto 1fr;height:100vh}
  header,.setbar{grid-column:1/-1;display:flex;gap:16px;align-items:center;flex-wrap:wrap;
    padding:9px 16px;background:var(--panel);border-bottom:1px solid var(--line-soft)}
  .setbar{padding:7px 16px;gap:14px;background:var(--table-2)}
  .setbar .grp{display:flex;align-items:center;gap:7px;padding-right:14px;
    border-right:1px solid var(--line-soft)}
  .setbar .grp:last-child{border-right:0}
  .setbar .tag{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-dim)}

  .brand{font-family:var(--disp);font-size:19px;letter-spacing:.12em;text-transform:uppercase;
    display:flex;align-items:center;gap:9px;white-space:nowrap}
  .brand i{width:9px;height:9px;border-radius:50%;background:var(--ball);display:block}
  .brand small{font-family:var(--mono);font-size:10px;letter-spacing:0;color:var(--ink-dim)}
  .ctl{display:flex;align-items:center;gap:6px;color:var(--ink-dim);font-size:12px}
  input[type=text],input[type=number],select{
    background:var(--table);border:1px solid var(--line-soft);border-radius:3px;
    padding:5px 7px;color:var(--ink);font-family:var(--mono);font-size:12px}
  input[type=text]{width:92px;font-family:var(--body)}
  input[type=number]{width:64px}
  #fps{width:78px}   /* auto-detect fills in values like 29.97 / 119.88, needs the room */
  select{font-family:var(--body)}
  input:disabled{opacity:.35}
  input[type=color]{width:34px;height:26px;padding:2px;background:var(--table);
    border:1px solid var(--line-soft);border-radius:3px;cursor:pointer}
  .btn{background:transparent;border:1px solid var(--line);border-radius:3px;
    padding:6px 11px;cursor:pointer;font-size:12px;letter-spacing:.04em;transition:background .12s}
  .btn:hover{background:var(--line-soft)}
  .btn:disabled{opacity:.4;cursor:default}
  .btn:disabled:hover{background:transparent}
  .btn:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--ball);outline-offset:1px}
  .btn.hot{border-color:var(--ball);color:var(--ball)}
  .btn.hot:hover:not(:disabled){background:rgba(255,122,24,.14)}
  label.file{position:relative;overflow:hidden}
  label.file input{position:absolute;inset:0;opacity:0;cursor:pointer}
  .srcname{font-family:var(--mono);font-size:11.5px;color:var(--ink-dim);
    max-width:230px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

  .stage{display:flex;flex-direction:column;min-width:0;min-height:0;padding:14px 16px;gap:12px}
  .screen{flex:1;min-height:0;background:#04121F;border:1px solid var(--line-soft);
    border-radius:4px;display:flex;align-items:center;justify-content:center}
  video{max-width:100%;max-height:100%;display:block}
  .empty{color:var(--ink-dim);text-align:center;padding:30px;line-height:1.8;max-width:430px}
  .empty b{color:var(--ink);font-weight:500}

  .transport{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
  .tc{font-family:var(--mono);font-size:20px;font-variant-numeric:tabular-nums}
  .tc small{font-size:12px;color:var(--ink-dim);margin-left:7px}
  .scrub{flex:1;min-width:160px;accent-color:var(--ball)}
  .speed{display:flex;gap:3px}
  .speed button{padding:4px 8px;font-family:var(--mono);font-size:11px}
  .speed button[aria-pressed=true]{border-color:var(--ball);color:var(--ball)}

  .tline{position:relative;height:18px;background:#04121F;border:1px solid var(--line-soft);
    border-radius:3px;overflow:hidden;cursor:pointer;flex:none}
  .tline i{position:absolute;top:0;bottom:0}
  .tline i.keep{background:rgba(255,122,24,.30)}
  .tline i.hl{top:10px;background:rgba(255,211,77,.85)}
  .tline i.sv{width:1px;bottom:9px;background:rgba(233,242,250,.4)}
  .tline i.ph{width:2px;background:#fff;opacity:.85}
  .legend{display:flex;gap:8px;flex-wrap:wrap;font-size:11.5px;color:var(--ink-dim)}
  .legend span{border:1px solid var(--line-soft);border-radius:3px;padding:3px 8px}
  .legend kbd{font-family:var(--mono);color:var(--ink);margin-right:5px}

  .rail{border-left:1px solid var(--line-soft);display:flex;flex-direction:column;
    min-height:0;background:var(--panel)}
  .board{padding:16px 16px 12px;border-bottom:1px solid var(--line-soft)}
  .cards{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .card{position:relative;background:var(--table);border:1px solid var(--line-soft);
    border-radius:4px;padding:8px 0 10px;text-align:center}
  .card.serving{border-color:var(--ball)}
  .card .who{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-dim);
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 8px}
  .card .nums{display:flex;align-items:baseline;justify-content:center;gap:12px;margin-top:2px}
  .card .g{font-family:var(--disp);font-size:30px;line-height:1;color:var(--ink-dim)}
  .card .pts{font-family:var(--disp);font-size:58px;line-height:.98;font-variant-numeric:tabular-nums}
  .card.serving .pts{color:var(--score)}
  .card .dots{font-size:11px;letter-spacing:2px;color:var(--score);min-width:16px;text-align:left}
  .card .cap{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-dim);opacity:.7}
  .boardmeta{display:flex;justify-content:space-between;margin-top:10px;font-size:11.5px;color:var(--ink-dim)}
  .boardmeta b{color:var(--ink);font-weight:500}
  .boardmeta .rule{color:var(--warn)}
  .adjbar{display:flex;align-items:center;gap:4px;margin-top:9px;font-size:11px;color:var(--ink-dim)}
  .adjbar input[type=number]{width:38px;padding:3px 4px;font-size:11px}
  .adjbar select{font-size:11px;padding:3px 2px}
  .adjbar .btn{padding:3px 8px;font-size:11px}

  .streamhead{display:flex;justify-content:space-between;align-items:center;padding:9px 14px;
    border-bottom:1px solid var(--line-soft);font-size:11px;letter-spacing:.13em;
    text-transform:uppercase;color:var(--ink-dim)}
  .stream{flex:1;overflow-y:auto;min-height:80px}
  .ev{display:grid;grid-template-columns:60px 1fr auto auto auto;gap:8px;align-items:center;
    padding:6px 14px;border-bottom:1px solid rgba(32,72,110,.5);cursor:pointer;font-size:12.5px}
  .ev:hover{background:var(--table-2)}
  .ev time{font-family:var(--mono);font-size:11.5px;color:var(--ink-dim)}
  .ev .lbl{display:flex;align-items:center;gap:7px;min-width:0}
  .ev .dot{width:6px;height:6px;border-radius:50%;background:var(--line);flex:none}
  .ev.serve .dot{background:var(--ball)}
  .ev.game .dot{background:var(--warn)}
  .ev .sc{font-family:var(--mono);font-size:11.5px;color:var(--ink-dim)}
  .ev .sc em{color:var(--warn);font-style:normal}
  .ev .kill{border:0;background:none;color:var(--ink-dim);cursor:pointer;padding:0 3px;font-size:15px}
  .ev .kill:hover{color:var(--ball)}
  .streamempty{padding:22px 14px;color:var(--ink-dim);font-size:12.5px;line-height:1.7}
  .capbar{display:flex;gap:6px;padding:8px 14px;border-bottom:1px solid var(--line-soft)}
  .capbar input[type=text]{flex:1;width:auto;font-family:var(--body)}
  .capbar input[type=number]{width:52px}
  .ev.caption .dot{background:#9C6ADE}
  .ev.hl .dot{background:#FFD34D}
  .ev.adjust .dot{background:#FF6B6B}

  .cutout{border-top:1px solid var(--line-soft);padding:11px 14px;font-size:12px;
    color:var(--ink-dim);display:flex;flex-direction:column;gap:5px}
  .cutout .row{display:flex;justify-content:space-between}
  .cutout b{color:var(--ink);font-family:var(--mono);font-weight:400}
  .cutout .save{color:var(--ball)}
  .pads{display:flex;gap:8px 10px;margin-top:4px;flex-wrap:wrap}
  .pads .ctl{font-size:11px}

  .render{border-top:1px solid var(--line-soft);padding:11px 14px;display:flex;
    flex-direction:column;gap:8px;background:var(--table-2)}
  .render .line{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--ink-dim)}
  .render .out{font-family:var(--mono);font-size:11px;color:var(--ink-dim);
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;direction:rtl;text-align:left}
  .go{width:100%;padding:9px;font-size:13px;letter-spacing:.06em}
  .bar{height:5px;background:var(--table);border-radius:3px;overflow:hidden}
  .bar i{display:block;height:100%;width:0;background:var(--ball);
    transition:width .3s linear}
  .bar.done i{background:var(--good)}
  .bar.bad i{background:var(--bad)}
  .pmeta{display:flex;justify-content:space-between;font-size:11px;
    font-family:var(--mono);color:var(--ink-dim)}
  .plog{font-family:var(--mono);font-size:10.5px;color:var(--ink-dim);
    max-height:76px;overflow-y:auto;line-height:1.55;white-space:pre-wrap;word-break:break-all}
  .plog.bad{color:var(--bad)}
  .note{font-size:11px;color:var(--warn);line-height:1.5}

  @media (max-width:960px){
    .shell{grid-template-columns:1fr;grid-template-rows:auto auto auto 1fr;height:auto}
    .rail{border-left:0;border-top:1px solid var(--line-soft)}
    .stage{height:54vh}
  }
  @media (prefers-reduced-motion:reduce){*{transition:none !important}}
</style>

<div class="shell">
  <header>
    <div class="brand"><i></i>ttcut<small>__VERSION__</small></div>
    <button class="btn" id="pick">Load video</button>
    <span class="srcname" id="srcname">nothing loaded</span>
    <div class="ctl">A<input type="text" id="nameA" value="Player A" title='Doubles: enter both players, e.g. "Kim / Lee" — ● = first (#1), ●● = second (#2)'></div>
    <div class="ctl">B<input type="text" id="nameB" value="Player B" title='Doubles: enter both players, e.g. "Park / Cho" — ● = first (#1), ●● = second (#2)'></div>
    <div class="ctl">First serve<select id="firstServer"><option value="0">A</option><option value="1">B</option></select></div>
    <span style="flex:1"></span>
    <label class="btn file">Load tags<input type="file" id="load" accept=".json"></label>
    <button class="btn" id="save">Export JSON</button>
    <button class="btn" id="score" title="Download the game results and point-by-point log (plain text)">Export score</button>
  </header>

  <div class="setbar">
    <div class="grp"><span class="tag">fps</span>
      <input type="number" id="fps" value="30" min="1" max="240" step="1"></div>
    <div class="grp"><span class="tag">mode</span>
      <select id="side" title="In doubles the scoreboard and the UI show which player of the pair (#1 / #2) is serving">
        <option value="singles">Singles</option>
        <option value="doubles">Doubles</option>
      </select></div>
    <div class="grp"><span class="tag">game to</span>
      <input type="number" id="target" value="11" min="1" step="1"><span class="tag">pts</span></div>
    <div class="grp"><span class="tag">ending</span>
      <select id="deuce">
        <option value="standard">Standard · by 2</option>
        <option value="capped">Capped · first to cap</option>
      </select>
      <span class="tag">cap</span><input type="number" id="cap" value="12" min="2" step="1" disabled></div>
    <div class="grp"><span class="tag">games</span>
      <input type="number" id="sgA" value="0" min="0" step="1">
      <span class="tag">:</span>
      <input type="number" id="sgB" value="0" min="0" step="1"></div>
    <div class="grp"><span class="tag">handicap</span>
      <input type="number" id="spA" value="0" min="0" step="1">
      <span class="tag">:</span>
      <input type="number" id="spB" value="0" min="0" step="1">
      <select id="scope">
        <option value="every">Every game</option>
        <option value="first">First game</option>
      </select></div>
    <div class="grp"><span class="tag">accent</span>
      <input type="color" id="accent" value="#FF7A18"
             title="Shared by the point digits and the bar beside the names">
      <button class="btn" id="accentReset" title="Back to the default orange">Reset</button></div>
  </div>

  <div class="stage">
    <div class="screen" id="screen">
      <div class="empty" id="empty">
        Click <b>Load video</b> at the top left, or <b>drag a video file into this window</b>.<br>
        The file is read straight from this computer and is never uploaded anywhere.
      </div>
    </div>

    <div class="transport">
      <div class="tc"><span id="tc">00:00.00</span><small id="frameno">frame 0</small></div>
      <input type="range" class="scrub" id="scrub" min="0" max="0" step="0.001" value="0" aria-label="Playback position">
      <div class="speed" id="speed">
        <button class="btn" data-r="0.5">.5×</button>
        <button class="btn" data-r="1" aria-pressed="true">1×</button>
        <button class="btn" data-r="1.5">1.5×</button>
        <button class="btn" data-r="2">2×</button>
      </div>
    </div>

    <div class="tline" id="tline"
         title="Bright = kept, dark = cut, gold = highlight. Click to jump."></div>

    <div class="legend">
      <span><kbd>space</kbd>play / pause</span>
      <span><kbd>S</kbd>serve</span>
      <span><kbd>A</kbd>point A</span>
      <span><kbd>B</kbd>point B</span>
      <span><kbd>H</kbd>highlight</span>
      <span><kbd>N</kbd>new game</span>
      <span><kbd>Z</kbd>undo</span>
      <span><kbd>← →</kbd>1 s</span>
      <span><kbd>⇧← →</kbd>5 s</span>
      <span><kbd>⌥← →</kbd>frame</span>
      <span><kbd>1-4</kbd>speed</span>
    </div>
  </div>

  <div class="rail">
    <div class="board">
      <div class="cards">
        <div class="card" id="cardA">
          <div class="who" id="whoA">Player A</div>
          <div class="nums"><span class="g" id="gmA">0</span><span class="pts" id="ptsA">0</span><span class="dots" id="dotsA"></span></div>
          <div class="cap">games · points</div>
        </div>
        <div class="card" id="cardB">
          <div class="who" id="whoB">Player B</div>
          <div class="nums"><span class="g" id="gmB">0</span><span class="pts" id="ptsB">0</span><span class="dots" id="dotsB"></span></div>
          <div class="cap">games · points</div>
        </div>
      </div>
      <div class="boardmeta">
        <span>Game <b id="gameNo">1</b><span id="ruleNote" class="rule"></span></span>
        <span><b id="expServer">A</b> to serve<span id="srvNumTxt"></span></span>
      </div>
      <div class="adjbar" title="Score correction at the current playback position — fill in only the fields you want to change; scoring continues from there. Fixes a mis-tag or sets the games mid-match without re-tagging.">
        <span class="tag">fix</span>
        <span>g</span><input type="number" id="adjGA" placeholder="·" min="0"><input type="number" id="adjGB" placeholder="·" min="0">
        <span>p</span><input type="number" id="adjPA" placeholder="·" min="0"><input type="number" id="adjPB" placeholder="·" min="0">
        <select id="adjSrv"><option value="">srv —</option><option value="A">A</option><option value="B">B</option></select>
        <select id="adjNum" title="Doubles: which player of the serving pair is up (use it for the receiver swap at 5 in the deciding game)"><option value="">#—</option><option value="1">#1</option><option value="2">#2</option></select>
        <button class="btn" id="adjAdd">Fix</button>
      </div>
    </div>

    <div class="streamhead"><span>events</span><span id="evcount">0</span></div>
    <div class="capbar">
      <input type="text" id="capText" placeholder="Caption text… (Enter adds it)" maxlength="120">
      <input type="number" id="capDur" value="3" min="0.5" step="0.5" title="Seconds on screen">
      <button class="btn" id="capAdd" title="Burn this line into the video, bottom-centre, at the current time">+ Cap</button>
    </div>
    <div class="stream" id="stream"></div>

    <div class="cutout">
      <div class="row"><span>Cuttable segments</span><b id="cutN">0</b></div>
      <div class="row"><span>Time removed</span><b class="save" id="cutT">0.0s</b></div>
      <div class="row"><span>Output length</span><b id="outT">0.0s</b></div>
      <div class="pads">
        <div class="ctl">after point<input type="number" id="tailPad" value="1.0" step="0.1" min="0">s</div>
        <div class="ctl">before serve<input type="number" id="leadPad" value="0.3" step="0.1" min="0">s</div>
        <div class="ctl">min cut<input type="number" id="minCut" value="2.0" step="0.1" min="0">s</div>
      </div>
    </div>

    <div class="render">
      <div class="line">
        <span>Quality</span>
        <select id="quality">
          <option value="fast">Fast</option>
          <option value="high" selected>Standard</option>
          <option value="max">Best (slow)</option>
        </select>
        <select id="renderScope" title="What to render: the full cut match, only the rallies marked with H, or both files in one go">
          <option value="full">Full match</option>
          <option value="highlights">Highlights only</option>
          <option value="both">Full + highlights</option>
        </select>
        <select id="encoder" title="Encoder: auto = the GPU hardware encoder detected at startup (CPU when there is none). Max quality always uses the CPU.">
          <option value="">Auto</option>
          <option value="libx264">CPU (libx264)</option>
        </select>
        <label class="ctl" style="margin-left:auto"><input type="checkbox" id="cutLets">cut lets too</label>
      </div>
      <div class="out" id="outPath">—</div>
      <button class="btn hot go" id="go" disabled>Render video</button>
      <div id="progWrap" hidden>
        <div class="bar" id="bar"><i></i></div>
        <div class="pmeta"><span id="pctTxt">0%</span><span id="etaTxt"></span></div>
      </div>
      <div class="plog" id="plog" hidden></div>
      <div class="note" id="note" hidden></div>
    </div>
  </div>
</div>

<script>
(() => {
  const VERSION = "__VERSION__";
  const $ = id => document.getElementById(id);
  const screenEl = $('screen'), emptyEl = $('empty');

  let video = null, events = [], mediaTime = 0, srcName = '', srcPath = '';
  let outPath = '', ffmpegOK = false, polling = null;
  let blobURL = null, fpsSamples = [], fpsFilled = false;

  const num = (id, d) => { const v = +$(id).value; return isFinite(v) ? v : d; };
  const fps    = () => Math.max(1, num('fps', 30));
  const target = () => Math.max(1, num('target', 11));
  const deuce  = () => $('deuce').value;
  const capVal = () => Math.max(target(), num('cap', target() + 1));
  const scope  = () => $('scope').value;
  const side   = () => $('side').value;
  const isDoubles = () => side() === 'doubles';
  const firstServer = () => +$('firstServer').value;
  const names  = () => [$('nameA').value || 'A', $('nameB').value || 'B'];
  const startGames  = () => [Math.max(0, num('sgA', 0)), Math.max(0, num('sgB', 0))];
  const startPoints = () => [Math.max(0, num('spA', 0)), Math.max(0, num('spB', 0))];

  const fmt = t => {
    if (!isFinite(t) || t < 0) t = 0;
    const m = Math.floor(t / 60), s = t - m * 60;
    return String(m).padStart(2,'0') + ':' + s.toFixed(2).padStart(5,'0');
  };
  const frameOf = t => Math.round(t * fps());
  const mmss = s => {
    if (s == null) return '';
    s = Math.round(s);
    return Math.floor(s/60) + ':' + String(s%60).padStart(2,'0');
  };
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  /* ───────────────────────── Payload sent to Python
     Scoring and cut statistics are computed in Python only; the interface no
     longer keeps its own copy of that logic. */
  function docPayload() {
    const nm = names(), sg = startGames(), sp = startPoints();
    return {
      version: 2, generator: 'ttcut ' + VERSION, source: srcName, fps: fps(),
      pointsPerGame: target(),
      players: {A: nm[0], B: nm[1]},
      firstServer: firstServer() === 0 ? 'A' : 'B',
      format: {pointsPerGame: target(), deuce: deuce(), cap: capVal(), side: side()},
      start: {games: {A: sg[0], B: sg[1]},
              points: {A: sp[0], B: sp[1]},
              handicapScope: scope()},
      pads: {tail: num('tailPad', 1), lead: num('leadPad', 0.3)},
      scoreboard: {accent: $('accent').value},
      events: events.map(e => ({...e, t: +e.t.toFixed(3), frame: frameOf(e.t)}))
    };
  }
  const optPayload = () => ({
    min_cut: num('minCut', 2), cut_lets: $('cutLets').checked,
    quality: $('quality').value, scope: $('renderScope').value,
    encoder: $('encoder').value || undefined
  });

  /* ───────────────────────── Video */
  $('pick').addEventListener('click', async () => {
    $('pick').disabled = true;
    try {
      const r = await fetch('/pick-video', {method: 'POST'});
      const d = await r.json();
      if (d.cancelled || !d.path) return;
      if (blobURL) { URL.revokeObjectURL(blobURL); blobURL = null; }
      srcPath = d.path; srcName = d.name; outPath = d.defaultOut;
      $('srcname').textContent = d.name;
      $('srcname').title = d.path;
      $('outPath').textContent = d.defaultOut;
      if (d.info) {
        if (d.info.fps) $('fps').value = Math.round(d.info.fps * 100) / 100;
        $('srcname').title = `${d.path}\n${d.info.w}×${d.info.h} · ${d.info.fps}fps · ${d.info.codec}`;
      }
      mountVideo();
      updateGo();
      refresh();
    } catch (e) {
      banner('Could not load the video: ' + e.message);
    } finally { $('pick').disabled = false; }
  });

  function mountVideo(src) {
    if (video) { video.pause(); video.remove(); }
    video = document.createElement('video');
    video.src = src || ('/video?t=' + Date.now());
    video.preload = 'auto'; video.playsInline = true;
    emptyEl.style.display = 'none';
    screenEl.appendChild(video);
    video.addEventListener('loadedmetadata', () => {
      $('scrub').max = video.duration || 0; tick();
    });
    video.addEventListener('timeupdate', tick);
    video.addEventListener('seeked', tick);
    video.addEventListener('error', () => banner('This video will not play; the browser may not support its codec.'));
    pumpFrames();
  }

  function pumpFrames() {
    if (!video || !video.requestVideoFrameCallback) return;
    video.requestVideoFrameCallback((now, meta) => {
      /* A dropped file cannot be probed by ffprobe (no path), so estimate the
         frame rate from presented-frame timing during plain 1x playback and
         snap it to the nearest standard rate. */
      if (blobURL && !fpsFilled && video && !video.paused && video.playbackRate === 1) {
        fpsSamples.push(meta.mediaTime);
        if (fpsSamples.length >= 30) {
          const dt = fpsSamples[fpsSamples.length - 1] - fpsSamples[0];
          if (dt > 0.2) {
            const est = (fpsSamples.length - 1) / dt;
            const std = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 119.88, 120];
            let best = std[0];
            for (const s of std) if (Math.abs(s - est) < Math.abs(best - est)) best = s;
            if (Math.abs(best - est) / best < 0.05) {
              $('fps').value = Math.round(best * 100) / 100;
              fpsFilled = true; refresh();
            }
          }
          fpsSamples = [];
        }
      }
      mediaTime = meta.mediaTime; tick(); pumpFrames();
    });
  }
  function now() {
    if (!video) return 0;
    const t = (video.requestVideoFrameCallback && !video.seeking) ? mediaTime : video.currentTime;
    return isFinite(t) ? t : video.currentTime;
  }
  function tick() {
    if (!video) return;
    const t = now();
    $('tc').textContent = fmt(t);
    $('frameno').textContent = 'frame ' + frameOf(t);
    if (document.activeElement !== $('scrub')) $('scrub').value = t;
    positionPlayhead();
  }
  $('scrub').addEventListener('input', e => { if (video) video.currentTime = +e.target.value; });

  function seekBy(sec) {
    if (!video) return;
    video.pause();
    const t = Math.max(0, Math.min(video.duration || 0, now() + sec));
    video.currentTime = Math.round(t * fps()) / fps();
  }
  function setRate(r) {
    if (video) video.playbackRate = r;
    [...$('speed').children].forEach(b => b.setAttribute('aria-pressed', String(+b.dataset.r === r)));
  }
  $('speed').addEventListener('click', e => {
    const b = e.target.closest('button'); if (b) setRate(+b.dataset.r);
  });

  /* ───────────────────────── Drag & drop
     Browsers never reveal a dropped file's real path, so the drop mounts the
     file directly for preview and tagging; the native dialog opens once at
     render time to tell Python (and ffmpeg) where the file actually lives. */
  addEventListener('dragover', e => e.preventDefault());
  addEventListener('drop', e => {
    e.preventDefault();
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!f) return;
    if (/\.json$/i.test(f.name)) { loadTagsFile(f); return; }
    if (!/^video\//.test(f.type) &&
        !/\.(mp4|mov|m4v|mkv|avi|webm|ts|mts)$/i.test(f.name)) {
      banner('That does not look like a video file.'); return;
    }
    if (blobURL) URL.revokeObjectURL(blobURL);
    blobURL = URL.createObjectURL(f);
    srcPath = ''; srcName = f.name; outPath = '';
    fpsSamples = []; fpsFilled = false;
    $('srcname').textContent = f.name + ' (dropped)';
    $('srcname').title = f.name;
    $('outPath').textContent = '—';
    mountVideo(blobURL);
    banner('Dropped video ready for tagging; the frame rate fills in during 1x playback. Rendering will open the file dialog once to confirm where the file lives.');
    updateGo(); refresh();
  });

  /* ───────────────────────── Events */
  function addCaption() {
    if (!video) return;
    const txt = $('capText').value.trim();
    if (!txt) { $('capText').focus(); return; }
    const t = Math.round(now() * fps()) / fps();
    events.push({t, type: 'caption', text: txt, dur: Math.max(0.5, num('capDur', 3))});
    events.sort((a, b) => a.t - b.t);
    $('capText').value = '';
    refresh();
  }
  $('capAdd').addEventListener('click', addCaption);
  $('capText').addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); addCaption(); }
  });

  /* Score correction: only the filled-in fields override; scoring continues
     from the corrected state. */
  function addAdjust() {
    if (!video) return;
    const t = Math.round(now() * fps()) / fps();
    const ev = {t, type: 'adjust'};
    const gA = $('adjGA').value, gB = $('adjGB').value;
    const pA = $('adjPA').value, pB = $('adjPB').value;
    if (gA !== '' || gB !== '')
      ev.games = {...(gA === '' ? {} : {A: +gA}), ...(gB === '' ? {} : {B: +gB})};
    if (pA !== '' || pB !== '')
      ev.points = {...(pA === '' ? {} : {A: +pA}), ...(pB === '' ? {} : {B: +pB})};
    if ($('adjSrv').value) ev.server = $('adjSrv').value;
    if ($('adjNum').value) ev.serverNum = +$('adjNum').value;
    if (!ev.games && !ev.points && !ev.server && !ev.serverNum) {
      banner('Fill in at least one field to correct (games, points, server or #).');
      return;
    }
    events.push(ev);
    events.sort((a, b) => a.t - b.t);
    ['adjGA','adjGB','adjPA','adjPB'].forEach(id => $(id).value = '');
    $('adjSrv').value = ''; $('adjNum').value = '';
    refresh();
  }
  $('adjAdd').addEventListener('click', addAdjust);

  function add(type, winner) {
    if (!video) return;
    const t = Math.round(now() * fps()) / fps();
    events.push(winner === undefined ? {t, type} : {t, type, winner});
    events.sort((a,b) => a.t - b.t);
    refresh();
  }
  function undo() {
    if (!events.length) return;
    let idx = 0;
    for (let i = 1; i < events.length; i++) if (events[i].t >= events[idx].t) idx = i;
    events.splice(idx, 1); refresh();
  }

  /* ───────────────────────── Ask Python for the score */
  let seq = 0, timer = null;
  function refresh() {
    clearTimeout(timer);
    timer = setTimeout(doRefresh, 50);
  }
  async function doRefresh() {
    const mine = ++seq;
    $('cap').disabled = deuce() !== 'capped';
    try {
      const r = await fetch('/fold', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({doc: docPayload(), opt: optPayload()})
      });
      const st = await r.json();
      if (mine !== seq) return;               // drop stale responses
      paint(st);
      banner(!st.ok && $('renderScope').value === 'highlights' ? st.reason : null);
    } catch (e) {
      banner('Cannot reach the local service. Is the terminal window still open?');
    }
  }

  /* ───────────────────────── Painting */
  function paint(st) {
    const nm = names(), cur = st.cur;
    $('whoA').textContent = nm[0]; $('whoB').textContent = nm[1];
    $('ptsA').textContent = cur.a;  $('ptsB').textContent = cur.b;
    $('gmA').textContent = cur.gA;  $('gmB').textContent = cur.gB;
    $('gameNo').textContent = cur.gameNo;
    $('ruleNote').textContent = deuce() === 'capped' ? ` · cap ${capVal()}` : '';
    $('expServer').textContent = nm[cur.server];
    $('srvNumTxt').textContent = isDoubles() ? ` · #${cur.serverNum}` : '';
    const dots = '●'.repeat(isDoubles() ? cur.serverNum : 1);
    $('dotsA').textContent = cur.server === 0 ? dots : '';
    $('dotsB').textContent = cur.server === 1 ? dots : '';
    $('cardA').classList.toggle('serving', cur.server === 0);
    $('cardB').classList.toggle('serving', cur.server === 1);

    const stream = $('stream');
    $('evcount').textContent = events.length;
    if (!events.length) {
      stream.innerHTML = '<div class="streamempty">No events yet.<br>Play the video and press <b style="color:var(--ink)">S</b> the moment the ball leaves the bat on a serve, then <b style="color:var(--ink)">A</b> or <b style="color:var(--ink)">B</b> when the point is won.</div>';
    } else {
      let prevServe = false, html = '';
      events.forEach((e, i) => {
        const s = st.snaps[i];
        let label, cls;
        if (e.type === 'serve') { cls = 'serve'; label = prevServe ? 'Serve · let' : 'Serve'; }
        else if (e.type === 'game') { cls = 'game'; label = 'New game'; }
        else if (e.type === 'caption') { cls = 'caption'; label = '“' + esc(e.text) + '”'; }
        else if (e.type === 'highlight') { cls = 'hl'; label = '★ Highlight'; }
        else if (e.type === 'adjust') {
          cls = 'adjust';
          const p = [];
          if (e.games) p.push(`${e.games.A ?? '·'}–${e.games.B ?? '·'} games`);
          if (e.points) p.push(`${e.points.A ?? '·'}–${e.points.B ?? '·'}`);
          if (e.server || e.serverNum)
            p.push('serve ' + (e.server || '') + (e.serverNum ? '#' + e.serverNum : ''));
          label = 'Fix ' + p.join(' · ');
        }
        else { cls = 'point'; label = 'Point ' + nm[e.winner === 'A' ? 0 : 1]; }
        prevServe = e.type === 'serve' ||
          (['caption','highlight','adjust'].includes(e.type) && prevServe);
        const sc = s ? (s.won ? `<em>${s.gA}–${s.gB} games</em>` : `${s.a}–${s.b}`) : '';
        html += `<div class="ev ${cls}" data-i="${i}">
          <time>${fmt(e.t)}</time>
          <span class="lbl"><i class="dot"></i>${label}</span>
          <span class="sc">${s && s.won ? `${s.a}–${s.b}` : ''}</span>
          <span class="sc">${sc}</span>
          <button class="kill" data-move="${i}" title="Move to the current playback position">⟲</button>
          <button class="kill" data-kill="${i}" title="Delete">×</button>
        </div>`;
      });
      stream.innerHTML = html;
      stream.scrollTop = stream.scrollHeight;
    }

    const c = st.cuts || {};
    $('cutN').textContent = c.n || 0;
    $('cutT').textContent = (c.seconds || 0).toFixed(1) + 's';
    $('outT').textContent = (c.outSeconds || 0).toFixed(1) + 's'
      + (c.pct ? ` · ${c.pct}% shorter` : '');
    drawTimeline(st);
    updateGo(st.ok);
  }

  /* ── LosslessCut-style timeline: bright = kept, dark = cut, gold = highlight */
  function drawTimeline(st) {
    const tl = $('tline');
    const dur = video && video.duration;
    if (!dur) { tl.innerHTML = ''; return; }
    const pct = t => (Math.max(0, Math.min(dur, t)) / dur * 100);
    const seg = (k, cls) =>
      `<i class="${cls}" style="left:${pct(k.from).toFixed(3)}%;width:${Math.max(0.15, pct(k.to) - pct(k.from)).toFixed(3)}%"></i>`;
    let html = '';
    (st.keepList || []).forEach(k => html += seg(k, 'keep'));
    (st.hlList || []).forEach(k => html += seg(k, 'hl'));
    events.filter(e => e.type === 'serve').forEach(e =>
      html += `<i class="sv" style="left:${pct(e.t).toFixed(3)}%"></i>`);
    html += '<i class="ph" id="tlph"></i>';
    tl.innerHTML = html;
    positionPlayhead();
  }
  function positionPlayhead() {
    const ph = document.getElementById('tlph');
    if (ph && video && video.duration)
      ph.style.left = (now() / video.duration * 100).toFixed(3) + '%';
  }
  $('tline').addEventListener('click', e => {
    if (!video || !video.duration) return;
    const r = e.currentTarget.getBoundingClientRect();
    video.pause();
    video.currentTime = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * video.duration;
  });

  function updateGo(planOK) {
    const running = polling !== null;
    const loaded = !!srcPath || !!blobURL;
    const ok = loaded && ffmpegOK && events.length > 0 && planOK !== false;
    $('go').disabled = running || !ok;
    if (!ffmpegOK && loaded) $('go').textContent = 'ffmpeg not found';
    else $('go').textContent = running ? 'Rendering…'
      : (!srcPath && blobURL ? 'Render video (confirm file…)' : 'Render video');
  }

  function banner(msg) {
    const n = $('note');
    if (!msg) { n.hidden = true; return; }
    n.hidden = false; n.textContent = msg;
  }

  $('stream').addEventListener('click', e => {
    const k = e.target.closest('[data-kill]');
    if (k) { events.splice(+k.dataset.kill, 1); refresh(); return; }
    const mv = e.target.closest('[data-move]');
    if (mv && video) {          // re-time a mis-placed tag without re-tagging
      events[+mv.dataset.move].t = Math.round(now() * fps()) / fps();
      events.sort((a, b) => a.t - b.t);
      refresh(); return;
    }
    const row = e.target.closest('.ev');
    if (row && video) { video.pause(); video.currentTime = events[+row.dataset.i].t; }
  });

  function paintAccent() {
    document.documentElement.style.setProperty('--score', $('accent').value);
  }
  $('accent').addEventListener('input', paintAccent);
  $('accentReset').addEventListener('click', () => {
    $('accent').value = '#FF7A18'; paintAccent();
  });

  ['nameA','nameB','firstServer','target','fps','tailPad','leadPad','minCut',
   'deuce','cap','sgA','sgB','spA','spB','scope','cutLets','renderScope','side']
    .forEach(id => $(id).addEventListener('input', refresh));

  /* ───────────────────────── Keyboard
     Only fields you actually type in swallow the shortcuts; the scrub bar,
     checkboxes and buttons keep focus after a click, and the shortcuts must
     keep working then (preventDefault stops the control's own key action). */
  addEventListener('keydown', e => {
    const el = document.activeElement;
    if (el && (el.tagName === 'SELECT' || el.tagName === 'TEXTAREA' ||
               (el.tagName === 'INPUT' && !/^(range|checkbox)$/.test(el.type)))) return;
    if (e.metaKey || e.ctrlKey) return;
    const step = e.altKey ? 1 / fps() : e.shiftKey ? 5 : 1;
    switch (e.key) {
      case ' ':          if (video) video.paused ? video.play() : video.pause(); break;
      case 'ArrowLeft':  seekBy(-step); break;
      case 'ArrowRight': seekBy(step); break;
      case 's': case 'S': add('serve'); break;
      case 'a': case 'A': add('point', 'A'); break;
      case 'b': case 'B': add('point', 'B'); break;
      case 'h': case 'H': add('highlight'); break;
      case 'n': case 'N': add('game'); break;
      case 'z': case 'Z': undo(); break;
      case '1': setRate(0.5); break;
      case '2': setRate(1); break;
      case '3': setRate(1.5); break;
      case '4': setRate(2); break;
      default: return;
    }
    e.preventDefault();
  });

  /* ───────────────────────── Rendering */
  $('go').addEventListener('click', async () => {
    $('go').disabled = true;
    if (!srcPath) {          // dropped file: confirm the real location once
      try {
        const r = await fetch('/pick-video', {method: 'POST'});
        const d = await r.json();
        if (d.cancelled || !d.path) {
          banner('Rendering needs the actual file on disk — pick it in the dialog (choose the same file you dropped).');
          updateGo(); return;
        }
        srcPath = d.path; srcName = d.name; outPath = d.defaultOut;
        $('srcname').textContent = d.name;
        $('srcname').title = d.path;
        $('outPath').textContent = d.defaultOut;
        if (d.info && d.info.fps) $('fps').value = Math.round(d.info.fps * 100) / 100;
        banner(null);
      } catch (e) { banner('Could not confirm the file: ' + e.message); updateGo(); return; }
    }
    $('plog').hidden = true; $('plog').classList.remove('bad');
    $('bar').classList.remove('done','bad');
    $('progWrap').hidden = false;
    setBar(0, 'starting ffmpeg…');
    try {
      const r = await fetch('/render', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({doc: docPayload(), opt: optPayload(), out: outPath})
      });
      const d = await r.json();
      if (d.error) { fail(d.error); return; }
      if (d.notes && d.notes.length) {
        $('plog').hidden = false; $('plog').textContent = d.notes.join('\n');
      }
      startPolling();
    } catch (e) { fail(e.message); }
  });

  function setBar(pct, right) {
    $('bar').querySelector('i').style.width = Math.max(0, Math.min(100, pct)) + '%';
    $('pctTxt').textContent = pct.toFixed(0) + '%';
    $('etaTxt').textContent = right || '';
  }
  function fail(msg) {
    $('bar').classList.add('bad');
    $('plog').hidden = false; $('plog').classList.add('bad');
    $('plog').textContent = msg;
    polling = null; updateGo();
  }

  function startPolling() {
    polling = setInterval(async () => {
      try {
        const s = await (await fetch('/render/status')).json();
        if (s.state === 'running') {
          setBar(s.pct, (s.eta != null ? '~' + mmss(s.eta) + ' left' : '') +
                        (s.speed ? ' · ' + s.speed : ''));
          updateGo();
        } else {
          clearInterval(polling); polling = null;
          if (s.state === 'done') {
            setBar(100, mmss(s.elapsed) + ' elapsed');
            $('bar').classList.add('done');
            $('plog').hidden = false;
            $('plog').textContent = 'Done -> ' + s.out;
          } else if (s.state === 'cancelled') {
            setBar(s.pct, 'cancelled');
          } else {
            fail((s.message || 'Render failed') + '\n' + (s.log || []).join('\n'));
          }
          updateGo();
        }
      } catch (e) {
        clearInterval(polling); polling = null;
        fail('Lost the connection to the local service.');
      }
    }, 400);
    updateGo();
  }

  /* ───────────────────────── Save and load */
  $('score').addEventListener('click', async () => {
    try {
      const d = await (await fetch('/score', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({doc: docPayload(), opt: optPayload()})
      })).json();
      const url = URL.createObjectURL(new Blob([d.text || ''], {type: 'text/plain;charset=utf-8'}));
      const a = document.createElement('a');
      a.href = url;
      a.download = (srcName.replace(/\.[^.]+$/, '') || 'match') + '.score.txt';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { banner('Score export failed: ' + e.message); }
  });

  $('save').addEventListener('click', async () => {
    const doc = docPayload();
    try {                       // include the cut list in the export too, matching the V1.22 format
      const st = await (await fetch('/fold', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({doc, opt: optPayload()})
      })).json();
      if (st.cutList) doc.cuts = st.cutList;
    } catch (e) { /* if it fails, leave it out; the main data is unaffected */ }
    const url = URL.createObjectURL(new Blob([JSON.stringify(doc, null, 2)], {type:'application/json'}));
    const a = document.createElement('a');
    a.href = url;
    a.download = (srcName.replace(/\.[^.]+$/, '') || 'match') + '.tags.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  function loadTagsFile(f) {
    const r = new FileReader();
    r.onload = () => {
      try {
        const d = JSON.parse(r.result);
        events = (d.events || []).map(x => ({...x})).sort((a,b) => a.t - b.t);
        if (d.fps) $('fps').value = d.fps;
        if (d.players) { $('nameA').value = d.players.A; $('nameB').value = d.players.B; }
        if (d.firstServer) $('firstServer').value = d.firstServer === 'B' ? '1' : '0';
        if (d.pads) { $('tailPad').value = d.pads.tail; $('leadPad').value = d.pads.lead; }

        const F = d.format || {};
        $('target').value = F.pointsPerGame || d.pointsPerGame || 11;
        $('deuce').value  = F.deuce || 'standard';
        $('side').value   = F.side || 'singles';
        $('cap').value    = F.cap || (+$('target').value + 1);
        const S = d.start || {}, g = S.games || {}, p = S.points || {};
        $('sgA').value = g.A || 0; $('sgB').value = g.B || 0;
        $('spA').value = p.A || 0; $('spB').value = p.B || 0;
        $('scope').value = S.handicapScope || 'every';
        $('accent').value = (d.scoreboard || {}).accent || '#FF7A18';
        paintAccent();
        refresh();
      } catch (err) {
        banner('No usable tag data in that file. Is it a JSON exported by this tool?');
      }
    };
    r.readAsText(f);
  }

  $('load').addEventListener('change', e => {
    const f = e.target.files[0]; if (!f) return;
    loadTagsFile(f);
    e.target.value = '';
  });

  /* ───────────────────────── Startup: pick the loaded state back up, so a
     browser refresh does not lose anything */
  (async () => {
    try {
      const s = await (await fetch('/state')).json();
      ffmpegOK = !!s.ffmpeg;
      if (s.ffmpeg) {          // encoder select: auto = the server-detected default, then each HW encoder
        const sel = $('encoder'), cpu = sel.querySelector('[value="libx264"]');
        sel.options[0].textContent = 'Auto (' + (s.defaultEncoder || 'libx264') + ')';
        (s.hwEncoders || []).forEach(enc => {
          const o = document.createElement('option');
          o.value = enc; o.textContent = enc; sel.insertBefore(o, cpu);
        });
      }
      if (s.video) {
        srcPath = s.video; srcName = s.videoName;
        $('srcname').textContent = s.videoName;
        $('srcname').title = s.video;
        mountVideo();
      }
      if (!s.ffmpeg) banner('ffmpeg not found. Tagging and JSON export still work, but rendering does not.');
      if (s.job && s.job.state === 'running') { $('progWrap').hidden = false; startPolling(); }
    } catch (e) { /* service not up yet, never mind */ }
    refresh();
  })();
})();
</script>
"""

# ─────────────────────────────────────────── HTTP server

def guess_type(path):
    t, _ = mimetypes.guess_type(path)
    if not t:
        ext = os.path.splitext(path)[1].lower()
        t = {".mov": "video/quicktime", ".mp4": "video/mp4",
             ".m4v": "video/x-m4v", ".mkv": "video/x-matroska"}.get(ext, "video/mp4")
    return t


class Handler(BaseHTTPRequestHandler):
    server_version = f"ttcut/{VERSION}"

    def log_message(self, *a):
        pass                                    # do not spam the console with every range request

    # ── Helpers
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self._write(body)

    def _write(self, data):
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass                                # browsers abort range requests all the time

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    # ── Routes
    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/index.html"):
            return self._html()
        if p == "/video":
            return self._video()
        if p == "/state":
            with STATE_LOCK:
                v = STATE["video"]
                job = STATE["job"]
            return self._json(dict(
                video=v, videoName=os.path.basename(v) if v else None,
                ffmpeg=STATE["ffmpeg"],
                hwEncoders=detect_hw_encoders(STATE["ffmpeg"]),
                defaultEncoder=default_encoder(STATE["ffmpeg"]),
                job=job.snapshot() if job else None))
        if p == "/render/status":
            with STATE_LOCK:
                job = STATE["job"]
            return self._json(job.snapshot() if job else dict(state="idle"))
        self.send_error(404)

    def _same_origin(self):
        """Block other web pages from poking this local service (for instance to
        pop up the file dialog). A same-origin fetch always sends Origin, so
        "present but mismatched" is refused."""
        o = self.headers.get("Origin")
        if o is None:
            return True
        host = self.headers.get("Host", "")
        return o in (f"http://{host}", f"https://{host}")

    def do_POST(self):
        p = urlparse(self.path).path
        if not self._same_origin():
            return self._json(dict(error="cross-origin request rejected"), 403)
        try:
            if p == "/fold":
                return self._fold()
            if p == "/pick-video":
                return self._pick()
            if p == "/render":
                return self._render()
            if p == "/render/cancel":
                return self._cancel()
            if p == "/score":
                return self._score()
        except Exception as ex:
            return self._json(dict(error=f"{type(ex).__name__}: {ex}"), 500)
        self.send_error(404)

    # ── Index page
    def _html(self):
        body = HTML.replace("__VERSION__", VERSION).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self._write(body)

    # ── Video streaming (Range support is required, or scrubbing breaks and
    # Safari may refuse to play at all)
    def _video(self):
        with STATE_LOCK:
            path = STATE["video"]
        if not path or not os.path.isfile(path):
            return self.send_error(404, "no video loaded")
        size = os.path.getsize(path)
        ctype = guess_type(path)
        rng = self.headers.get("Range")

        start, end = 0, size - 1
        partial = False
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng.strip())
            if m:
                s, e = m.group(1), m.group(2)
                if s:
                    start = int(s)
                    end = int(e) if e else size - 1
                elif e:                          # bytes=-N means the last N bytes
                    start = max(0, size - int(e))
                if start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
                end = min(end, size - 1)
                partial = True

        length = end - start + 1
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = length
                while left > 0:
                    chunk = f.read(min(256 * 1024, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # ── Scoring (single source of truth)
    def _fold(self):
        req = self._body()
        doc = req.get("doc") or {}
        opt = req.get("opt") or {}
        pl = plan(doc, opt)
        sc = pl["scoring"]
        res = dict(cur=sc["cur"], snaps=sc["snaps"], ok=pl["ok"], reason=pl["reason"])
        res["hlList"] = [{"from": round(s, 3), "to": round(t, 3)}
                         for s, t in pl.get("hl", [])]
        if pl["ok"]:
            span, total = pl["span"], pl["total"]
            res["cuts"] = dict(
                n=len(pl["cuts"]),
                seconds=round(span - total, 1),
                dropped=len(pl["dropped"]),
                outSeconds=round(total, 1),
                pct=round((span - total) / span * 100) if span > 0 else 0)
            res["cutList"] = [{"from": round(f, 3), "to": round(t, 3)}
                              for f, t, _ in pl["cuts"]]
            res["keepList"] = [{"from": round(s, 3), "to": round(t, 3)}
                               for s, t in pl["keeps"]]
        else:
            res["cuts"] = dict(n=0, seconds=0.0, dropped=0, outSeconds=0.0, pct=0)
            res["keepList"] = []
        return self._json(res)

    # ── Native file dialog
    def _pick(self):
        p = native_pick_video()
        if not p:
            return self._json(dict(cancelled=True))
        with STATE_LOCK:
            STATE["video"] = p
        info = probe(p, STATE["ffprobe"])
        return self._json(dict(
            path=p, name=os.path.basename(p),
            info=dict(w=info["w"], h=info["h"], fps=round(info["fps"], 2),
                      codec=info["codec"], duration=info["duration"],
                      bitrate=info["bitrate"]) if info else None,
            defaultOut=default_out(p)))

    # ── Render
    def _render(self):
        with STATE_LOCK:
            job = STATE["job"]
            video = STATE["video"]
            ffmpeg = STATE["ffmpeg"]
        if job and job.state == "running":
            return self._json(dict(error="A render is already running."), 409)
        if not video:
            return self._json(dict(error="No video loaded yet."), 400)
        if not ffmpeg:
            return self._json(dict(error="ffmpeg not found, cannot render."), 400)

        req = self._body()
        doc = req.get("doc") or {}
        opt = req.get("opt") or {}
        out = req.get("out") or default_out(video)
        out = os.path.abspath(out)
        scope = opt.get("scope") or "full"

        stem = os.path.splitext(out)[0]
        hl_out = (stem[:-4] if stem.endswith(".cut") else stem) + ".highlights.mp4"

        # One plan per output file; "both" renders the full match and the
        # highlight reel in sequence with one combined progress bar
        wanted = ([("full", out)] if scope == "full" else
                  [("highlights", hl_out)] if scope == "highlights" else
                  [("full", out), ("highlights", hl_out)])
        plans = []
        for sc_name, sc_out in wanted:
            pl = plan(doc, dict(opt, scope=sc_name))
            if not pl["ok"]:
                return self._json(dict(error=pl["reason"]), 400)
            plans.append((pl, sc_out))

        # Drop a copy of the tags next to the output, so a re-render or a
        # parameter change can always be reproduced
        try:
            with open(os.path.splitext(out)[0] + ".tags.json", "w",
                      encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        try:                     # and a score sheet next to it
            with open(os.path.splitext(out)[0] + ".score.txt", "w",
                      encoding="utf-8") as f:
                f.write("\n".join(score_report(plans[0][0], doc_names(doc), video)) + "\n")
        except Exception:
            pass

        logs, tasks = [], []
        for pl, sc_out in plans:
            cmd, workdir, _ = build_render(doc, pl, video, sc_out, opt, ffmpeg,
                                           STATE["ffprobe"], log=logs.append,
                                           progress=True)
            tasks.append((cmd, workdir, pl["total"]))
        grand = sum(pl["total"] for pl, _ in plans)
        new = Job(" + ".join(os.path.basename(o) for _, o in plans), grand)
        new.log = logs
        with STATE_LOCK:
            STATE["job"] = new
        threading.Thread(target=run_job, args=(new, tasks),
                         daemon=True).start()
        return self._json(dict(ok=True, out=new.out, total=round(grand, 1),
                               summary=summary_lines(plans[0][0], opt, video),
                               notes=logs))

    def _score(self):
        req = self._body()
        doc = req.get("doc") or {}
        pl = plan(doc, dict(req.get("opt") or {}, scope="full"))
        text = "\n".join(score_report(pl, doc_names(doc), doc.get("source") or "")) + "\n"
        return self._json(dict(text=text))

    def _cancel(self):
        with STATE_LOCK:
            job = STATE["job"]
        if job and job.state == "running" and job.proc:
            job.state = "cancelled"
            try:
                job.proc.terminate()
            except Exception:
                pass
        return self._json(dict(ok=True))


def default_out(video):
    return os.path.join(os.path.dirname(os.path.abspath(video)),
                        os.path.splitext(os.path.basename(video))[0] + ".cut.mp4")


def free_port(preferred=8770):
    for port in (preferred, 0):
        try:
            s = socket.socket()
            s.bind(("127.0.0.1", port))
            p = s.getsockname()[1]
            s.close()
            return p
        except OSError:
            continue
    return 8770


def lan_ip():
    """Best-effort local network address, for printing the --listen URL."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))          # no traffic is sent; just picks a route
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def serve(open_browser=True, port=None, ffmpeg_hint=None, listen=False):
    ff = find_ffmpeg(ffmpeg_hint)
    STATE["ffmpeg"] = ff
    if ff:
        probe_path = os.path.join(os.path.dirname(ff),
                                  "ffprobe.exe" if IS_WIN else "ffprobe")
        STATE["ffprobe"] = probe_path if os.path.isfile(probe_path) else "ffprobe"

    port = port or free_port()
    host = "0.0.0.0" if listen else "127.0.0.1"
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{port}/"

    print(f"\nttcut {VERSION}")
    print(f"UI        {url}")
    print(f"ffmpeg    {ff or 'not found -- tagging and JSON export work, rendering does not'}")
    if ff:
        hw = detect_hw_encoders(ff)
        print(f"HW encode {', '.join(hw) + ' (default, changeable in the UI)' if hw else 'none, using CPU libx264'}")
    if not ff:
        print("          Mac: brew install ffmpeg-full")
        print("          Windows: put ffmpeg.exe next to this script")
    if listen:
        ip = lan_ip()
        print(f"LAN       {'http://%s:%d/' % (ip, port) if ip else 'listening on all interfaces, port %d' % port}")
        print("\n! --listen exposes the UI to everyone on this network. Anyone who")
        print("  opens it can tag, pop up the file dialog on THIS machine, and start")
        print("  renders. Use it only on a network you trust. Ctrl-C to stop.\n")
    else:
        print("\nListening on 127.0.0.1 only, not reachable from outside. Ctrl-C to stop.\n")

    if open_browser:
        threading.Thread(target=lambda: (time.sleep(0.6), webbrowser.open(url)),
                         daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# ─────────────────────────────────────────── Command-line render (same behaviour as V1.22)

def join_videos(parts, out, ffmpeg_hint):
    """Losslessly concatenate rendered parts with ffmpeg's concat demuxer
    (stream copy, no re-encode). The parts must share resolution, frame rate
    and encoder settings -- which they do when rendered with the same
    quality options."""
    if len(parts) < 2:
        sys.exit("--join needs at least two files.")
    for pth in parts:
        if not os.path.isfile(pth):
            sys.exit(f"not found: {pth}")
    ffmpeg = find_ffmpeg(ffmpeg_hint, os.path.dirname(os.path.abspath(parts[0])))
    if not ffmpeg:
        sys.exit("ffmpeg not found.")
    out = out or os.path.join(os.path.dirname(os.path.abspath(parts[0])),
                              "match_full.mp4")
    out = os.path.abspath(out)
    lst = os.path.splitext(out)[0] + ".join.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for pth in parts:
            f.write("file '%s'\n" % os.path.abspath(pth).replace("'", r"'\''"))
    print(f"\nttcut {VERSION}")
    print(f"Joining   {len(parts)} parts (stream copy, no quality loss)")
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", "-movflags", "+faststart", out], check=True)
    try:
        os.remove(lst)
    except OSError:
        pass
    print(f"\nDone -> {out}")


def cli_render(args):
    doc = json.load(open(args.tags, encoding="utf-8-sig"))   # tolerate a Notepad BOM
    opt = dict(lead=args.lead, tail=args.tail, min_cut=args.min_cut,
               cut_lets=args.cut_lets, let_tail=args.let_tail,
               quality=args.quality, encoder=args.encoder, crf=args.crf,
               preset=args.preset, bitrate=args.bitrate, fps=args.fps,
               hdr=args.hdr, size=args.size, hwaccel=args.hwaccel, font=args.font,
               accent=args.accent,
               scope="highlights" if args.highlights else "full")

    pl = plan(doc, opt)
    out = args.out or default_out(args.video)
    if args.highlights and not args.out:
        out = os.path.splitext(out)[0]
        out = (out[:-4] if out.endswith(".cut") else out) + ".highlights.mp4"

    print(f"\nttcut {VERSION}")
    if not pl["ok"]:
        sys.exit(pl["reason"])
    for line in summary_lines(pl, opt, args.video)[:5]:
        print(line)
    print()
    for line in summary_lines(pl, opt, args.video)[5:]:
        print(line)
    if pl["dropped"]:
        print(f"\nSkipped {len(pl['dropped'])} cuts that were too short (keeping them beats a jump cut):")
        for f, t, why in pl["dropped"]:
            print(f"   {ts(f)} → {ts(t)}   {t - f:.2f}s   {why}")

    if args.dry_run:
        print("\nKept segments:")
        for i, (s, e) in enumerate(pl["keeps"]):
            print(f"   {i + 1:2d}  {ts(s)} → {ts(e)}   {e - s:6.2f}s")
        print()
        print("\n".join(score_report(pl, doc_names(doc), args.video)))
        print()
        return

    ffmpeg = find_ffmpeg(args.ffmpeg, os.path.dirname(os.path.abspath(args.video)))
    if not ffmpeg:
        sys.exit("\nffmpeg not found.\n"
                 "  Mac    : brew install ffmpeg-full\n"
                 "  Windows: put ffmpeg.exe next to this script, or point at it with "
                 "--ffmpeg \"C:\\ffmpeg\\bin\"")
    ffprobe = os.path.join(os.path.dirname(ffmpeg),
                           "ffprobe.exe" if IS_WIN else "ffprobe")
    if not os.path.isfile(ffprobe):
        ffprobe = "ffprobe"
    print(f"ffmpeg    {ffmpeg}")
    print()

    cmd, workdir, flt = build_render(doc, pl, args.video, out, opt,
                                     ffmpeg, ffprobe, log=print)
    print("\n" + " ".join(
        (c if len(c) < 60 else f"<filter graph, {len(c)} chars, see {flt}>") for c in cmd) + "\n")
    subprocess.run(cmd, check=True, cwd=workdir)
    sp = os.path.splitext(out)[0] + ".score.txt"
    with open(sp, "w", encoding="utf-8") as f:
        f.write("\n".join(score_report(pl, doc_names(doc), args.video)) + "\n")
    print(f"\nDone -> {out}")
    print(f"Score sheet -> {sp}")


def main():
    for stream in (sys.stdout, sys.stderr):      # the Windows console is not UTF-8 by default
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    p = argparse.ArgumentParser(
        description=f"ttcut {VERSION} — table tennis tagging and cutting. "
                    f"With no arguments it opens the interface.")
    p.add_argument("-v", "--version", action="version", version=f"ttcut {VERSION}")
    p.add_argument("tags", nargs="?", help="tags JSON (omit to open the interface)")
    p.add_argument("video", nargs="?", help="source video (omit to open the interface)")
    p.add_argument("-o", "--out", default=None)
    p.add_argument("--lead", type=float, default=None, help="seconds kept before each serve (defaults to the JSON)")
    p.add_argument("--tail", type=float, default=None, help="seconds kept after each point (defaults to the JSON)")
    p.add_argument("--min-cut", type=float, default=DEFAULT_MIN_CUT,
                   help="cuts shorter than this are left alone, to avoid pointless jump cuts")
    p.add_argument("--cut-lets", action="store_true", help="also cut the ball retrieval between lets")
    p.add_argument("--let-tail", type=float, default=1.5, help="seconds kept after a let")

    g = p.add_argument_group("quality")
    g.add_argument("--quality", choices=list(QUALITY), default="high",
                   help="fast, high (default), max (libx264 CRF, much slower)")
    g.add_argument("--encoder", default=None,
                   help="Mac: h264_videotoolbox / Windows: h264_nvenc, h264_qsv, "
                        "h264_amf / libx264 (pure CPU, best and slowest)")
    g.add_argument("--crf", type=int, default=None, help="override the quality value; lower is better")
    g.add_argument("--preset", default=None, help="libx264 preset")
    g.add_argument("--bitrate", default=None, help="override the bitrate, e.g. 40M")
    g.add_argument("--fps", default="source", help="source = follow the source, or give a number")
    g.add_argument("--hdr", choices=["auto", "tonemap", "keep", "ignore"], default="auto")
    g.add_argument("--size", default=None, help="override the resolution, e.g. 1920x1080")
    g.add_argument("--hwaccel", default="auto",
                   help="hardware decoding: auto (videotoolbox on Mac, off elsewhere) / none / cuda / qsv / d3d11va / dxva2")

    s = p.add_argument_group("interface")
    s.add_argument("--port", type=int, default=None, help="port to listen on")
    s.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    s.add_argument("--listen", action="store_true",
                   help="also accept connections from the local network, so other "
                        "devices on the same Wi-Fi can open the UI (trusted networks only)")

    p.add_argument("--accent", default=None,
                   help=f"scoreboard accent colour (point digits and side bar), "
                        f"e.g. \"#FF7A18\". Default {DEFAULT_ACCENT}")
    p.add_argument("--font", default=FONT_NAME, help="font name used for the scoreboard names")
    p.add_argument("--ffmpeg", default=None,
                   help="path to ffmpeg.exe or its folder (when it is not on PATH)")
    p.add_argument("--highlights", action="store_true",
                   help="render only the rallies marked as highlights (H key); "
                        "default output name becomes <source>.highlights.mp4")
    p.add_argument("--dry-run", action="store_true", help="print the cut list only, do not render")
    p.add_argument("--join", nargs="+", metavar="PART", default=None,
                   help="concatenate two or more rendered .cut.mp4 parts losslessly "
                        "(stream copy); combine with -o for the output name")
    args = p.parse_args()

    if args.join:
        join_videos(args.join, args.out, args.ffmpeg)
    elif args.tags and args.video:
        cli_render(args)
    elif args.tags or args.video:
        p.error("a command-line render needs both the tags JSON and the video; "
                "to open the interface, pass no arguments.")
    else:
        serve(open_browser=not args.no_browser, port=args.port,
              ffmpeg_hint=args.ffmpeg, listen=args.listen)


if __name__ == "__main__":
    main()
