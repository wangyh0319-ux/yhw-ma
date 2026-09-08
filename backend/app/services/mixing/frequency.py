import librosa
import numpy as np

BANDS = (
    ("sub", 20, 60),
    ("bass", 60, 120),
    ("low_mid", 120, 300),
    ("mid", 300, 1000),
    ("upper_mid", 1000, 4000),
    ("presence", 4000, 8000),
    ("air", 8000, 20000),
)


def _to_db(power: float) -> float:
    return float(10.0 * np.log10(max(power, 1e-12)))


def measure_frequency(samples: np.ndarray, sr: int, bar_count: int = 64) -> dict:
    mix = samples.mean(axis=1)
    stft = np.abs(librosa.stft(y=mix, n_fft=4096))
    power = np.square(stft)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
    mean_power = power.mean(axis=1)
    nyquist = sr / 2.0

    bands = {}
    for name, low, high in BANDS:
        if nyquist <= low:
            bands[name] = {
                "hz_low": low,
                "hz_high": high,
                "db": None,
                "available": False,
            }
            continue
        top = min(high, nyquist)
        mask = (freqs >= low) & (freqs < top)
        energy = float(np.mean(mean_power[mask])) if np.any(mask) else 0.0
        bands[name] = {
            "hz_low": low,
            "hz_high": high,
            "db": round(_to_db(energy), 2),
            "available": True,
            "limited_by_sample_rate": top < high,
        }

    mid_db = bands["mid"]["db"]
    for name, data in bands.items():
        if data["db"] is None or mid_db is None:
            data["relative_to_mid_db"] = None
        else:
            data["relative_to_mid_db"] = round(data["db"] - mid_db, 2)

    picks = np.linspace(0, len(mean_power) - 1, bar_count).astype(int)
    bars = []
    for index in picks:
        bars.append(
            {
                "hz": round(float(freqs[index]), 1),
                "db": round(_to_db(float(mean_power[index])), 2),
            }
        )

    return {"bands": bands, "bars": bars}