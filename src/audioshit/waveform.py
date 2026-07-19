import wave
from pathlib import Path
import numpy as np


def compute_peaks(wav_path: Path, num_buckets: int) -> np.ndarray:
    if num_buckets <= 0:
        raise ValueError("num_buckets must be positive")

    with wave.open(str(wav_path), "rb") as wf:
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Unsupported sample width: {sampwidth} bytes (expected 16-bit PCM)")

    samples = np.frombuffer(raw, dtype=np.int16)
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1).astype(np.int16)

    bucket_size = max(1, len(samples) // num_buckets)
    trimmed_len = min(len(samples), bucket_size * num_buckets)
    trimmed = samples[:trimmed_len].reshape(-1, bucket_size)

    peaks = np.zeros((num_buckets, 2), dtype=np.int16)
    peaks[: trimmed.shape[0], 0] = trimmed.min(axis=1)
    peaks[: trimmed.shape[0], 1] = trimmed.max(axis=1)
    return peaks
