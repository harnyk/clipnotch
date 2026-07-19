# clipnotch

Keyboard-first desktop tool for slicing audio samples out of a YouTube video: paste a link, get a waveform, drop markers, preview intervals, export the ones you want.

## Install

```bash
uv tool install .
```

This puts a `clipnotch` executable on your `PATH` (via `uv tool`). Requires `ffmpeg` on `PATH`.

## Run

```bash
clipnotch
```

Or launch straight into a YouTube URL, skipping the paste-and-Enter step:

```bash
clipnotch https://www.youtube.com/watch?v=...
```

(or, from inside the project directory without installing: `uv run clipnotch [url]`)

Downloaded audio is cached by a hash of the URL under a temp directory (`$TMPDIR/clipnotch`, e.g. `/tmp/clipnotch`), so reopening the same URL skips re-downloading and re-converting.

## Keyboard cheatsheet

| Key | Action |
|---|---|
| `←` / `→` | Move playhead by a small step (100 ms) |
| `Shift + ←` / `Shift + →` | Move playhead by a large step (1000 ms) |
| `Space` | Play from the current position. If `U` (loop) is on, playback loops within the interval containing the playhead once it reaches that interval's end; otherwise it just keeps playing. Pressing `Space` again stops and rewinds to the nav point (blue) |
| `S` | Stop in place — stop playback without rewinding to the nav point and without moving it |
| `M` | Add a marker at the current position |
| `O` / `P` | Nudge the marker to the left of the playhead by -10 / +10 ms |
| `[` / `]` | Nudge the marker to the right of the playhead by -10 / +10 ms |
| `Backspace` / `Delete` | Remove the nearest marker |
| `Tab` | Jump to the next marker |
| `Shift + Tab` | Jump to the previous marker |
| `K` / `L` | Jump to the previous / next interval (covers the first and last interval too, unlike Tab); also sets the nav point there |
| `Enter` | Pin the nav point (blue) to the current playhead position — does not play anything |
| `U` | Toggle loop mode for `Space` (shown in the "Loop: ON/OFF" label next to the URL field) |
| `X` | Toggle the current interval for export |
| `Ctrl + S` | Export all included intervals |
| `+` / `-` | Zoom the waveform |

Clicking the waveform moves the playhead and returns keyboard focus to the app, so shortcuts keep working afterward. The waveform view auto-scrolls to keep the playhead in view.

The **nav point** (blue line) is the position `Space` returns playback to when stopping. It's only set by `Enter` or by jumping to an interval with `K`/`L` — plain navigation (arrows, Tab) and `Space`/`S` never move it.

Marker nudging (`O`/`P`/`[`/`]`) can't push a marker past its neighbor — it stops one millisecond short.
