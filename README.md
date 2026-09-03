**English** · [繁體中文](README.zh-TW.md)

# picklecut

**Pickleball match video: tag the rallies, cut the dead time, burn in a persistent scoreboard that knows side-out scoring. One tool, start to finish.**

Drop in a full match recorded on your phone, tag each serve and each rally, and picklecut removes the dead time between rallies while overlaying a scoreboard that tracks the score, the serving team and the server number (#1/#2) as the match goes on. Out comes a tight, watchable video.

Adapted from [ttcut](https://github.com/) (the table-tennis original); the cutting and rendering pipeline is the same, the scoring engine is pickleball's.

---

## Requirements

- **Python 3.8 or newer**
- **ffmpeg** — not bundled, install it yourself

```bash
# macOS
brew install ffmpeg

# Confirm the subtitles filter is present (the scoreboard needs it)
ffmpeg -filters | grep subtitles
```

On Windows, drop `ffmpeg.exe` next to the script, or point `--ffmpeg` at the folder containing it. Get it from [ffmpeg.org](https://ffmpeg.org/download.html).

A GPU is optional. Hardware encoders (NVENC, Quick Sync, AMF, VideoToolbox) are detected at startup and used automatically when one works — see *Output settings*.

## Getting started

```bash
python3 picklecut_v1_1_EN.py
```

The tool starts a local server and opens your browser. **It binds to `127.0.0.1` only and is not reachable from the network.**

1. Click **Load video** at the top left — or just **drag the video file into the window** (tagging starts right away; the frame rate is auto-estimated during 1× playback, and the file dialog opens once at render time to confirm where the file lives, since browsers never reveal a dropped file's path). Dropping a `.tags.json` loads it as tags.
2. Fill in both team names and who serves first; pick doubles/singles and the scoring system; check the frame rate
3. Play the video. Press `S` on every serve, `A` or `B` for whoever **wins the rally** — the tool works out whether that's a point or a side-out
4. The panel on the right shows the running score, the official call (e.g. `5–3–2`) and cut statistics as you go
5. Hit render. The result lands next to the source video as `<name>.cut.mp4`, together with `<name>.tags.json` (the tags) and `<name>.score.txt` (the score sheet)

> **Refreshing the browser clears your tags.** The video path and any render in progress survive a reload, but the tagged events do not. On a long match, hit **Export JSON** partway through.

## For non-programmers

Three ways to skip the terminal, from lightest to heaviest:

**Double-click launchers** (in this repo): once Python and ffmpeg are installed on the machine, `picklecut_EN.bat` (Windows) or `picklecut_EN.command` (Mac) starts the English build with a double-click; `picklecut.bat` / `picklecut.command` start the Chinese build. Keep the console window open while using the tool — closing it stops the server. On Mac, run `chmod +x picklecut_EN.command` once (or right-click → Open the first time).

**Standalone executable** (no Python install at all): run `build_exe.bat` (Windows) or `build_exe.sh` (Mac) — they need `pip install pyinstaller` once — and share the resulting `dist/` executable together with an `ffmpeg` binary in the same folder. The person you give it to just double-clicks. Two caveats: antivirus products often flag fresh PyInstaller exes as false positives and may silently delete them during the build — add the project folder to the AV exclusions before building — and each platform builds its own executable (build the Mac one on a Mac).

**Sharing over the local network**: start with `--listen` and the console prints a LAN URL (e.g. `http://192.168.1.20:8770/`) that anyone on the same Wi-Fi can open from their phone or laptop — no install on their side at all. The video, the file dialog and the render all live on the host machine. **`--listen` exposes the UI to everyone on the network; use it only on networks you trust.** A true internet-hosted version is deliberately out of scope: it would mean uploading multi-gigabyte match videos to a server, which this tool's local-first design exists to avoid.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `←` `→` | Step one second |
| `Shift` + `←` `→` | Step five seconds |
| `Alt` + `←` `→` | Step one frame |
| `S` | Tag a serve |
| `A` | Rally won by A |
| `B` | Rally won by B |
| `H` | Mark the current rally as a highlight |
| `N` | New game |
| `Z` | Undo the last tag |
| `1` `2` `3` `4` | Playback speed 0.5× / 1× / 1.5× / 2× |

Shortcuts do not fire while the cursor is in a text field, so you can type names freely — but they DO keep working after you use the scrub bar, the speed buttons or a checkbox.

## Timeline and fixing mistakes

A LosslessCut-style strip sits under the transport: **bright = kept, dark = cut, gold = highlighted rallies**, thin ticks = serves, white line = playhead. Click anywhere on it to jump. It updates live as you tag or change settings, so you always see exactly which segments the render will keep.

Nothing ever requires re-tagging from scratch:

- **Move a tag**: every event row has a `⟲` button that moves that tag to the current playback position.
- **Delete a tag**: the `×` button, as before.
- **Correct the score**: the *fix* bar under the scoreboard inserts a correction at the current time — fill in only the fields you want to change (games, points, serving side, server #) and scoring continues from there. This is also how you set the game count manually mid-match. Corrections are stored in the JSON as `adjust` events.
- **Resume later**: load an exported `.tags.json` (button or drag-and-drop) and everything — events, captions, highlights, corrections, settings — comes back editable.

## Highlights

Press `H` during a rally (or right after it ends) to mark it. The **render scope** selector next to quality then offers: **Full match** (default), **Highlights only** (just the marked rallies, scoreboard included — output `<name>.highlights.mp4`), or **Full + highlights**, which renders both files in one go with a single combined progress bar. On the command line, `--highlights` renders the highlight reel from a tags JSON.

## Captions

Type a line in the caption bar above the event list and press **+ Cap** (or Enter): the text is burned into the output, bottom-centre, starting at the current playback position for the chosen number of seconds (default 3). Captions live in the tags JSON as `caption` events (`{"t": 12.4, "type": "caption", "text": "…", "dur": 3}`), appear in the event list where they can be deleted like any tag, and are re-timed automatically across the cuts — a caption that falls entirely inside a removed segment is dropped.

## Score sheet

Every render also writes `<name>.score.txt` next to the video: the result of each game (11–7, 9–11 …), the games tally, and a point-by-point log with the source time, the game number, who served (`A#2` in doubles), who won the rally, the running score, side-outs and a ★ on highlighted rallies. Corrections and manual new-game events appear in the log too, so the sheet explains every number on the scoreboard. The **Export score** button in the header downloads the same text without rendering, and `--dry-run` prints it after the cut table.

## Cutting rules

The gap between the end of a rally and the next serve is dead time — retrieving the ball, rotating positions, the ritual glare at your partner. That gap is what picklecut removes.

| Setting | Default | What it does |
|---|---|---|
| Hold after rally | 1.0 s | How long to keep after the rally ends, so the ball finishes its bounce on screen |
| Hold before serve | 0.3 s | How long to keep before the next serve, so the cut does not feel clipped |
| Minimum cut | 2.0 s | Anything shorter than this is left alone, to avoid pointless jump cuts |
| Cut replays | off | When on, the dead time before a replayed serve is cut too |
| Hold after replay | 1.5 s | Only applies when the setting above is on |

## Scoring rules

Everything is customizable in the interface and stored in the tags JSON:

- **Side-out scoring** (default — the traditional / USA Pickleball rec system): only the serving side scores. In doubles, each game starts with the first-serving team on server #2 (the **0-0-2** start); a lost rally moves the serve from server #1 to #2, then side-out to the other team. In singles a lost rally is a straight side-out. A game can only end on a rally won by the serving side. The scoreboard marks the serving team with one accent dot (server #1) or two (server #2), and the UI shows the official three-number call.
- **Rally scoring**: every rally scores a point for its winner, and the winner serves next. (This is the generic rally system — MLP-specific extras like the freeze are not implemented.)
- **Doubles / singles** toggle
- **Points per game** — 11 by default; type 15 or 21 for tournament formats
- **Win by 2** (standard) or **capped** — first to the cap takes the game
- **Starting game count** — for when each game is its own file and you are continuing a match
- **Handicap** — set a starting score for either side, applied either every game or only the first
- **Starting server number** — `#1 / #2 · continuing` next to the first-serve selector, for a video that picks up a doubles game mid-way

Scoring is implemented once, in Python. The interface and the final render call the same function, so the two can never disagree about the score.

## Matches split across multiple videos

When one match spans several files, cut each file separately and join the results:

1. **Video 1**: tag and render as usual. Export the tags JSON too — loading it into the next session carries the names, format and colours over.
2. **Video 2**: set **games** to the game count where the video starts. If it starts mid-game, set the **handicap** to the score at that moment with scope **first game**, set **first serve** to the side serving, and pick the **server number** (#1/#2) next to it. The scoreboard and score calls then continue seamlessly.
3. Render every part with the **same quality settings**, then join them losslessly:

```bash
python3 picklecut_v1_1_EN.py --join game1.cut.mp4 game2.cut.mp4 -o match.mp4
```

`--join` is a stream copy — no re-encode, no quality loss — which is why the parts must share resolution, frame rate and encoder settings (they do when rendered by this tool with the same options from the same camera).

## Output settings

| Quality | Scale | CRF | preset | Notes |
|---|---|---|---|---|
| `fast` | 0.70× | 21 | veryfast | Draft, for checking that the cuts land right |
| `high` | 1.00× | 18 | medium | Default; keeps the source resolution |
| `max` | 1.40× | 16 | slow | Forces software encoding — slowest and best |

Frame rate follows the source by default. HDR sources are tone-mapped to SDR by default.

**GPU encoding.** At startup the tool test-encodes a few frames with each hardware encoder ffmpeg offers on this platform — NVENC (NVIDIA), Quick Sync (Intel) and AMF (AMD) on Windows, VideoToolbox on Mac — and the first one that actually works becomes the default encoder. The console prints what was found, and the **encoder** select next to quality offers the same choice (auto / each working hardware encoder / CPU `libx264`). `--encoder` on the command line overrides it; `max` quality always uses `libx264`. What to expect: a discrete NVIDIA or AMD card is several times faster than the CPU at 1080p60; an Intel iGPU on a strong desktop CPU is about a wash (it mainly lowers CPU load) and clearly faster only against a weak laptop CPU. Hardware *decoding* (`--hwaccel`) is on by default only on Mac; on Windows it tends to slow 4K renders down, because every frame is copied back for the scoreboard overlay, so leave it off unless you have measured a gain.

## Command line

With a tags JSON already in hand, you can skip the interface and render directly:

```bash
# Basic
python3 picklecut_v1_1_EN.py match.tags.json match.MOV

# Choose the output path and quality
python3 picklecut_v1_1_EN.py match.tags.json match.MOV -o final.mp4 --quality max

# Print the cut table without rendering, to sanity-check the cut points
python3 picklecut_v1_1_EN.py match.tags.json match.MOV --dry-run
```

<details>
<summary>Full flag list</summary>

| Flag | Description |
|---|---|
| `-o, --out` | Output path; defaults to `<source>.cut.mp4` |
| `--lead` / `--tail` | Seconds held before the serve / after the rally; read from the JSON by default |
| `--min-cut` | Minimum cut length in seconds, default 2.0 |
| `--cut-replays` | Also cut the dead time before a replayed serve |
| `--replay-tail` | Seconds held after a replayed serve, default 1.5 |
| `--quality` | `fast` / `high` / `max`, default `high` |
| `--encoder` | Pick the encoder explicitly. Default: the first hardware encoder that passes a test encode at startup (NVENC / Quick Sync / AMF / VideoToolbox), else `libx264`; `--quality max` always uses `libx264`. The UI has the same choice in its encoder select |
| `--crf` | Override the quality value; lower is better |
| `--preset` | libx264 preset |
| `--bitrate` | Override the bitrate, e.g. `40M` |
| `--fps` | `source` to follow the input, or a number |
| `--size` | Override the resolution, e.g. `1920x1080` |
| `--hdr` | `auto` / `tonemap` / `keep` / `ignore` |
| `--hwaccel` | Hardware decoding: `auto` (VideoToolbox on Mac, off elsewhere) / `none` / `cuda` / `qsv` / `d3d11va` / `dxva2` |
| `--accent` | Scoreboard accent colour; wins over the value in the JSON |
| `--font` | Scoreboard font name |
| `--ffmpeg` | Folder containing ffmpeg |
| `--port` | Pick the port |
| `--no-browser` | Do not open a browser automatically |
| `--listen` | Also accept connections from the local network (trusted networks only) |
| `--highlights` | Render only the rallies marked with `H`; default output `<source>.highlights.mp4` |
| `--join PART...` | Losslessly concatenate rendered parts (stream copy); use with `-o` |
| `--dry-run` | Print the cut table, render nothing |

</details>

## Tags JSON format

The exported file is plain JSON — portable, diffable, and editable by hand. Tag on a Mac and render on Windows with the same file; that works.

```json
{
  "version": 3,
  "generator": "picklecut V1.1-EN",
  "source": "IMG_1496.MOV",
  "fps": 30,
  "sport": "pickleball",
  "players": { "A": "Team A", "B": "Team B" },
  "firstServer": "A",
  "format": { "pointsPerGame": 11, "deuce": "standard", "cap": 12,
              "scoring": "sideout", "side": "doubles" },
  "start": {
    "games":  { "A": 0, "B": 0 },
    "points": { "A": 0, "B": 0 },
    "handicapScope": "every"
  },
  "pads": { "tail": 1.0, "lead": 0.3 },
  "scoreboard": { "accent": "#BFD730" },
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

There are six event types. Three shape the cuts and the score: `serve`, `point` (which carries a `winner` — the side that **won the rally**, whether or not that produced a point on the board) and `game`. Three ride along without touching the cuts: `highlight` (marks the rally it falls in for the highlight reel), `caption` (`text` plus `dur` seconds, burned in bottom-centre and re-timed across cuts) and `adjust` (a score correction — any of `games`, `points`, `server`, `serverNum`, overriding only the fields present). A matching `.tags.json` is also written next to the rendered video.

## Language versions

| File | Interface language |
|---|---|
| `picklecut_v1_1_EN.py` | English |
| `picklecut_v1_1.py` | Traditional Chinese |

**The two builds share identical scoring, cutting and rendering logic** — only the interface text and code comments differ. Tags JSON is interchangeable: tag with one build and render with the other, in either direction. The generated scoreboard `.ass` files are byte-identical apart from a single version comment line. The test suite in `tests/` checks exactly this.

## Troubleshooting

**The video will not display in the browser, but the file is fine**
The source is probably HEVC. Chrome cannot preview HEVC; Safari can. On a Mac, tagging in Safari is the better choice anyway — you get native 4K H.264 hardware decoding.

**macOS warns that libass cannot find a PingFang font path**
Harmless, ignore it. The font is found in AssetsV2 and the scoreboard renders correctly.

**Windows says tkinter is missing**
Some Python installs ship without tkinter, so the file dialog cannot open. Render from the command line instead, or install a Python distribution that includes tkinter.

**ffmpeg not found**
The interface says so on startup. You can still tag and export JSON, you just cannot produce a finished video. Install ffmpeg or point `--ffmpeg` at it, then restart.

**Rendering is slow**
Check the `HW encode` line in the console (or the encoder select in the UI). If it says none, no hardware encoder passed the startup test and the CPU is doing the work — `fast` quality is the quickest CPU option. If a hardware encoder was found but rendering is still slow, try CPU `libx264` in the select; on a strong CPU an Intel iGPU brings no speed gain. Leave `--hwaccel` off on Windows.

**The output looks worse than expected**
If the target bitrate falls below the source, the tool prints a warning before rendering along with a suggested value. Override it with `--bitrate` or `--quality max`. If the source itself was recorded at a low bitrate, quality is capped by the recording and there is nothing to be done about it here.

## Versions

Small changes bump by 0.1; architectural or output-format changes bump the whole number. The full changelog lives in the docstring at the top of the script.

- **V1.1** — Drag & drop loading; arrow keys step 1 s (Shift 5 s / Alt frame) and survive scrub-bar focus; burned-in captions; LosslessCut-style timeline; score-correction events and per-event retime; highlight marking with full/highlights/both render scopes; starting server number for multi-video matches; `--join`; hardware-encoder detection at startup with an encoder select in the UI; `--hwaccel qsv` no longer crashes ffmpeg; score sheet (`.score.txt`) written on every render, plus an Export score button
- **V1** — First pickleball version, adapted from ttcut V2.2: side-out and rally scoring, doubles server numbers, score calls, serve dots on the scoreboard

## Table tennis (ttcut)

The original table-tennis tool this project descends from ships in this repo too, upgraded to **ttcut V2.4**: `ttcut_v2_4_EN.py` (English) and `ttcut_v2_4.py` (繁體中文), with launchers `ttcut_EN.bat` / `ttcut.bat` / `.command`, executables from the same `build_exe` scripts, and `--listen`. Since V2.4 the two tools are one code base with a different scoring engine plugged in: everything sport-independent — drag & drop, the timeline, captions, highlights, score corrections, `--join`, GPU detection — is in both.

What differs:

- **Scoring engine.** ttcut: two serves each, one each from deuce (10–10 by default), a game ends at the target with a two-point lead or at the cap. picklecut: side-out or rally scoring, singles/doubles, server numbers, the 0-0-2 start. Table-tennis **doubles**: switch **Doubles** on in ttcut and the scoreboard marks which player of the pair serves (● = the first-named player, ●● = the second); the players alternate each time their pair gets the serve, and every game restarts at #1. The receiver swap at 5 in a deciding game is not automatic — enter it with the correction bar's `#`.
- **Scoreboard and UI.** Both scoreboards have a serve-dot column. ttcut has only the singles/doubles switch — no scoring-system select, no score call. Its correction bar sets games, points, the serving side and (in doubles) the player number; naming a server restarts the two-serve rotation from that point.
- **Wording and flags.** "Point A/B" instead of "A/B wins the rally", lets instead of replays (`--cut-lets` / `--let-tail`), orange accent by default.
- **Tags JSON.** ttcut writes `version` 2 without `sport`, `format.scoring`, `format.side` or `start.serverNum`. The two formats are **not** interchangeable: picklecut would read a ttcut file under side-out rules, and ttcut ignores the pickleball fields.

## Other racket sports

The scoring engine is the only sport-specific part of the pipeline. Badminton is rally scoring with a target of 21 (already expressible with today's knobs: rally + 21 + cap 30). Tennis and padel need a new scoring fold and a sets column on the scoreboard — planned, not yet implemented. See `docs/2026-08-31-pickleball-adaptation-design.md`.

## Licence

MIT — see [LICENSE](LICENSE).

This tool calls ffmpeg as an external program. It **neither contains nor distributes ffmpeg itself**. ffmpeg is licensed separately; get it from official sources.

Written with the assistance of Anthropic Claude.

---

Copyright (c) 2026 MikaDD (Taiwan)
