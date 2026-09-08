import numpy as np
from scipy.signal import butter, sosfiltfilt

from app.services.mixing.loudness import _round

LOW_CUTOFF_HZ = 120.0
UNAVAILABLE = {
    "available": False,
    "message": "Cannot judge stereo image from a mono file.",
    "width": None,
    "correlation": None,
    "left_rms": None,
    "right_rms": None,
    "lr_balance_db": None,
    "mid_rms": None,
    "side_rms": None,
    "side_to_mid_db": None,
    "low_frequency": None,
}


def _rms(signal: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(signal))))


def _lowpass(signal: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
    nyquist = sr / 2.0
    if cutoff >= nyquist:
        return signal.copy()
    sos = butter(N=4, Wn=cutoff / nyquist, btype="low", output="sos")
    return sosfiltfilt(sos, signal)


def measure_stereo(samples: np.ndarray, sr: int) -> dict:
    if samples.shape[1] < 2:
        return dict(UNAVAILABLE)

    left = samples[:, 0]
    right = samples[:, 1]
    mid = 0.5 * (left + right)
    side = 0.5 * (left - right)

    left_rms = _rms(left)
    right_rms = _rms(right)
    mid_rms = _rms(mid)
    side_rms = _rms(side)

    if left.size >= 8:
        correlation = float(np.corrcoef(left, right)[0, 1])
        if not np.isfinite(correlation):
            correlation = None
    else:
        correlation = None

    # 0 = fully mid (mono), higher = more side energy / wider.
    width = float(side_rms / max(mid_rms, 1e-12))

    left_low = _lowpass(left, sr, LOW_CUTOFF_HZ)
    right_low = _lowpass(right, sr, LOW_CUTOFF_HZ)
    mid_low = 0.5 * (left_low + right_low)
    side_low = 0.5 * (left_low - right_low)
    mid_low_rms = _rms(mid_low)
    side_low_rms = _rms(side_low)
    if left_low.size >= 8:
        correlation_low = float(np.corrcoef(left_low, right_low)[0, 1])
        if not np.isfinite(correlation_low):
            correlation_low = None
    else:
        correlation_low = None

    return {
        "available": True,
        "message": None,
        "width": _round(width, 3),
        "correlation": _round(correlation, 3),
        "left_rms": round(left_rms, 6),
        "right_rms": round(right_rms, 6),
        "lr_balance_db": _round(20.0 * np.log10(max(left_rms, 1e-12) / max(right_rms, 1e-12))),
        "mid_rms": round(mid_rms, 6),
        "side_rms": round(side_rms, 6),
        "side_to_mid_db": _round(20.0 * np.log10(max(side_rms, 1e-12) / max(mid_rms, 1e-12))),
        "low_frequency": {
            "cutoff_hz": LOW_CUTOFF_HZ,
            "correlation": _round(correlation_low, 3),
            "side_to_mid_db": _round(
                20.0 * np.log10(max(side_low_rms, 1e-12) / max(mid_low_rms, 1e-12))
            ),
        },
    }