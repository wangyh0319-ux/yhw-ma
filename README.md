# AI Music Analyzer

Short-drama music toolkit: measure a track, score a mix, and find library cues from a scene description.

Upload **MP3** or **WAV** (up to 50 MB). The UI is English; scene search understands Chinese descriptions.

This repository is the source code. Clone it and run locally to try the app. Audio files in a private library are not included.

## What it does

Three modules in one web app:

| Module | For | What you get |
| --- | --- | --- |
| **Analyzer** | “What is this track?” | Duration, BPM, key, LUFS, RMS, spectrum, optional AI genre/mood/energy |
| **Mixing Assistant** | “How is this bounce?” | Mix Health 0–100, loudness / frequency / dynamics / stereo / clipping, issue list, optional AI notes from those numbers only |
| **Library** | Short-drama music cues | Batch upload, mood/style/scene tags, filters, **Find Music** from a written scene |

Scene search example: *女主发现男友出轨后，一个人在雨夜回家.*  
The app maps that to mood / scene / relationship / drama tags, scores the library, and explains why each cue was suggested. It works **without** a paid OpenAI key (keyword rules). If a key is present and the API succeeds, parsing can be more precise.

Mixing DSP stays separate from Analyzer: stereo load, 7-band mix spectrum, scores first; AI only comments on those scores.

## Stack

- **Frontend:** React + Vite  
- **Backend:** FastAPI (Python 3.9+ locally; Docker uses 3.11)  
- **Audio:** librosa, pyloudnorm, ffmpeg (MP3)  
- **Library:** SQLite  
- **Optional AI:** OpenAI-compatible chat API (`gpt-4o-mini` by default)

## Run locally

You need **two terminals**. MP3 analysis requires **ffmpeg** on the machine (`brew install ffmpeg` on macOS). WAV works without it.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Use this address (not port 8000) while developing so you get the live UI.

### Optional OpenAI

Copy `backend/.env.example` to `backend/.env` and set `OPENAI_API_KEY`. Without a key, measurements, mix scores, tagging rules, and scene search still run; Analyzer/Mixing AI text and richer drama tags are skipped.

Do not commit `.env`.

## Deploy

A `Dockerfile` builds the frontend and serves it from FastAPI (one URL). Railway-style hosts should generate a public domain after a successful deploy. Public hobby instances may time out on long files; the image caps analysis to **22.05 kHz / 90 seconds** to reduce memory use.

## Limits

- Formats: `.mp3`, `.wav`  
- Upload size: 50 MB  
- Library audio and the SQLite DB are gitignored (`backend/library/`)  
- Temporary Analyzer/Mixing uploads are deleted after the run; library files are kept on the server disk  

## License

Private project shared as a portfolio. Ask before reusing it in a product.
