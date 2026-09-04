**English** · [繁體中文](README.zh-TW.md)

# picklecut · ttcut

**Match video for pickleball and table tennis: tag the rallies, cut the dead time, burn in a live scoreboard, get a score sheet.** One pipeline, two scoring engines.

Based on **ttcut**, the table-tennis original by **MikaDD (Taiwan)**. The pickleball adaptation and everything since are by **deyugo**. Both tools ship here under the MIT licence with both copyright notices kept.

Drop in a full match recorded on your phone, press a key on every serve and every rally end, and the tool removes the dead time between rallies while overlaying a scoreboard that follows the score and the server. Out comes a tight, watchable video plus a point-by-point score sheet.

| Sport | 繁體中文 build | English build | Double-click launchers |
|---|---|---|---|
| Pickleball | `picklecut_v1_1.py` | `picklecut_v1_1_EN.py` | `picklecut.bat` / `.command`, `picklecut_EN.bat` / `.command` |
| Table tennis | `ttcut_v2_4.py` | `ttcut_v2_4_EN.py` | `ttcut.bat` / `.command`, `ttcut_EN.bat` / `.command` |

The two language builds of a tool share identical logic and interchangeable tags JSON; only the interface text differs (the test suite in `tests/` checks this). picklecut and ttcut are the same code with a different scoring engine plugged in, but their tags JSON is **not** interchangeable.

## Requirements

- **Python 3.8 or newer**
- **ffmpeg**, not bundled: `brew install ffmpeg` on Mac; on Windows drop `ffmpeg.exe` next to the script or point `--ffmpeg` at its folder ([ffmpeg.org](https://ffmpeg.org/download.html))
- A GPU is optional; hardware encoders are detected at startup (see *Output and GPU*)

## Getting started

```bash
python3 picklecut_v1_1_EN.py    # pickleball
python3 ttcut_v2_4_EN.py        # table tennis
```

Or double-click a launcher (Mac: `chmod +x name.command` once, or right-click → Open). Keep the console window open while you work; closing it stops the tool. A local server starts and your browser opens. **It binds to `127.0.0.1` only.**

1. Click **Load video**, or just **drag the video into the window** (tagging starts right away; the frame rate is estimated during 1× playback; a file dialog opens once at render time because browsers never reveal a dropped file's path). Dropping a `.tags.json` loads it as tags.
2. Fill in the names and who serves first. Pickleball: pick doubles/singles and the scoring system. Table tennis: pick singles/doubles.
3. Play. Press `S` on every serve, `A` or `B` for whoever **wins the rally**. Pickleball works out whether that is a point or a side-out; table tennis scores a point.
4. The right panel shows the running score (pickleball also the official call, e.g. `5–3–2`) and the cut statistics.
5. Render. Next to the source you get `<name>.cut.mp4`, `<name>.tags.json` (the tags) and `<name>.score.txt` (the score sheet).

> **Refreshing the browser clears your tags.** Hit **Export JSON** partway through a long match.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `←` `→` / `Shift` + `←` `→` / `Alt` + `←` `→` | Step one second / five seconds / one frame |
| `S` | Tag a serve |
| `A` / `B` | Rally won by A / B |
| `H` | Mark the current rally as a highlight |
| `N` | New game |
| `Z` | Undo the last tag |
| `1` `2` `3` `4` | Playback speed 0.5× / 1× / 1.5× / 2× |

Shortcuts do not fire while the cursor is in a text field, but they keep working after you use the scrub bar, the speed buttons or a checkbox.

## Fixing mistakes

A LosslessCut-style strip under the transport shows what the render will keep: **bright = kept, dark = cut, gold = highlighted rallies**, ticks = serves, white line = playhead. Click to jump. Nothing ever needs re-tagging from scratch:

- **Move a tag**: the `⟲` button on an event row moves it to the current playback position. **Delete**: `×`.
- **Update the score by hand**: the *fix* bar under the scoreboard inserts a correction at the current time. Fill in only what you want to change (games, points, serving side, and in doubles the player number) and scoring continues from there. Use it after a recording gap, a mis-tag, or to set the game count mid-match. Corrections are `adjust` events in the JSON and appear in the score sheet.
- **Resume later**: load an exported `.tags.json` (button or drag-and-drop); events, captions, highlights, corrections and settings all come back editable.

Anything you do not tag is simply cut: a timeout, a lens blocked for a minute, the camera left running during a break, everything before the first serve and after the last rally. What the tool cannot do is skip a stretch *inside* one rally.

## Highlights and captions

Press `H` during (or right after) a rally to mark it. The **render scope** select offers **Full match**, **Highlights only** (marked rallies, scoreboard included, output `<name>.highlights.mp4`) or **Full + highlights** (both files, one progress bar). On the command line, `--highlights`.

Type a line in the caption bar and press **+ Cap** (or Enter): it is burned in bottom-centre from the current position for the chosen seconds (default 3), stored as a `caption` event, and re-timed across the cuts; a caption that falls entirely inside a cut is dropped.

## Score sheet

Every render also writes `<name>.score.txt`: the result of each game, the games tally, and a point-by-point log with the source time, game number, who served (`A#2` in doubles), who won the rally, the running score, side-outs (pickleball) and a ★ on highlighted rallies. Corrections and manual new-game events are listed too. The **Export score** button downloads the same text without rendering; `--dry-run` prints it after the cut table.

## Scoring rules

**Pickleball (picklecut)**

- **Side-out scoring** (default): only the serving side scores. Doubles starts each game on server #2 (the **0-0-2** start); a lost rally moves the serve from #1 to #2, then side-out. Singles side-out is immediate. A game can only end on a serving-side rally win. The scoreboard marks the server with one dot (#1) or two (#2); the UI shows the three-number call.
- **Rally scoring**: every rally scores; the winner serves next. (Generic rules; MLP extras like the freeze are not implemented.)
- **Doubles / singles**, and a **starting server number** (#1 / #2) for a video that picks up a doubles game mid-way.

**Table tennis (ttcut)**

- Two serves each, one each once both sides reach 10 (deuce); a game ends at the target with a two-point lead, or at the cap.
- **Doubles**: switch it on and the scoreboard shows which player of the pair serves (● = the first-named player, ●● = the second). Players alternate each time their pair gets the serve; every game restarts at #1. The receiver swap at 5 in a deciding game is not automatic; enter it with the fix bar's `#`.
- A correction that names the server restarts the two-serve rotation from that point.

**Both**: points per game (11 by default; 15 or 21), win by 2 or capped, starting game count, handicap (every game or the first only). Scoring is implemented once in Python; the interface and the render call the same function.

## Cutting rules

The gap between the end of a rally and the next serve is what gets removed.

| Setting | Default | What it does |
|---|---|---|
| Hold after rally | 1.0 s | Keep a moment after the rally ends |
| Hold before serve | 0.3 s | Keep a moment before the next serve |
| Minimum cut | 2.0 s | Shorter gaps are left alone (no pointless jump cuts) |
| Cut replays / lets | off | Also cut the dead time between two consecutive serves |
| Hold after replay / let | 1.5 s | Only when the setting above is on |

picklecut calls a repeated serve a *replay* (`--cut-replays` / `--replay-tail`), ttcut a *let* (`--cut-lets` / `--let-tail`).

## Matches split across videos

1. Cut the first file as usual and export its tags JSON; load it into the next session to carry names, format and colours over.
2. For the next file set the **starting games**; if it starts mid-game, set the **handicap** to the score at that moment with scope *first game*, the **first server**, and (pickleball doubles) the **server number**. Or simply insert a correction at the start.
3. Render every part with the same quality settings, then join losslessly (stream copy, no re-encode):

```bash
python3 picklecut_v1_1_EN.py --join game1.cut.mp4 game2.cut.mp4 -o match.mp4
```

## Output and GPU

| Quality | Scale | CRF | preset | Notes |
|---|---|---|---|---|
| `fast` | 0.70× | 21 | veryfast | Draft, to check the cuts |
| `high` | 1.00× | 18 | medium | Default; source resolution |
| `max` | 1.40× | 16 | slow | Always CPU `libx264`; slowest and best |

Frame rate follows the source; HDR is tone-mapped to SDR. At startup the tool test-encodes a few frames with each hardware encoder available (NVENC, Quick Sync, AMF on Windows; VideoToolbox on Mac) and the first one that works becomes the default; the console prints it and the **encoder** select next to quality lets you pick another or CPU `libx264`. A discrete NVIDIA/AMD card is several times faster than the CPU at 1080p60; an Intel iGPU on a strong desktop CPU is about a wash. Hardware *decoding* (`--hwaccel`) is on by default only on Mac; on Windows it tends to slow 4K down because every frame is copied back for the overlay.

## Command line

With a tags JSON in hand you can render without the interface (same flags for ttcut):

```bash
python3 picklecut_v1_1_EN.py match.tags.json match.MOV                       # render
python3 picklecut_v1_1_EN.py match.tags.json match.MOV -o final.mp4 --quality max
python3 picklecut_v1_1_EN.py match.tags.json match.MOV --dry-run             # cut table + score sheet, no render
python3 picklecut_v1_1_EN.py match.tags.json match.MOV --highlights          # highlight reel
```

<details>
<summary>Flags</summary>

| Flag | Description |
|---|---|
| `-o, --out` | Output path; default `<source>.cut.mp4` |
| `--lead` / `--tail` | Seconds held before the serve / after the rally (default: from the JSON) |
| `--min-cut` | Minimum cut length, default 2.0 s |
| `--cut-replays` / `--replay-tail` | Also cut between consecutive serves / seconds held after a replay (ttcut: `--cut-lets` / `--let-tail`) |
| `--quality` | `fast` / `high` / `max`, default `high` |
| `--encoder` | Encoder; default is the first hardware encoder that passes the startup test, else `libx264` |
| `--crf` / `--preset` / `--bitrate` | Override quality value / libx264 preset / bitrate (e.g. `40M`) |
| `--fps` / `--size` | `source` or a number / e.g. `1920x1080` |
| `--hdr` | `auto` / `tonemap` / `keep` / `ignore` |
| `--hwaccel` | `auto` (VideoToolbox on Mac, off elsewhere) / `none` / `cuda` / `qsv` / `d3d11va` / `dxva2` |
| `--accent` / `--font` | Scoreboard accent colour (wins over the JSON) / font name |
| `--ffmpeg` | Folder containing ffmpeg |
| `--port` / `--no-browser` / `--listen` | Port / do not open a browser / also accept local-network connections |
| `--highlights` | Render only the rallies marked with `H`; output `<source>.highlights.mp4` |
| `--join PART...` | Losslessly concatenate rendered parts; use with `-o` |
| `--dry-run` | Print the cut table and the score sheet, render nothing |

</details>

## Tags JSON

Plain JSON: portable, diffable, editable by hand. Tag on a Mac, render on Windows.

```json
{
  "version": 3, "generator": "picklecut V1.1-EN", "source": "IMG_1496.MOV", "fps": 30,
  "sport": "pickleball",
  "players": { "A": "Team A", "B": "Team B" }, "firstServer": "A",
  "format": { "pointsPerGame": 11, "deuce": "standard", "cap": 12, "scoring": "sideout", "side": "doubles" },
  "start": { "games": { "A": 0, "B": 0 }, "points": { "A": 0, "B": 0 }, "handicapScope": "every" },
  "pads": { "tail": 1.0, "lead": 0.3 }, "scoreboard": { "accent": "#BFD730" },
  "events": [
    { "t": 12.400, "frame": 372, "type": "serve" },
    { "t": 15.000, "frame": 450, "type": "highlight" },
    { "t": 18.933, "frame": 568, "type": "point", "winner": "A" },
    { "t": 20.000, "frame": 600, "type": "caption", "text": "Match point", "dur": 3 },
    { "t": 45.100, "frame": 1353, "type": "game" },
    { "t": 46.000, "frame": 1380, "type": "adjust", "games": { "A": 1 }, "server": "B", "serverNum": 2 }
  ]
}
```

Six event types. `serve`, `point` (with `winner`, the side that won the rally) and `game` shape the cuts and the score; `highlight`, `caption` (`text`, `dur`) and `adjust` (any of `games`, `points`, `server`, `serverNum`) ride along. ttcut writes `version` 2 without `sport`, `format.scoring` or `start.serverNum`; its `format.side` is `singles` or `doubles`.

## Sharing

- **Local network**: start with `--listen` and the console prints a LAN URL that any phone or laptop on the same Wi-Fi can open; the video, the file dialog and the render stay on the host. **Trusted networks only.** An internet-hosted version is deliberately out of scope.
- **Standalone executables**: `build_exe.bat` / `build_exe.sh` (needs `pip install pyinstaller`) build all four tools into `dist/`; ship each exe with an ffmpeg binary in the same folder. Antivirus products often delete fresh PyInstaller exes during the build; add the folder to the exclusions first. Build each platform on that platform.

## Troubleshooting

- **The video does not show in the browser**: probably HEVC. Chrome cannot preview it; Safari can (and gives hardware 4K decoding on a Mac).
- **macOS warns that libass cannot find a PingFang font path**: harmless.
- **Windows says tkinter is missing**: the file dialog cannot open; render from the command line or install a Python that includes tkinter.
- **ffmpeg not found**: you can still tag and export JSON. Install ffmpeg or use `--ffmpeg`, then restart.
- **Rendering is slow**: check the `HW encode` line in the console or the encoder select. `fast` quality is the quickest CPU option; on a strong CPU an Intel iGPU brings no gain; leave `--hwaccel` off on Windows.
- **Output looks worse than the source**: the tool warns before rendering when the target bitrate is below the source; use `--bitrate` or `--quality max`.

## Versions

Small changes bump by 0.1; architectural or output-format changes bump the whole number. Full changelogs live in each script's docstring.

- **picklecut V1.1** (2026-09-02): drag & drop, 1 s / 5 s / frame arrow keys, captions, timeline, corrections and per-event retime, highlights and render scopes, starting server number, `--join`, hardware-encoder detection with an encoder select, score sheet. **V1** (2026-08-31): first pickleball version, adapted from ttcut V2.2.
- **ttcut V2.4** (2026-09-02): every sport-independent feature of picklecut V1.1 ported back, plus doubles with per-player serve dots and the score sheet. Table-tennis scoring itself is unchanged since V2.2.

## Other racket sports

Only the scoring engine is sport-specific. Badminton is already expressible in picklecut (rally scoring, 21 points, cap 30). Tennis and padel need a new scoring fold and a sets column; planned, not implemented. See `docs/2026-08-31-pickleball-adaptation-design.md`.

## Licence

MIT, see [LICENSE](LICENSE). The original ttcut is copyright MikaDD (Taiwan); the pickleball adaptation and later versions of both tools are copyright deyugo. The tools call ffmpeg as an external program and **neither contain nor distribute ffmpeg**; it is licensed separately. Written with the assistance of Anthropic Claude.

---

Copyright (c) 2026 MikaDD (Taiwan), original ttcut  
Copyright (c) 2026 deyugo, pickleball adaptation and later versions
