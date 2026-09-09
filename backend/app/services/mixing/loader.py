from pathlib import Path
import os

import librosa
import numpy as np


def load_mix_audio(path: Path):
    try:
        target_sr = os.getenv("AUDIO_SR", "").strip()
        sr_arg = int(target_sr) if target_sr else None
        duration_cap = os.getenv("AUDIO_DURATION_SEC", "").strip()
        duration_arg = float(duration_cap) if duration_cap else None
        y, sr = librosa.load(
            path, sr=sr_arg, mono=False, duration=duration_arg
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not read this audio file. WAV works as-is; MP3 needs ffmpeg."
        ) from exc

    y = np.asarray(y, dtype=np.float64)
    if y.size == 0:
        raise RuntimeError("Audio file has no samples.")

    if y.ndim == 1:
        y = y.reshape(-1, 1)
    else:
        y = y.T

    return y, int(sr)