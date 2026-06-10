import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from transcript import extract_video_id, fetch_transcript, group_sentences
from tts_engine import get_supported_languages, get_voices_for_language, synthesize
from enhancer import enhance_transcript, build_ssml
from audiobook import merge_audio_files
from admin import record_job, update_job, track_activity, get_dashboard
from pydantic import BaseModel

app = FastAPI(title="YouTube Audiobook Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(tempfile.gettempdir()) / "youtube-audiobook"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

jobs: dict[str, dict] = {}

# Serve frontend static files in production
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


class GenerateRequest(BaseModel):
    url: str
    language: str = "en"
    voice: str | None = None


@app.get("/languages")
async def list_languages():
    return get_supported_languages()


@app.get("/voices")
async def list_voices(language: str = "en"):
    return get_voices_for_language(language)


@app.post("/generate")
async def generate_audiobook(req: GenerateRequest, background_tasks: BackgroundTasks, request: Request):
    job_id = str(uuid.uuid4())
    client_ip = request.client.host if request.client else "unknown"
    record_job(job_id, req.url, req.language, req.voice or "", client_ip)
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "output_path": None,
        "filename": None,
    }
    background_tasks.add_task(_process_job, job_id, req.url, req.language, req.voice)
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def get_status(job_id: str, request: Request):
    track_activity(request.client.host if request.client else "unknown")
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "status": job["status"],
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
    }


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    if not job["output_path"] or not os.path.exists(job["output_path"]):
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(
        job["output_path"],
        media_type="audio/mpeg",
        filename=job.get("filename", "audiobook.mp3"),
    )


@app.get("/admin")
async def admin_dashboard(request: Request):
    track_activity(request.client.host if request.client else "unknown")
    return get_dashboard()


@app.get("/")
@app.get("/admin")
async def serve_frontend():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return {"message": "Backend is running. Build the frontend with `cd frontend && npx vite build`"}


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    raise HTTPException(status_code=404, detail="Not found")


async def _process_job(job_id: str, url: str, language: str, voice: str | None):
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["message"] = "Extracting video ID..."

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)
        update_job(job_id, "error", str(e))
        return

    jobs[job_id]["progress"] = 5
    jobs[job_id]["message"] = "Fetching transcript..."

    try:
        segments = await fetch_transcript(video_id, language)
    except Exception as e:
        msg = f"Transcript error: {e}"
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = msg
        update_job(job_id, "error", msg)
        return

    if not segments:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = "No transcript available"
        update_job(job_id, "error", "No transcript available")
        return

    groups = group_sentences(segments)
    jobs[job_id]["progress"] = 15
    jobs[job_id]["message"] = f"Enhancing transcript with AI ({len(groups)} segments)..."

    try:
        enhanced = await enhance_transcript(groups, language)
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = f"Enhancement failed: {e}"
        update_job(job_id, "error", f"Enhancement failed: {e}")
        return

    if not voice:
        voices = get_voices_for_language(language)
        voice = next(iter(voices.keys())) if voices else "en-US-JennyNeural"

    jobs[job_id]["progress"] = 20
    jobs[job_id]["message"] = f"Synthesizing {len(enhanced)} segments with emotional TTS..."

    audio_files = []
    total = len(enhanced)

    for i, item in enumerate(enhanced):
        jobs[job_id]["progress"] = int(20 + (i / total) * 75)
        jobs[job_id]["message"] = f"Audio {i + 1}/{total} ({item.get('emotion', 'neutral')})..."

        ssml = build_ssml(
            text=item["text"],
            emotion=item.get("emotion", "neutral"),
            voice=voice,
            lang=language,
        )

        try:
            audio_data = await synthesize(ssml, voice, language)
        except Exception as e:
            jobs[job_id]["message"] = f"TTS failed on segment {i + 1}: {e}"
            continue

        seg_path = os.path.join(OUTPUT_DIR, f"{job_id}_seg_{i:04d}.mp3")
        with open(seg_path, "wb") as f:
            f.write(audio_data)
        audio_files.append(seg_path)

    if not audio_files:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = "No audio could be generated"
        update_job(job_id, "error", "No audio could be generated")
        return

    jobs[job_id]["progress"] = 96
    jobs[job_id]["message"] = "Merging audio files..."

    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp3")
    try:
        await merge_audio_files(audio_files, output_path)
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = f"Merge failed: {e}"
        update_job(job_id, "error", f"Merge failed: {e}")
        return

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["progress"] = 100
    jobs[job_id]["message"] = "Done"
    jobs[job_id]["output_path"] = output_path
    jobs[job_id]["filename"] = f"audiobook_{video_id}.mp3"
    update_job(job_id, "completed")
