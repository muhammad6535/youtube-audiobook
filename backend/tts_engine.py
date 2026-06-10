import asyncio

LANGUAGE_VOICES = {
    "ar": {
        "label": "Arabic",
        "edge_tts": [
            "ar-EG-SalmaNeural",
            "ar-SA-HamedNeural",
            "ar-AE-FatimaNeural",
            "ar-QA-MoazNeural",
        ],
    },
    "he": {
        "label": "Hebrew",
        "edge_tts": [
            "he-IL-HilaNeural",
            "he-IL-AvriNeural",
        ],
    },
    "en": {
        "label": "English",
        "edge_tts": [
            "en-US-JennyNeural",
            "en-US-GuyNeural",
            "en-GB-SoniaNeural",
            "en-GB-RyanNeural",
            "en-AU-NatashaNeural",
        ],
    },
}


def get_supported_languages() -> dict:
    return {code: info["label"] for code, info in LANGUAGE_VOICES.items()}


def get_voices_for_language(lang: str) -> dict:
    info = LANGUAGE_VOICES.get(lang)
    if not info:
        return {}
    voices = {}
    for backend, voice_list in info.items():
        if backend == "label":
            continue
        for v in voice_list:
            voices[v] = {"backend": backend, "name": v}
    return voices


async def synthesize(text: str, voice: str, lang: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data
