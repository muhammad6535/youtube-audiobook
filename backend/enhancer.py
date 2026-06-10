import json
import os
from openai import OpenAI

ZEN_API_KEY = os.environ.get(
    "OPENCODE_ZEN_KEY",
    "sk-2gMZ390jBpMqXiv6PiDxfOf5xegK9dIt1bKTOC4IN0ugZotPJLl1AkMjpEf9QGL2",
)
ZEN_BASE_URL = "https://opencode.ai/zen/v1"
ZEN_MODEL = "big-pickle"

REVIEW_PROMPT = """You are a professional audiobook editor. Your job is to transform a raw YouTube transcript into a polished audiobook script.

Rules:
1. Fix grammar, sentence fragments, and run-on sentences
2. Rewrite conversational YouTube speech into flowing audiobook prose. For example:
   - "hey guys welcome back to the channel" → removed entirely or rewritten
   - "so yeah um today we're gonna talk about" → cleaned up
   - "don't forget to like and subscribe" → removed
3. Remove filler words: um, uh, like, you know, sort of, kind of, basically, actually, literally, right?, okay so, so yeah
4. Fix incomplete sentences — if the speaker trails off, complete the thought naturally based on context
5. Combine short choppy segments into flowing paragraphs
6. Add natural paragraph breaks at topic transitions
7. Keep the original meaning, facts, and information INTACT — do not fabricate
8. Preserve the speaker's unique voice and personality
9. Remove stage directions like [Music], [Applause], [Laughter] unless they add narrative value
10. If the speaker repeats themselves, keep the best version

Respond with a JSON object:
{
  "script": "The full rewritten audiobook script as a single string with paragraph breaks (\\n\\n)",
  "segments": [
    {
      "paragraph": "First paragraph of the script",
      "emotion": "one of: neutral, excited, cheerful, sad, angry, calm, serious, friendly, fearful, gentle, surprised"
    }
  ]
}

Split the script into segments at natural paragraph breaks (topic changes). Each segment should be 1-3 sentences.
Assign each segment the emotion that best matches its content.
Keep the original language (Arabic, Hebrew, or English). Do NOT translate.
Return ONLY valid JSON, no other text."""


def _call_llm(transcript_text: str, language: str) -> dict:
    client = OpenAI(api_key=ZEN_API_KEY, base_url=ZEN_BASE_URL)

    lang_hint = {
        "ar": "The transcript is in Arabic. Write the audiobook script in Arabic.",
        "he": "The transcript is in Hebrew. Write the audiobook script in Hebrew.",
        "en": "The transcript is in English. Write the audiobook script in English.",
    }.get(language, "")

    resp = client.chat.completions.create(
        model=ZEN_MODEL,
        messages=[
            {"role": "system", "content": f"{REVIEW_PROMPT}\n\n{lang_hint}"},
            {"role": "user", "content": transcript_text},
        ],
        temperature=0.3,
    )

    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("LLM returned empty response")

    data = _extract_json(content)
    if data is None:
        raise RuntimeError(f"LLM returned invalid JSON: {content[:300]}")

    return data


def _extract_json(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        obj = json.loads(content[start:end])
        return obj
    except (ValueError, json.JSONDecodeError):
        pass

    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        arr = json.loads(content[start:end])
        return {"segments": arr}
    except (ValueError, json.JSONDecodeError):
        return None


def batch_segments(segments: list[dict], max_batch_chars: int = 6000) -> list[list[dict]]:
    batches = []
    current = []
    current_len = 0

    for seg in segments:
        text_len = len(seg["text"])
        if current_len + text_len > max_batch_chars and current:
            batches.append(current)
            current = []
            current_len = 0
        current.append(seg)
        current_len += text_len

    if current:
        batches.append(current)

    return batches


async def enhance_transcript(segments: list[dict], language: str) -> list[dict]:
    if not segments:
        return [{"text": "No transcript available.", "emotion": "neutral"}]

    batches = batch_segments(segments)
    enhanced = []

    for batch in batches:
        transcript_text = "\n".join(
            f"[{i}] {s['text']}" for i, s in enumerate(batch)
        )

        try:
            result = _call_llm(transcript_text, language)
        except Exception as e:
            result = {"script": " ".join(s["text"] for s in batch), "segments": [
                {"paragraph": s["text"], "emotion": "neutral"} for s in batch
            ]}

        segs = result.get("segments", [])
        script = result.get("script", "")

        if not segs and script:
            segs = [{"paragraph": script, "emotion": "neutral"}]

        for item in segs:
            enhanced.append({
                "text": item.get("paragraph", item.get("text", "")),
                "emotion": item.get("emotion", "neutral"),
            })

    if not enhanced:
        return [{"text": " ".join(s["text"] for s in segments), "emotion": "neutral"}]

    return enhanced


EMOTION_PROFILE: dict[str, dict[str, str]] = {
    "neutral": {"rate": "0%", "pitch": "0Hz", "volume": "0%"},
    "excited": {"rate": "+8%", "pitch": "+15Hz", "volume": "+5%"},
    "cheerful": {"rate": "+5%", "pitch": "+10Hz", "volume": "+3%"},
    "sad": {"rate": "-5%", "pitch": "-10Hz", "volume": "-5%"},
    "angry": {"rate": "+3%", "pitch": "+5Hz", "volume": "+10%"},
    "fearful": {"rate": "+10%", "pitch": "+20Hz", "volume": "+3%"},
    "calm": {"rate": "-8%", "pitch": "-5Hz", "volume": "-8%"},
    "serious": {"rate": "-3%", "pitch": "-3Hz", "volume": "0%"},
    "friendly": {"rate": "+3%", "pitch": "+5Hz", "volume": "+3%"},
    "gentle": {"rate": "-5%", "pitch": "-8Hz", "volume": "-5%"},
    "surprised": {"rate": "+12%", "pitch": "+25Hz", "volume": "+5%"},
}


def build_ssml(text: str, emotion: str, voice: str, lang: str = "en") -> str:
    prosody = EMOTION_PROFILE.get(emotion, EMOTION_PROFILE["neutral"])

    lang_map = {"ar": "ar-SA", "he": "he-IL", "en": "en-US"}
    xml_lang = lang_map.get(lang, "en-US")

    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="https://www.w3.org/2001/mstts" '
        f'xml:lang="{xml_lang}">'
        f'<voice name="{voice}">'
        f'<prosody rate="{prosody["rate"]}" pitch="{prosody["pitch"]}" volume="{prosody["volume"]}">'
        f"{escaped}"
        f"</prosody>"
        f"</voice>"
        f"</speak>"
    )
