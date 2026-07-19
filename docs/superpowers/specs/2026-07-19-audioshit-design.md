# audioshit — Design Spec

Date: 2026-07-19

## Purpose

A keyboard-first desktop tool for quickly slicing and converting audio samples from source material. First iteration: paste a YouTube link, extract audio, visualize the waveform, place markers, preview each inter-marker interval, and export selected intervals to a folder in a chosen format. Telegram voice message / video ingestion is a candidate for a later iteration once the YouTube + marker workflow is solid.

## Scope (Iteration 1)

- Input: YouTube URL only (paste into UI). Local file drag-and-drop is a stretch goal for this iteration if time allows, but not required.
- Output: WAV by default, with a format dropdown driven by whatever ffmpeg supports (mp3, flac, etc.).
- Out of scope for iteration 1: Telegram ingestion, batch processing multiple URLs at once, undo/redo history, project save/load (re-opening a previous marker session).

## Stack

- **Language/runtime**: Python 3.12, dependencies managed via `uv`.
- **GUI**: PySide6 (Qt for Python). Chosen over Rust (egui/iced) and C#/Avalonia because of faster iteration speed, despite Python being a secondary preference to the user — accepted as the pragmatic fallback.
- **Download**: `yt-dlp` to fetch the best available audio stream from a YouTube URL.
- **Audio processing**: `ffmpeg` / `ffprobe` invoked via subprocess for decoding, format conversion, and trimming. No web/Electron stack.
- **Waveform data**: `numpy` for computing min/max peak buckets from decoded PCM, used to render the waveform view.
- **Playback**: `QMediaPlayer` (Qt Multimedia) for native playhead/seek/position control.

## Architecture

Five components:

1. **Ingest** — Takes a YouTube URL, runs `yt-dlp` to download the best audio stream to a temp directory, then `ffmpeg` converts it to WAV for internal processing. (Local file drag-and-drop would skip the `yt-dlp` step and go straight to the WAV conversion step.)
2. **Waveform Engine** — Decodes the WAV to PCM and computes min/max peaks per block via `numpy`, upfront for the whole file (source material is expected to be minutes long, not hours, so no need for progressive/streaming computation in this iteration).
3. **Player** — Wraps `QMediaPlayer`. Supports play-from-position, seek, and stop-at-position (used both for whole-track playback and for single-shot interval preview).
4. **Marker Editor** — Owns the marker/interval state: an ordered list of marker positions (ms), derived list of intervals between adjacent markers, each interval carrying an `included_in_export: bool` flag defaulting to `False`.
5. **Exporter** — For each interval flagged `included_in_export`, invokes `ffmpeg -ss <start> -to <end>` with re-encoding to the selected format, writing to the chosen output folder.

## Data Flow

```
YouTube URL → yt-dlp → raw audio file → ffmpeg → WAV (temp)
                                                    │
                                                    ▼
                                          Waveform Engine (peaks)
                                                    │
                                                    ▼
                                    GUI: waveform view + Marker Editor
                                                    │
                                    (keyboard) markers added/removed/toggled
                                                    │
                                                    ▼
                                    Exporter → ffmpeg per included interval
                                                    │
                                                    ▼
                                    output folder: <source_name>_<start>_<end>.<ext>
```

## UI & Keyboard Workflow

Keyboard-first; mouse is optional (click on waveform to move playhead).

| Key | Action |
|---|---|
| ←/→ | Move playhead (Shift = large step, plain = small step, e.g. 1s/10ms) |
| Space | Play/stop whole track from current position |
| M | Place a marker at the playhead position |
| Backspace/Delete | Delete the nearest marker to the playhead |
| Tab / Shift+Tab | Jump to next/previous marker |
| Enter | Preview the interval currently under the playhead — plays once, then stops (no looping) |
| X | Toggle "included in export" for the current interval (visual highlight: included = green, excluded = grey) |
| Ctrl+S | Export all included intervals to the chosen folder/format |
| +/- or Ctrl+Wheel | Zoom waveform |

A side panel lists all intervals as a table (position, duration, included/excluded status) mirroring the waveform, for a non-visual way to scan state.

Format selection (dropdown, ffmpeg-supported formats, WAV default) and output folder selection (standard OS folder picker) live in the export/toolbar area.

## File Naming

Exported files: `<source_name>_<start_timecode>_<end_timecode>.<ext>`, e.g. `lecture_00-12-450_00-14-200.wav`.

## Error Handling

- Invalid/unreachable YouTube URL or `yt-dlp` failure → surfaced as a status-bar/toast message; app stays usable.
- `ffmpeg`/`ffprobe` missing from PATH → checked at startup, explicit message pointing to install ffmpeg.
- Corrupt/unsupported audio file → decode error caught and surfaced; app remains in a working state.
- Export: destination folder writability checked before starting export, not discovered mid-batch.

## Testing

- Unit tests (pytest) for marker/interval logic: add, remove, toggle include/exclude, boundary conditions — pure data-model tests, no real audio.
- Unit tests for ffmpeg command construction during export (timecodes and filenames built correctly) — subprocess mocked.
- One integration test using a small local test WAV fixture: full load → add markers → mark included → export → verify output files exist with expected durations. No network calls to YouTube in tests; `yt-dlp` is exercised manually (or optionally mocked) rather than in the automated suite.
