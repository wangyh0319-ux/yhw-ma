import re
from pathlib import Path

from app.config import LIBRARY_DIR

LYRIC_SUFFIXES = (".lrc", ".txt")
AUDIO_SUFFIXES = (".mp3", ".wav")
MAX_LYRICS_CHARS = 4000
_LRC_TAG = re.compile(r"\[[^\]]*\]")


def _safe_stem(title: str):
    name = Path(title or "").name.strip()
    if not name or name in {".", ".."}:
        return None
    return Path(name).stem or None


def _clean_lyrics(text: str) -> str:
    if not text:
        return ""
    lines = []
    for raw in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = _LRC_TAG.sub("", raw).strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(("ti:", "ar:", "al:", "by:", "offset:")):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    if len(cleaned) > MAX_LYRICS_CHARS:
        return cleaned[:MAX_LYRICS_CHARS]
    return cleaned


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return _clean_lyrics(path.read_text(encoding=encoding))
        except Exception:
            continue
    return ""


def _tag_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        for encoding in ("utf-8", "gb18030", "latin-1"):
            try:
                return value.decode(encoding)
            except Exception:
                continue
        return ""
    text = getattr(value, "text", None)
    if isinstance(text, (list, tuple)):
        return "\n".join(str(item) for item in text if item)
    if text:
        return str(text)
    return str(value)


def _from_mutagen(path: Path) -> str:
    try:
        from mutagen import File
    except Exception:
        return ""
    try:
        audio = File(str(path))
    except Exception:
        return ""
    if audio is None or not audio.tags:
        return ""

    chunks = []
    tags = audio.tags
    try:
        keys = list(tags.keys())
    except Exception:
        keys = []

    for key in keys:
        label = str(key).upper()
        if not any(
            token in label
            for token in ("USLT", "SYLT", "LYRICS", "UNSYNCEDLYRICS", "©LYR")
        ):
            continue
        try:
            value = tags[key]
        except Exception:
            continue
        if isinstance(value, (list, tuple)):
            chunks.extend(_tag_text(item) for item in value)
        else:
            chunks.append(_tag_text(value))

    return _clean_lyrics("\n".join(chunk for chunk in chunks if chunk))


def _sidecar_candidates(audio_path: Path, title: str):
    stems = [audio_path.with_suffix("")]
    stem = _safe_stem(title)
    if stem:
        stems.append(audio_path.parent / stem)
        stems.append(LIBRARY_DIR / stem)
        downloads = Path.home() / "Downloads"
        if downloads.is_dir():
            stems.append(downloads / stem)
    seen = set()
    for stem_path in stems:
        for suffix in LYRIC_SUFFIXES:
            candidate = Path(str(stem_path) + suffix)
            resolved = str(candidate)
            if resolved in seen:
                continue
            seen.add(resolved)
            yield candidate


def _original_audio_candidates(title: str):
    stem = _safe_stem(title)
    if not stem:
        return
    downloads = Path.home() / "Downloads"
    if not downloads.is_dir():
        return
    for suffix in AUDIO_SUFFIXES:
        yield downloads / f"{stem}{suffix}"


def load_lyrics_snippet(audio_path: Path, title: str = "") -> str:
    """Read lyrics from tags or a same-stem sidecar. Never invents text."""
    path = Path(audio_path)
    if path.is_file():
        embedded = _from_mutagen(path)
        if embedded:
            return embedded

    for candidate in _sidecar_candidates(path, title):
        if candidate.is_file():
            text = _read_text_file(candidate)
            if text:
                return text

    for original in _original_audio_candidates(title):
        if original.is_file():
            embedded = _from_mutagen(original)
            if embedded:
                return embedded
    return ""
