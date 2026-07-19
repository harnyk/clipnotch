import wave
from pathlib import Path
import numpy as np
import pytest


def _write_sine_wav(path: Path, duration_s: float = 1.0, freq: float = 440.0, framerate: int = 44100) -> None:
    n_samples = int(duration_s * framerate)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    amplitude = 16000
    samples = (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(samples.tobytes())


@pytest.fixture
def test_wav_path(tmp_path) -> Path:
    path = tmp_path / "test_tone.wav"
    _write_sine_wav(path)
    return path
