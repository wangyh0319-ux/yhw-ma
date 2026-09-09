import os
from pathlib import Path

# librosa/numba need a writable cache. Without it, WAV/MP3 load fails with
# "no locator available" and the UI only shows a generic ffmpeg error.
_cache = Path(os.getenv("NUMBA_CACHE_DIR") or "/tmp/ai-music-analyzer-numba")
try:
    _cache.mkdir(parents=True, exist_ok=True)
    os.environ["NUMBA_CACHE_DIR"] = str(_cache)
except OSError:
    pass
