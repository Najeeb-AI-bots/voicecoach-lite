"""
coach.py — turns objective speech metrics into coaching feedback.

Two modes:
  - "Rule-based" : no API key, free. Deterministic feedback from thresholds.
  - "Anthropic Claude" : bring-your-own-key. Natural, encouraging coaching.

Mirrors the AWS Bedrock -> Claude coaching loop from the full Voice Coach Pro
desktop app, in a web-deployable form.
"""


def _rule_based(acoustic: dict, text: dict, confidence: int) -> str:
    tips = []
    wpm = text.get("wpm")
    if wpm:
        if wpm > 180:
            tips.append(f"⏩ Pace: {wpm} wpm is fast — slow down and add deliberate pauses so key points land.")
        elif wpm < 100:
            tips.append(f"⏪ Pace: {wpm} wpm is slow — pick up energy to keep listeners engaged.")
        else:
            tips.append(f"✅ Pace: {wpm} wpm is in the ideal conversational range.")
    fr = text.get("filler_rate_pct", 0)
    if fr > 4:
        tips.append(f"🗣️ Fillers: {fr}% filler words ({text.get('filler_count')} total) — pause silently instead of saying 'um/like'.")
    else:
        tips.append(f"✅ Fillers: {fr}% — clean, minimal filler use.")
    pv = acoustic.get("pitch_var_hz", 0)
    if pv and pv < 10:
        tips.append("🎵 Tone: pitch is fairly monotone — vary intonation to emphasize important words.")
    elif pv and pv > 25:
        tips.append("✅ Tone: good pitch variation — your delivery sounds dynamic.")
    lp = acoustic.get("longest_pause_s", 0)
    if lp and lp > 3:
        tips.append(f"⏸️ Pauses: longest pause was {lp}s — a bit long; keep momentum between points.")

    verdict = ("Strong, confident delivery." if confidence >= 75
               else "Solid foundation with clear areas to tighten." if confidence >= 55
               else "Good effort — focus on pace and fillers to build confidence.")
    return f"Confidence estimate: {confidence}/100 — {verdict}\n\n" + "\n".join(tips)


def _claude(acoustic: dict, text: dict, confidence: int, transcript: str, api_key: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "You are a supportive public-speaking coach. Based on these objective "
            "metrics and the transcript, give concise, encouraging, specific feedback "
            "on pace, tone, fillers, and confidence. Max 150 words, plain text.\n\n"
            f"Metrics: {acoustic} | {text} | confidence={confidence}/100\n\n"
            f"Transcript: {transcript[:1500]}"
        )
        msg = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return _rule_based(acoustic, text, confidence) + f"\n\n[LLM coaching unavailable ({e}); used rule-based.]"


def coach(acoustic, text, confidence, transcript="", provider="Rule-based", api_key=""):
    if provider.startswith("Anthropic") and api_key:
        return _claude(acoustic, text, confidence, transcript, api_key)
    return _rule_based(acoustic, text, confidence)
