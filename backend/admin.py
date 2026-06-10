"""Admin dashboard - activity tracking and logs"""
import time
import uuid
from datetime import datetime, timezone
from collections import defaultdict
from threading import Lock

_lock = Lock()

# In-memory storage (use SQLite for persistence in production)
_jobs: list[dict] = []
_active_sessions: dict[str, float] = {}  # ip -> last active timestamp
_hourly_counts: dict[str, int] = defaultdict(int)  # "YYYY-MM-DDTHH" -> count


def record_job(
    job_id: str,
    url: str,
    language: str,
    voice: str,
    client_ip: str = "unknown",
):
    now = datetime.now(timezone.utc)
    hour_key = now.strftime("%Y-%m-%dT%H")
    with _lock:
        _jobs.append(
            {
                "job_id": job_id,
                "url": url,
                "language": language,
                "voice": voice,
                "client_ip": client_ip,
                "created_at": now.isoformat(),
                "completed_at": None,
                "status": "pending",
                "error": None,
            }
        )
        _hourly_counts[hour_key] += 1
        _active_sessions[client_ip] = time.time()
        _cleanup_sessions()


def update_job(job_id: str, status: str, error: str = None):
    now = datetime.now(timezone.utc)
    with _lock:
        for job in _jobs:
            if job["job_id"] == job_id:
                job["status"] = status
                job["error"] = error
                if status in ("completed", "error"):
                    job["completed_at"] = now.isoformat()
                break


def track_activity(client_ip: str):
    with _lock:
        _active_sessions[client_ip] = time.time()
        _cleanup_sessions()


def _cleanup_sessions(max_age_secs: int = 300):
    cutoff = time.time() - max_age_secs
    stale = [ip for ip, t in _active_sessions.items() if t < cutoff]
    for ip in stale:
        del _active_sessions[ip]


def get_dashboard() -> dict:
    with _lock:
        total = len(_jobs)
        completed = sum(1 for j in _jobs if j["status"] == "completed")
        failed = sum(1 for j in _jobs if j["status"] == "error")
        active_now = len(_active_sessions)

        # Active hours (last 24h)
        now = datetime.now(timezone.utc)
        hours_24 = []
        for i in range(24):
            h = now.replace(minute=0, second=0, microsecond=0)
            h = h.replace(hour=(now.hour - i) % 24)
            key = h.strftime("%Y-%m-%dT%H")
            hours_24.append({"hour": key, "requests": _hourly_counts.get(key, 0)})
        hours_24.reverse()

        # Recent activity logs (last 50)
        logs = sorted(_jobs, key=lambda j: j["created_at"], reverse=True)[:50]

        return {
            "total_jobs": total,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "active_sessions": active_now,
            "active_hours": hours_24,
            "recent_logs": [
                {
                    "job_id": j["job_id"],
                    "url": j["url"],
                    "language": j["language"],
                    "voice": j["voice"],
                    "status": j["status"],
                    "error": j["error"],
                    "created_at": j["created_at"],
                    "duration": (
                        (
                            datetime.fromisoformat(j["completed_at"])
                            - datetime.fromisoformat(j["created_at"])
                        ).total_seconds()
                        if j.get("completed_at")
                        else None
                    ),
                }
                for j in logs
            ],
        }
