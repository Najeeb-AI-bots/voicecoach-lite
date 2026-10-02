"""
analysis.py — acoustic + text analysis for VoiceCoach Lite.

Extracts objective delivery metrics from a speech clip:
  - pace (words per minute)
  - pitch variation (monotone vs. dynamic)
  - energy / volume consistency
  - pauses (count + longest)
  - filler-word rate
  - estimated confidence score

Degrades gracefully: if librosa isn't available, falls back to duration-based
estimates so the demo still runs anywhere.
"""

import re

FILLERS = ["um", "uh", "like", "you know", "so", "actually", "basically", "literally"]


def analyze_audio(wav_path: str):
    """Return a dict of acoustic metrics. Uses librosa if available."""
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(wav_path, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        # Energy / RMS
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        energy_var = float(np.std(rms))

        # Pitch (f0) via pyin
        try:
            f0, voiced, _ = librosa.pyin(
                y, fmin=float(librosa.note_to_hz("C2")),
                fmax=float(librosa.note_to_hz("C7")), sr=sr)
            f0_valid = f0[~np.isnan(f0)] if f0 is not None else np.array([])
            pitch_mean = float(np.mean(f0_valid)) if f0_valid.size else 0.0
            pitch_var = float(np.std(f0_valid)) if f0_valid.size else 0.0
        except Exception:
            pitch_mean, pitch_var = 0.0, 0.0

        # Pauses via silence detection
        intervals = librosa.effects.split(y, top_db=30)
        n_pauses = max(0, len(intervals) - 1)
        longest_pause = 0.0
        for i in range(1, len(intervals)):
            gap = (intervals[i][0] - intervals[i - 1][1]) / sr
            longest_pause = max(longest_pause, gap)

        return {
            "duration_s": round(duration, 1),
            "energy_mean": round(energy_mean, 4),
            "energy_var": round(energy_var, 4),
            "pitch_mean_hz": round(pitch_mean, 1),
            "pitch_var_hz": round(pitch_var, 1),
            "n_pauses": n_pauses,
            "longest_pause_s": round(longest_pause, 2),
            "engine": "librosa",
        }
    except Exception as e:
        return {"duration_s": None, "engine": f"fallback ({e})"}


def analyze_text(transcript: str, duration_s: float | None):
    """Return pace, filler rate, and basic readability."""
    words = re.findall(r"\b\w+\b", transcript.lower())
    n_words = len(words)
    wpm = round(n_words / (duration_s / 60), 1) if duration_s else None

    filler_count = 0
    low = " " + transcript.lower() + " "
    for f in FILLERS:
        filler_count += low.count(" " + f + " ")
    filler_rate = round(100 * filler_count / n_words, 1) if n_words else 0.0

    return {
        "n_words": n_words,
        "wpm": wpm,
        "filler_count": filler_count,
        "filler_rate_pct": filler_rate,
    }


def confidence_score(acoustic: dict, text: dict) -> int:
    """Heuristic 0-100 confidence estimate from pace, pitch variation, fillers."""
    score = 70
    wpm = text.get("wpm")
    if wpm:
        # ideal ~130-160 wpm
        if 120 <= wpm <= 170:
            score += 10
        elif wpm < 90 or wpm > 200:
            score -= 15
    # pitch variation = dynamic (good); near-zero = monotone
    pv = acoustic.get("pitch_var_hz", 0)
    if pv and pv > 25:
        score += 8
    elif pv and pv < 10:
        score -= 8
    # fillers hurt
    fr = text.get("filler_rate_pct", 0)
    score -= min(20, int(fr * 2))
    return max(0, min(100, score))
