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

(or, from inside the project directory without installing: `uv run clipnotch`)

## Keyboard cheatsheet

| Key | Action |
|---|---|
| `←` / `→` | Move playhead by a small step (100 ms) |
| `Shift + ←` / `Shift + →` | Move playhead by a large step (1000 ms) |
| `Space` | Play / stop from the current position (stop returns to where playback started, not to the beginning of the file) |
| `M` | Add a marker at the current position |
| `Backspace` / `Delete` | Remove the nearest marker |
| `Tab` | Jump to the next marker |
| `Shift + Tab` | Jump to the previous marker |
| `Enter` | Preview the current interval once |
| `X` | Toggle the current interval for export |
| `Ctrl + S` | Export all included intervals |
| `+` / `-` | Zoom the waveform |

Clicking the waveform moves the playhead and gives it keyboard focus.
