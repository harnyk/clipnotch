import numpy as np
from audioshit.waveform import compute_peaks


def test_compute_peaks_returns_expected_shape(test_wav_path):
    peaks = compute_peaks(test_wav_path, num_buckets=100)
    assert peaks.shape == (100, 2)


def test_compute_peaks_min_le_max(test_wav_path):
    peaks = compute_peaks(test_wav_path, num_buckets=100)
    assert np.all(peaks[:, 0] <= peaks[:, 1])


def test_compute_peaks_captures_amplitude(test_wav_path):
    peaks = compute_peaks(test_wav_path, num_buckets=50)
    assert peaks[:, 1].max() > 15000
    assert peaks[:, 0].min() < -15000


def test_compute_peaks_rejects_non_positive_buckets(test_wav_path):
    import pytest

    with pytest.raises(ValueError):
        compute_peaks(test_wav_path, num_buckets=0)
