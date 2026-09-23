"""
Voice-to-text for the voice note feature — transcribes a citizen's voice
note into text using OpenAI's Whisper (open-source, runs locally, no API
key or internet call needed).

Loaded once at import time so the model isn't reloaded on every request —
important since Whisper models take a few seconds to load.

Model size trade-off:
- "tiny"/"base": fast, runs fine on CPU, lower accuracy
- "small"/"medium": better accuracy, needs more RAM/CPU time or a GPU
Start with "base" and only move up if transcription quality is too poor
for real submissions.
"""

import whisper

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def transcribe_voice_note(audio_path: str) -> dict:
    """
    Returns:
    {
        "status": "ok" | "error",
        "text": str | None,
        "language": str | None,
        "error": str | None,
    }

    Never raises — a failed transcription (corrupt file, unsupported format)
    returns a clear error status instead of crashing the request.
    """
    try:
        model = _get_model()
        result = model.transcribe(audio_path)
        return {
            "status": "ok",
            "text": result.get("text", "").strip(),
            "language": result.get("language"),
            "error": None,
        }
    except Exception as e:  # noqa: BLE001 — intentionally broad, this is a boundary function
        return {"status": "error", "text": None, "language": None, "error": str(e)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python voice_to_text.py <audio_path>")
        sys.exit(1)
    print(transcribe_voice_note(sys.argv[1]))
