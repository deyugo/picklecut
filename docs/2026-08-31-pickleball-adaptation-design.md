# picklecut — adapting ttcut to pickleball (and later, other racket sports)

Date: 2026-08-31 · Status: implemented (V1); verification results at the bottom held

## Goal

Turn this repo's ttcut V2.2 (table-tennis rally tagger + cutter + burned-in
scoreboard) into **picklecut V1**, a pickleball tool, with the internal seams
placed so badminton / tennis / padel can be added later. Table tennis remains
the upstream ttcut project; this repo becomes pickleball-first.

## Decisions (confirmed with KC 2026-08-31)

1. **Scoring**: support BOTH traditional side-out scoring (default) and rally
   scoring, selectable in the UI and stored in the tags JSON. All scoring
   parameters customizable: game target (11/15/21, free entry), win-by-2 vs
   capped, singles vs doubles, first server, starting games, handicap.
2. **Doubles**: two team rows on the scoreboard (no 4-name tracking). Serving
   team marked with accent dots — one dot = server #1, two dots = server #2.
   Tagging stays two keys (A / B = which side won the rally).
3. **Scope**: rename the tool to picklecut V1 (`picklecut_v1_EN.py`,
   `picklecut_v1.py`). Internally, sport-specific logic is isolated so a new
   sport = a new fold variant + terminology strings.

## Rules implemented

### Side-out mode (traditional, USA Pickleball rec standard)

- Only the serving side scores. A rally won by the receiving side scores
  nothing; it moves the serve.
- **Doubles**: each game starts with the first-serving team on server #2
  (the "0-0-2" start — that team gets only one server turn). Serving team
  wins the rally → +1 point, same server continues. Serving team loses →
  server #1 hands to server #2; server #2 loses → side-out, other team
  starts at server #1.
- **Singles**: server scores on won rallies; lost rally = side-out, no point.
- A game can only END on a point, i.e. on a rally won by the serving side.
- Game to `target` (default 11), win by 2; or capped (first to cap wins).
- First server alternates between games; doubles restarts at server #2.
- Official score call shown in the UI: `serving–receiving–server#` (doubles),
  `serving–receiving` (singles).

### Rally mode

- Every rally scores a point for its winner; the winner serves the next
  rally. No server numbers (the dot marks the serving side only).
- This is deliberately the *generic* rally system — it is also the badminton
  core. MLP-specific extras (freeze at game point, etc.) are out of scope for
  V1 and documented as such in the README.

### Unchanged from ttcut

- Event model: `serve`, `point` (semantics now "rally ended, won by X" —
  the engine decides point vs side-out), `game`. Cut = gap from rally end
  (+tail) to next serve (−lead); consecutive serves = "replay" (was "let"),
  optionally cut too.
- Handicap / starting games / starting points knobs.
- Everything downstream of the fold: cut planning, ffmpeg render, HTTP
  server, native file dialog, CLI.

## Code changes (per file)

`picklecut_v1_EN.py` (copy of `ttcut_v2_2_EN.py`, then):

1. **Header/branding**: docstring, `VERSION = "V1-EN"`, server_version,
   argparse text, printed banners, `-metadata comment=picklecut ...`,
   generator string, HTML `<title>`/brand.
2. **Scoring** (`fold_full`): rewritten as above. `fmt` gains
   `scoring: 'sideout'|'rally'` and `doubles: bool`. State tuples grow to
   `(t, gA, gB, a, b, server, serverNum)`. `snaps` entries gain
   `scored`, `srv`, `srvNum` for the event list and score call.
   `read_format` reads `format.scoring` / `format.side` with defaults
   (`sideout`, `doubles`).
3. **Scoreboard** (`build_ass`): consume 7-field states; draw ● (server #1 /
   singles / rally) or ●● (doubles server #2) in the accent colour in a
   narrow strip right of the points column (panel widened accordingly).
4. **UI (embedded HTML/JS)**: team name fields default "Team A/B"; new
   side (Doubles/Singles) and scoring (Side-out/Rally) selects in the
   setbar; boardmeta shows score call + "· #2" server number; serving card
   shows dots; event rows labelled "Rally A/B" with "side out" marker when
   no point scored; legend/empty-state text; `docPayload` emits
   `version: 3`, `sport`, `format.scoring`, `format.side`; JSON loader reads
   them back with fallbacks. Keyboard map unchanged.
5. **Terminology**: "let" → "replay" in all user-facing text; CLI flags
   `--cut-lets`/`--let-tail` → `--cut-replays`/`--replay-tail` (internal
   option keys unchanged to minimize churn).
6. **Default accent**: `#BFD730` pickleball chartreuse (points digits, side
   bar, UI accents). Still configurable via colour picker / `--accent` /
   JSON.

`picklecut_v1.py` (zh-TW): identical logic byte-for-byte where possible;
only UI strings and comments in Traditional Chinese, following the existing
ttcut convention (tags JSON interchangeable between builds; ASS output
byte-identical apart from the version comment).

`tests/test_scoring.py`: unittest suite loading both builds by path:
doubles 0-0-2 start; side-out chains (#1 → #2 → side-out); serving-side
scoring only; game end only on serve; deuce win-by-2; capped; singles;
rally mode (score every rally, serve follows winner); game events; handicap
and starting games; next-game server alternation; EN vs zh-TW fold parity
and ASS parity (minus version line).

`README.md` / `README.zh-TW.md`: rewritten for pickleball.

`ttcut_v2_2*.py`: left in the working tree for now (git preserves them);
delete when KC confirms.

## Future sports (design note, not implemented)

- **Badminton** = rally mode with target 21, cap 30 — needs only a sport
  preset (terminology + defaults).
- **Tennis / padel** = structurally different (points 0/15/30/40, games,
  sets, tiebreaks): needs a new fold variant AND a scoreboard layout with a
  sets column. The seams that make this possible: the fold returns opaque
  display states consumed only by `build_ass` and the `/fold` JSON; nothing
  else in the pipeline knows the sport.

## Verification

- `python -m unittest` green on the suite above, for both builds.
- `python picklecut_v1_EN.py <synthetic>.tags.json fake.mp4 --dry-run`
  prints a sane cut table and pickleball-worded summary.
- ASS parity check between EN and zh-TW builds on the same JSON.
