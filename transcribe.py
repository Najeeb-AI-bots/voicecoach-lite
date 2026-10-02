"""
transcribe.py — speech-to-text for VoiceCoach Lite.

The full desktop app uses Vosk (offline). For a lightweight public demo, this
tries faster-whisper if available, else returns a graceful message so the
acoustic analysis still works without a transcript.
"""


def transcribe(wav_path: str) -> str:
    # Try faster-whisper (small, CPU-friendly) if present
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base.en", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(wav_path)
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception:
        pass
    # Try SpeechRecognition + Google (needs internet) as a secondary path
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        return r.recognize_google(audio)
    except Exception:
        return ""
