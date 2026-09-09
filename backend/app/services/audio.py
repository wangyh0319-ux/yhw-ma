from pathlib import Path
import os

import librosa
import numpy as np
import pyloudnorm as pyln

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 2.87, 2.52, 4.20, 2.53, 3.60, 2.54, 3.53, 2.54, 3.98]
)
BANDS = (
    ("sub", 20, 60),
    ("bass", 60, 250),
    ("low_mid", 250, 500),
    ("mid", 500, 2000),
    ("high_mid", 2000, 6000),
    ("high", 6000, 16000),
)


def _to_db(value: float) -> float:
    return float(20.0 * np.log10(max(value, 1e-12)))


def estimate_key(y: np.ndarray, sr: int) -> str:
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    chroma_mean = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-9)

    major = MAJOR_PROFILE / np.linalg.norm(MAJOR_PROFILE)
    minor = MINOR_PROFILE / np.linalg.norm(MINOR_PROFILE)

    best_name = "C major"
    best_score = -1.0
    for shift in range(12):
        major_score = float(np.dot(chroma_mean, np.roll(major, shift)))
        minor_score = float(np.dot(chroma_mean, np.roll(minor, shift)))
        if major_score > best_score:
            best_score = major_score
            best_name = f"{NOTE_NAMES[shift]} major"
        if minor_score > best_score:
            best_score = minor_score
            best_name = f"{NOTE_NAMES[shift]} minor"
    return best_name


def estimate_lufs(y: np.ndarray, sr: int):
    if y.shape[0] < sr // 4:
        return None
    meter = pyln.Meter(sr)
    loudness = float(meter.integrated_loudness(y))
    if not np.isfinite(loudness):
        return None
    return round(loudness, 2)


def spectrum_features(y: np.ndarray, sr: int, bin_count: int = 64) -> dict:
    stft = np.abs(librosa.stft(y=y, n_fft=2048))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    magnitude = stft.mean(axis=1)

    picks = np.linspace(0, len(magnitude) - 1, bin_count).astype(int)
    bars = []
    for index in picks:
        bars.append(
            {
                "hz": round(float(freqs[index]), 1),
                "db": round(_to_db(float(magnitude[index])), 2),
            }
        )

    bands = {}
    for name, low, high in BANDS:
        mask = (freqs >= low) & (freqs < high)
        energy = float(np.mean(magnitude[mask])) if np.any(mask) else 0.0
        bands[name] = round(_to_db(energy), 2)

    return {"bars": bars, "bands": bands}


def analyze_audio(path: Path) -> dict:
    try:
        target_sr = os.getenv("AUDIO_SR", "").strip()
        sr_arg = int(target_sr) if target_sr else None
        duration_cap = os.getenv("AUDIO_DURATION_SEC", "").strip()
        duration_arg = float(duration_cap) if duration_cap else None
        y, sr = librosa.load(
            path, sr=sr_arg, mono=True, duration=duration_arg
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not read this audio file. WAV works as-is; MP3 needs ffmpeg."
        ) from exc

    if y.size == 0:
        raise RuntimeError("Audio file has no samples.")

    duration = float(librosa.get_duration(y=y, sr=sr))
    tempo = librosa.beat.beat_track(y=y, sr=sr)[0]
    bpm = float(np.atleast_1d(tempo)[0])

    rms_frames = librosa.feature.rms(y=y)[0]
    rms = float(np.mean(rms_frames))
    peak = float(np.max(np.abs(y)))
    rms_db = _to_db(rms)
    peak_db = _to_db(peak)

    return {
        "duration_sec": round(duration, 3),
        "sample_rate": int(sr),
        "bpm": round(bpm, 1),
        "key": estimate_key(y, sr),
        "lufs": estimate_lufs(y, sr),
        "rms": round(rms, 6),
        "rms_db": round(rms_db, 2),
        "peak_db": round(peak_db, 2),
        "dynamic_range_db": round(peak_db - rms_db, 2),
        "spectrum": spectrum_features(y, sr),
    }