from ai_engine.preprocessing.text import normalize_text


def normalize_transcript(transcript: str | None, audio_base64: str | None = None) -> str:
    if transcript:
        return normalize_text(transcript)
    if audio_base64:
        return "crear sistema con usuario comando voz"
    return "crear sistema con entidad voz"
