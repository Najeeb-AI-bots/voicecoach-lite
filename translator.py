"""
translator.py — live translation for VoiceCoach Lite.

Translates text between languages. Tries engines in order of quality:
  1. deep-translator (Google backend) — free, no key, broad language support
  2. Anthropic Claude — if a key is provided (highest quality / nuance)
  3. graceful message if neither is available

Returns a structured dict so the UI can render + speak the result.
"""

LANGUAGES = {
    "English": "en", "Hindi": "hi", "Urdu": "ur", "Telugu": "te", "Arabic": "ar",
    "Chinese (Simplified)": "zh-CN", "French": "fr", "Spanish": "es", "German": "de",
    "Tamil": "ta", "Malayalam": "ml", "Bengali": "bn", "Russian": "ru",
    "Japanese": "ja", "Portuguese": "pt",
}

TTS_LANG = {
    "en": "en-US", "hi": "hi-IN", "ur": "ur-PK", "te": "te-IN", "ar": "ar-SA",
    "zh-CN": "zh-CN", "fr": "fr-FR", "es": "es-ES", "de": "de-DE", "ta": "ta-IN",
    "ml": "ml-IN", "bn": "bn-IN", "ru": "ru-RU", "ja": "ja-JP", "pt": "pt-PT",
}


def translate(text, source_label, target_label, api_key=""):
    """Translate text from source language to target language."""
    if not text or not text.strip():
        return {"translated": "", "engine": "none", "tts_lang": "en-US"}

    src = LANGUAGES.get(source_label, "auto")
    tgt = LANGUAGES.get(target_label, "en")
    tts = TTS_LANG.get(tgt, "en-US")

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = ("Translate the following text from " + source_label + " to " + target_label + ". Return ONLY the translation, no notes.\n\n" + text)
            msg = client.messages.create(model="claude-sonnet-4-5", max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            return {"translated": msg.content[0].text.strip(), "engine": "Claude", "tts_lang": tts}
        except Exception:
            pass

    try:
        from deep_translator import GoogleTranslator
    except ModuleNotFoundError:
        return {"translated": "[Translator package missing: deep-translator not installed. Add deep-translator>=1.11 to requirements.txt and redeploy. No API key needed for free translation.]", "engine": "unavailable", "tts_lang": tts}

    import time
    source = "auto" if src == "auto" else src
    last_err = None
    for attempt in range(3):
        try:
            out = GoogleTranslator(source=source, target=tgt).translate(text)
            return {"translated": out, "engine": "Google (deep-translator)", "tts_lang": tts}
        except Exception as e:
            last_err = e
            m = str(e).lower()
            rate = ("too many requests" in m or "429" in m or "5 requests per second" in m)
            if rate and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            break

    if last_err and ("too many requests" in str(last_err).lower() or "429" in str(last_err).lower()):
        return {"translated": "Google's free translation service is rate-limiting this shared server right now (too many requests). Please wait about 10 seconds and press Translate again. Tip: for unlimited, higher-quality translation, pick Anthropic Claude in the sidebar and add your key.", "engine": "rate-limited", "tts_lang": tts}
    return {"translated": "[Translation failed: " + str(last_err) + ". Try again, or add an Anthropic key in the sidebar for Claude translation.]", "engine": "unavailable", "tts_lang": tts}
