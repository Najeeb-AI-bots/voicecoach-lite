"""
translator.py — live translation for VoiceCoach Lite.

Engines in order: Claude (if key) -> Google (retry) -> MyMemory (fallback) -> message.
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
            prompt = ("Translate from " + source_label + " to " + target_label + ". Return ONLY the translation.\n\n" + text)
            msg = client.messages.create(model="claude-sonnet-4-5", max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            return {"translated": msg.content[0].text.strip(), "engine": "Claude", "tts_lang": tts}
        except Exception:
            pass

    try:
        from deep_translator import GoogleTranslator
    except ModuleNotFoundError:
        return {"translated": "[Translator package missing: deep-translator not installed. Add deep-translator>=1.11 to requirements.txt and redeploy.]", "engine": "unavailable", "tts_lang": tts}

    import time
    source = "auto" if src == "auto" else src
    last_err = None

    for attempt in range(3):
        try:
            out = GoogleTranslator(source=source, target=tgt).translate(text)
            if out and out.strip():
                return {"translated": out, "engine": "Google", "tts_lang": tts}
        except Exception as e:
            last_err = e
            m = str(e).lower()
            rate = ("too many requests" in m or "429" in m or "5 requests per second" in m)
            if rate and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            break

    try:
        from deep_translator import MyMemoryTranslator
        mm_src = "en-GB" if source == "auto" else source
        out = MyMemoryTranslator(source=mm_src, target=tgt).translate(text)
        if out and out.strip():
            return {"translated": out, "engine": "MyMemory (fallback)", "tts_lang": tts}
    except Exception as e:
        last_err = e

    if last_err and ("too many requests" in str(last_err).lower() or "429" in str(last_err).lower()):
        return {"translated": "Both free translation services are busy right now (rate-limited on this shared server). Please wait about 10 seconds and press Translate again. For unlimited translation, pick Anthropic Claude in the sidebar and add your key.", "engine": "rate-limited", "tts_lang": tts}
    return {"translated": "[Translation failed: " + str(last_err) + ". Please try again in a moment, or pick Anthropic Claude in the sidebar and add your key.]", "engine": "unavailable", "tts_lang": tts}
