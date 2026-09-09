import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from app.config import LIBRARY_DB, LIBRARY_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT,
    audio_path TEXT,
    duration_sec REAL,
    bpm REAL,
    key TEXT,
    sample_rate INTEGER,
    genre TEXT,
    vocal_type TEXT,
    energy TEXT,
    tempo_feel TEXT,
    brightness TEXT,
    tension TEXT,
    intensity TEXT,
    mix_overall INTEGER,
    lufs REAL,
    dynamic_range_db REAL,
    mix_json TEXT,
    analyzer_json TEXT,
    ai_description TEXT,
    usage_suggestions TEXT,
    user_notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS track_tags (
    track_id TEXT NOT NULL,
    namespace TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (track_id, namespace, tag),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS import_jobs (
    id TEXT PRIMARY KEY,
    total INTEGER NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _connect():
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(LIBRARY_DB)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with _connect() as connection:
        connection.executescript(SCHEMA)


def _now():
    return datetime.now(timezone.utc).isoformat()


def create_track(
    title: str,
    artist: str = None,
    audio_path: str = None,
    duration_sec: float = None,
    sample_rate: int = None,
) -> dict:
    track_id = uuid4().hex
    clean_title = (title or "").strip() or "Untitled"
    clean_artist = (artist or "").strip() or None
    created = _now()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO tracks (
                id, title, artist, audio_path, duration_sec, sample_rate, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                track_id,
                clean_title,
                clean_artist,
                audio_path,
                duration_sec,
                sample_rate,
                created,
            ),
        )
    return get_track(track_id)


def list_tracks(moods=None, styles=None) -> list:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, title, artist, audio_path, duration_sec, bpm, key, genre, energy, created_at
            FROM tracks
            ORDER BY created_at DESC
            """
        ).fetchall()
    tracks = [with_tags(dict(row)) for row in rows]
    mood_set = {item for item in (moods or []) if item}
    style_set = {item for item in (styles or []) if item}
    if mood_set:
        tracks = [
            track
            for track in tracks
            if mood_set.intersection(track.get("tags", {}).get("mood") or [])
        ]
    if style_set:
        tracks = [
            track
            for track in tracks
            if track.get("genre") in style_set
            or style_set.intersection(track.get("tags", {}).get("style") or [])
        ]
    return tracks


def list_tracks_for_match() -> list:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, title, artist, audio_path, duration_sec, bpm, key, genre,
                   energy, tempo_feel, tension, intensity, mix_overall, lufs, analyzer_json
            FROM tracks
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [with_tags(dict(row)) for row in rows]


def get_track(track_id: str):
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM tracks WHERE id = ?",
            (track_id,),
        ).fetchone()
    if row is None:
        return None
    return with_tags(dict(row))


def update_audio(
    track_id: str,
    audio_path: str,
    duration_sec: float = None,
    sample_rate: int = None,
) -> dict:
    with _connect() as connection:
        connection.execute(
            """
            UPDATE tracks
            SET audio_path = ?, duration_sec = ?, sample_rate = ?
            WHERE id = ?
            """,
            (audio_path, duration_sec, sample_rate, track_id),
        )
    return get_track(track_id)


def get_tags(track_id: str) -> dict:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT namespace, tag FROM track_tags
            WHERE track_id = ?
            ORDER BY namespace, tag
            """,
            (track_id,),
        ).fetchall()
    tags = {}
    for row in rows:
        tags.setdefault(row["namespace"], []).append(row["tag"])
    return tags


def replace_tags(track_id: str, tags_by_namespace: dict):
    with _connect() as connection:
        connection.execute("DELETE FROM track_tags WHERE track_id = ?", (track_id,))
        for namespace, values in (tags_by_namespace or {}).items():
            for tag in values:
                connection.execute(
                    """
                    INSERT INTO track_tags (track_id, namespace, tag)
                    VALUES (?, ?, ?)
                    """,
                    (track_id, namespace, tag),
                )


def update_analysis(track_id: str, **fields):
    allowed = {
        "bpm",
        "key",
        "duration_sec",
        "genre",
        "vocal_type",
        "energy",
        "tempo_feel",
        "brightness",
        "tension",
        "intensity",
        "lufs",
        "dynamic_range_db",
        "analyzer_json",
        "ai_description",
        "usage_suggestions",
    }
    assignments = []
    values = []
    for name, value in fields.items():
        if name in allowed:
            assignments.append(f"{name} = ?")
            values.append(value)
    if not assignments:
        return get_track(track_id)
    values.append(track_id)
    with _connect() as connection:
        connection.execute(
            f"UPDATE tracks SET {', '.join(assignments)} WHERE id = ?",
            values,
        )
    return get_track(track_id)


def with_tags(track: dict):
    if track is None:
        return None
    track["tags"] = get_tags(track["id"])
    return track


def delete_track(track_id: str) -> bool:
    track = get_track(track_id)
    if track is None:
        return False
    with _connect() as connection:
        connection.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    if track.get("audio_path"):
        path = LIBRARY_DIR / track["audio_path"]
        path.unlink(missing_ok=True)
    return True