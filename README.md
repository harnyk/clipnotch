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
| `Space` | Play / stop from the current position (stop returns to the nav point, shown in blue) |
| `S` | "Stop here" — stop playback and pin the nav point (blue) to the current position |
| `M` | Add a marker at the current position |
| `Backspace` / `Delete` | Remove the nearest marker |
| `Tab` | Jump to the next marker |
| `Shift + Tab` | Jump to the previous marker |
| `K` / `L` | Jump to the previous / next interval (covers the first and last interval too, unlike Tab) |
| `Enter` | Preview the current interval once |
| `X` | Toggle the current interval for export |
| `Ctrl + S` | Export all included intervals |
| `+` / `-` | Zoom the waveform |

Clicking the waveform moves the playhead and returns keyboard focus to the app, so shortcuts keep working afterward. The waveform view auto-scrolls to keep the playhead in view.

The **nav point** (blue line) is the position `Space` returns playback to when stopping. Pressing `Space` to start playing sets it to wherever you started from; pressing `S` explicitly pins it wherever the playhead currently is (e.g. mid-playback), overriding that.
