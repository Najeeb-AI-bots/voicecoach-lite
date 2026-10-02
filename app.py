"""
VoiceCoach Lite — AI Public-Speaking Coach (Streamlit)

Upload a short speech clip (or paste a transcript). The app analyzes delivery
(pace, pitch, energy, pauses, fillers), estimates confidence, and returns AI
coaching feedback.

Open-source demo of a full desktop app (Flet + Vosk + librosa + AWS Bedrock).
Deploys on Streamlit Community Cloud — same flow as EscalaFlow / AuditLens.
"""

import streamlit as st

from analysis import analyze_audio, analyze_text, confidence_score
from transcribe import transcribe
from coach import coach

st.set_page_config(page_title="VoiceCoach Lite", page_icon="🎙️", layout="wide")

st.title("🎙️ VoiceCoach Lite — AI Public-Speaking Coach")
st.caption(
    "Upload a short speech clip and get instant coaching on pace, tone, fillers, "
    "and confidence. Open-source demo of a full desktop app "
    "(Flet · Vosk · librosa · AWS Bedrock). Built by Mohammed Abdul Najeeb."
)

with st.sidebar:
    st.header("⚙️ Configuration")
    provider = st.selectbox(
        "Coaching engine",
        ["Rule-based (no key, free)", "Anthropic Claude (bring your own key)"],
    )
    api_key = ""
    if provider.startswith("Anthropic"):
        api_key = st.text_input("Anthropic API key", type="password",
                                help="Used only in this session, never stored.")
    st.markdown("---")
    st.caption("Tip: a 20-60 second clip works best. If transcription isn't "
               "available on the host, paste your transcript below for full analysis.")

col1, col2 = st.columns(2)
with col1:
    audio_file = st.file_uploader("🎧 Upload speech clip (WAV/MP3/M4A)",
                                  type=["wav", "mp3", "m4a", "ogg", "flac"])
with col2:
    manual = st.text_area("📝 Transcript (optional — paste if STT unavailable)", height=120)

if st.button("🔎 Analyze my delivery", type="primary"):
    if not audio_file and not manual.strip():
        st.warning("Please upload an audio clip or paste a transcript.")
        st.stop()

    # Persist uploaded audio to a temp path for librosa
    audio_path = None
    if audio_file:
        import tempfile, os
        suffix = os.path.splitext(audio_file.name)[1] or ".wav"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(audio_file.read())
        tmp.flush()
        audio_path = tmp.name

    with st.spinner("Analyzing…"):
        acoustic = analyze_audio(audio_path) if audio_path else {"duration_s": None, "engine": "none"}
        transcript = manual.strip()
        if not transcript and audio_path:
            transcript = transcribe(audio_path)
        if not transcript:
            transcript = "(no transcript available — showing acoustic metrics only)"
        text = analyze_text(transcript, acoustic.get("duration_s"))
        conf = confidence_score(acoustic, text)
        feedback = coach(acoustic, text, conf, transcript, provider=provider, api_key=api_key)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Confidence", f"{conf}/100")
    m2.metric("Pace (WPM)", text.get("wpm") or "—")
    m3.metric("Filler rate", f"{text.get('filler_rate_pct')}%")
    m4.metric("Words", text.get("n_words"))

    st.subheader("📊 Delivery Metrics")
    st.markdown(
        f"| Metric | Value |\n|---|---|\n"
        f"| Duration | {acoustic.get('duration_s')} s |\n"
        f"| Pitch variation | {acoustic.get('pitch_var_hz')} Hz |\n"
        f"| Energy variation | {acoustic.get('energy_var')} |\n"
        f"| Pauses | {acoustic.get('n_pauses')} (longest {acoustic.get('longest_pause_s')}s) |\n"
        f"| Filler words | {text.get('filler_count')} |\n"
        f"| Analysis engine | {acoustic.get('engine')} |\n"
    )

    st.subheader("📝 Transcript")
    st.text(transcript)

    st.subheader("🎯 Coaching Feedback")
    st.text_area("", feedback, height=240)

st.markdown("---")
st.caption(
    "Built by Mohammed Abdul Najeeb · open-source demo of a production voice-coaching "
    "app (Flet desktop original). No data stored; audio processed in-session only."
)
