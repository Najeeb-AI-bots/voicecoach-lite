"""
translator.py — live translation for VoiceCoach Lite.

Translates text between languages. Tries engines in order of quality:
  1. deep-translator (Google backend) — free, no key, broad language support
  2. Anthropic Claude — if a key is provided (highest quality / nuance)
  3. graceful message if neither is available

Returns a structured dict so the UI can render + speak the result.
"""

# ISO codes for common languages (label -> code)
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Urdu": "ur",
    "Telugu": "te",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-CN",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Tamil": "ta",
    "Malayalam": "ml",
    "Bengali": "bn",
    "Russian": "ru",
    "Japanese": "ja",
    "Portuguese": "pt",
}

# Best-effort speech-synthesis locale per language (for the spoken output)
TTS_LANG = {
    "en": "en-US", "hi": "hi-IN", "ur": "ur-PK", "te": "te-IN", "ar": "ar-SA",
    "zh-CN": "zh-CN", "fr": "fr-FR", "es": "es-ES", "de": "de-DE", "ta": "ta-IN",
    "ml": "ml-IN", "bn": "bn-IN", "ru": "ru-RU", "ja": "ja-JP", "pt": "pt-PT",
}


def translate(text: str, source_label: str, target_label: str,
              api_key: str = "") -> dict:
    """Translate text from source language to target language."""
    if not text or not text.strip():
        return {"translated": "", "engine": "none", "tts_lang": "en-US"}

    src = LANGUAGES.get(source_label, "auto")
    tgt = LANGUAGES.get(target_label, "en")
    tts = TTS_LANG.get(tgt, "en-US")

    # 1. Claude (if key) — best quality
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = (f"Translate the following text from {source_label} to "
                      f"{target_label}. Return ONLY the translation, no notes.\n\n{text}")
            msg = client.messages.create(model="claude-sonnet-4-5", max_tokens=1000,
                                         messages=[{"role": "user", "content": prompt}])
            return {"translated": msg.content[0].text.strip(),
                    "engine": "Claude", "tts_lang": tts}
        except Exception:
            pass

    # 2. deep-translator (Google backend) — free, no key
    try:
        from deep_translator import GoogleTranslator
        source = "auto" if src == "auto" else src
        out = GoogleTranslator(source=source, target=tgt).translate(text)
        return {"translated": out, "engine": "Google (deep-translator)", "tts_lang": tts}
    except Exception as e:
        return {"translated": f"[Translation unavailable: {e}. Add an Anthropic key "
                              f"in the sidebar for Claude-powered translation.]",
                "engine": "unavailable", "tts_lang": tts}
