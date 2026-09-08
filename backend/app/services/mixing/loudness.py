import numpy as np
import pyloudnorm as pyln
from scipy.signal import resample_poly

CHANNEL_GAINS = (1.0, 1.0, 1.0, 1.41, 1.41)


def _round(value, digits=2):
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), digits)


def _k_weighted(samples: np.ndarray, sr: int) -> np.ndarray:
    meter = pyln.Meter(sr)
    data = np.array(samples, copy=True, dtype=np.float64)
    for stage in meter._filters.values():
        for channel in range(data.shape[1]):
            data[:, channel] = stage.apply_filter(data[:, channel])
    return data


def _block_lufs(filtered: np.ndarray, sr: int, window_sec: float, hop_sec: float):
    window = int(window_sec * sr)
    hop = max(int(hop_sec * sr), 1)
    if filtered.shape[0] < window:
        return []

    values = []
    channels = min(filtered.shape[1], len(CHANNEL_GAINS))
    for start in range(0, filtered.shape[0] - window + 1, hop):
        block = filtered[start : start + window]
        mean_square = np.mean(np.square(block), axis=0)
        weighted = sum(CHANNEL_GAINS[i] * mean_square[i] for i in range(channels))
        if weighted <= 1e-12:
            continue
        loudness = -0.691 + 10.0 * np.log10(weighted)
        if np.isfinite(loudness):
            values.append(float(loudness))
    return values


def _summarize(values):
    if not values:
        return None, None
    return _round(max(values)), _round(float(np.mean(values)))


def _integrated_lufs(samples: np.ndarray, sr: int):
    if samples.shape[0] < sr // 4:
        return None
    try:
        loudness = float(pyln.Meter(sr).integrated_loudness(samples))
    except Exception:
        return None
    return _round(loudness)


def _true_peak_dbtp(samples: np.ndarray):
    oversampled = resample_poly(samples, 4, 1, axis=0)
    peak = float(np.max(np.abs(oversampled)))
    return _round(20.0 * np.log10(max(peak, 1e-12)))


def measure_loudness(samples: np.ndarray, sr: int) -> dict:
    mix = samples.mean(axis=1)
    rms = float(np.sqrt(np.mean(np.square(mix))))
    filtered = _k_weighted(samples, sr)
    momentary = _block_lufs(filtered, sr, window_sec=0.4, hop_sec=0.1)
    short_term = _block_lufs(filtered, sr, window_sec=3.0, hop_sec=0.1)
    momentary_max, momentary_mean = _summarize(momentary)
    short_max, short_mean = _summarize(short_term)

    return {
        "integrated_lufs": _integrated_lufs(samples, sr),
        "short_term_lufs": short_max,
        "short_term_lufs_mean": short_mean,
        "momentary_lufs": momentary_max,
        "momentary_lufs_mean": momentary_mean,
        "true_peak_dbtp": _true_peak_dbtp(samples),
        "rms": round(rms, 6),
        "rms_db": _round(20.0 * np.log10(max(rms, 1e-12))),
    }