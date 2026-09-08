from pathlib import Path

import librosa
import numpy as np


def load_mix_audio(path: Path):
    try:
        y, sr = librosa.load(path, sr=None, mono=False)
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