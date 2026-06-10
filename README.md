# YouTube Audiobook Generator

Convert YouTube videos into professional audiobooks in **Arabic**, **English**, and **Hebrew**.

## Architecture

```
backend/      — Python FastAPI server
frontend/     — React + Vite + TypeScript + Tailwind CSS
```

**Pipeline**: YouTube URL → Transcript (youtube-transcript-api) → TTS (Edge-TTS neural voices) → MP3 download

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## How It Works

1. **Paste a YouTube URL** — any video with captions/subtitles enabled
2. **Select language** — Arabic, English, or Hebrew (auto-detects available transcript)
3. **Pick a voice** — multiple neural voices per language (male/female)
4. **Generate** — backend fetches the transcript, synthesizes speech via Edge-TTS, and merges segments into a single MP3
5. **Download** — listen in-browser or download the MP3

## Supported Languages

| Language | Voices | TTS Engine |
|----------|--------|------------|
| Arabic   | Salma, Hamed, Fatima, Moaz | Microsoft Edge Neural |
| Hebrew   | Hila, Avri | Microsoft Edge Neural |
| English  | Jenny, Guy, Sonia, Ryan, Natasha | Microsoft Edge Neural |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend   | Python FastAPI |
| Transcript | youtube-transcript-api |
| TTS      | edge-tts (Microsoft Edge neural voices, free) |
| Audio    | FFmpeg |
| Frontend | React 19, Vite, Tailwind CSS 4 |

## License

MIT
