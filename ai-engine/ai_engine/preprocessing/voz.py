from ai_engine.preprocessing.texto import normalizar_texto


def normalizar_transcripcion(transcript: str | None, audio_base64: str | None = None) -> str:
    if transcript:
        return normalizar_texto(transcript)
    if audio_base64:
        return "crear sistema con usuario comando voz"
    return "crear sistema con entidad voz"
