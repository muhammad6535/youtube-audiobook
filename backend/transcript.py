import re
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Could not extract video ID from URL")


async def fetch_transcript(video_id: str, language: str = "en") -> list[dict]:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        snippets = transcript.snippets

        texts = []
        for s in snippets:
            text = s.text.strip()
            if text and text not in ("[Music]", "[Applause]", "[Laughter]"):
                texts.append({"start": s.start, "duration": s.duration, "text": text})
        return texts
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript: {e}")


def group_sentences(segments: list[dict], max_chars: int = 500) -> list[dict]:
    groups = []
    current_group = {"start": 0, "texts": [], "char_count": 0}

    for i, seg in enumerate(segments):
        text = seg["text"]
        text_len = len(text)

        if current_group["char_count"] == 0:
            current_group["start"] = seg["start"]
            current_group["texts"].append(text)
            current_group["char_count"] = text_len
        elif current_group["char_count"] + text_len > max_chars:
            groups.append(
                {
                    "start": current_group["start"],
                    "text": " ".join(current_group["texts"]),
                }
            )
            current_group = {"start": seg["start"], "texts": [text], "char_count": text_len}
        else:
            current_group["texts"].append(text)
            current_group["char_count"] += text_len

    if current_group["texts"]:
        groups.append(
            {
                "start": current_group["start"],
                "text": " ".join(current_group["texts"]),
            }
        )

    return groups
