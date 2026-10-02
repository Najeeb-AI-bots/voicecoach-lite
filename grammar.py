"""
grammar.py — real grammar/style analysis for VoiceCoach Lite.

Uses language_tool_python (the LanguageTool engine) to detect genuine
grammatical errors — tense, subject-verb agreement, article misuse,
punctuation, word choice — not just keyword rules.

Degrades gracefully: if LanguageTool can't initialize (e.g. no Java on the
host), falls back to a lightweight heuristic so the app always returns something.
"""

import re

# Lightweight fallbacks used only if LanguageTool is unavailable.
_FALLBACK_PATTERNS = [
    (" dont ", "don't", "Missing apostrophe: 'don't'."),
    (" cant ", "can't", "Missing apostrophe: 'can't'."),
    (" wont ", "won't", "Missing apostrophe: 'won't'."),
    (" alot ", "a lot", "'a lot' is two words."),
    (" could of ", "could have", "Use 'could have', not 'could of'."),
    (" should of ", "should have", "Use 'should have', not 'should of'."),
    (" would of ", "would have", "Use 'would have', not 'would of'."),
    (" more better ", "better", "Double comparative: use 'better'."),
    (" theres ", "there's", "Missing apostrophe: 'there's'."),
]


def check_grammar(transcript: str) -> dict:
    """Return {error_count, errors:[{message, context, suggestion, rule}], engine}."""
    if not transcript or transcript.startswith("(no transcript"):
        return {"error_count": 0, "errors": [], "engine": "none"}

    # Primary: LanguageTool (real grammar engine)
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool("en-US")
        matches = tool.check(transcript)
        errors = []
        for m in matches[:25]:
            errors.append({
                "message": m.message,
                "context": m.context,
                "suggestion": ", ".join(m.replacements[:3]) if m.replacements else "",
                "rule": m.ruleId,
            })
        try:
            tool.close()
        except Exception:
            pass
        return {"error_count": len(matches), "errors": errors, "engine": "LanguageTool"}
    except Exception:
        pass

    # Fallback: lightweight heuristic (case-aware)
    low = " " + transcript.lower() + " "
    errors = []
    for bad, good, msg in _FALLBACK_PATTERNS:
        if bad in low:
            errors.append({"message": msg, "context": bad.strip(),
                           "suggestion": good, "rule": "FALLBACK"})
    # standalone lowercase 'i' — check ORIGINAL case so a correct 'I' isn't flagged
    if re.search(r"\bi\b", transcript):
        errors.append({"message": "Capitalize the pronoun 'I'.", "context": "i",
                       "suggestion": "I", "rule": "FALLBACK"})
    return {"error_count": len(errors), "errors": errors, "engine": "heuristic-fallback"}


def grammar_score(error_count: int, word_count: int) -> int:
    """0-100 grammar score: fewer errors per 100 words = higher."""
    if not word_count:
        return 100
    errors_per_100 = (error_count / word_count) * 100
    return max(0, min(100, round(100 - errors_per_100 * 12)))
