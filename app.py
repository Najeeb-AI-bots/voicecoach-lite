"""
VoiceCoach Lite — AI Public-Speaking Coach (Streamlit)

Record a clip live in the browser (or upload / paste a transcript). The app
analyzes delivery (pace, pitch, energy, pauses, fillers), checks grammar,
estimates confidence, returns AI coaching feedback — and reads it aloud like a
voice tutor via the browser's speech synthesis.

Open-source demo of a full desktop app (Flet + Vosk + librosa + AWS Bedrock).
Deploys on Streamlit Community Cloud — same flow as EscalaFlow / AuditLens.
"""

import json as _json
import streamlit as st
import streamlit.components.v1 as components

from analysis import analyze_audio, analyze_text, confidence_score
from transcribe import transcribe
from coach import coach
from grammar import check_grammar, grammar_score

st.set_page_config(page_title="VoiceCoach Lite", page_icon="🎙️", layout="wide")

st.title("🎙️ VoiceCoach Lite — AI Public-Speaking Coach")
st.caption(
    "Record a short clip and get instant coaching on pace, tone, fillers, grammar, "
    "and confidence — read aloud like a voice tutor. Open-source demo of a full "
    "desktop app (Flet · Vosk · librosa · AWS Bedrock). Built by Mohammed Abdul Najeeb."
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
    speak_auto = st.checkbox("🔊 Auto-play spoken feedback", value=True)
    st.caption("Tip: a 20-60 second clip works best. If transcription isn't "
               "available on the host, paste your transcript for full analysis.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**🎙️ Record live**")
    recorded = st.audio_input("Click the mic to record your speech")
    st.markdown("**— or upload a file —**")
    audio_file = st.file_uploader("Upload a clip (WAV/MP3/M4A)",
                                  type=["wav", "mp3", "m4a", "ogg", "flac"],
                                  label_visibility="collapsed")
with col2:
    manual = st.text_area("📝 Transcript (optional — paste if STT unavailable)", height=160)

if st.button("🔎 Analyze my delivery", type="primary"):
    audio_source = recorded or audio_file
    if not audio_source and not manual.strip():
        st.warning("Please record, upload an audio clip, or paste a transcript.")
        st.stop()

    audio_path = None
    if audio_source:
        import tempfile, os
        name = getattr(audio_source, "name", "recording.wav")
        suffix = os.path.splitext(name)[1] or ".wav"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(audio_source.read())
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
        gram = check_grammar(transcript)
        gscore = grammar_score(gram["error_count"], text.get("n_words", 0))
        feedback = coach(acoustic, text, conf, transcript, provider=provider, api_key=api_key)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Confidence", f"{conf}/100")
    m2.metric("Grammar", f"{gscore}/100")
    m3.metric("Pace (WPM)", text.get("wpm") or "—")
    m4.metric("Filler rate", f"{text.get('filler_rate_pct')}%")
    m5.metric("Words", text.get("n_words"))

    st.subheader("📊 Delivery Metrics")
    st.markdown(
        f"| Metric | Value |\n|---|---|\n"
        f"| Duration | {acoustic.get('duration_s')} s |\n"
        f"| Pitch variation | {acoustic.get('pitch_var_hz')} Hz |\n"
        f"| Energy variation | {acoustic.get('energy_var')} |\n"
        f"| Pauses | {acoustic.get('n_pauses')} (longest {acoustic.get('longest_pause_s')}s) |\n"
        f"| Filler words | {text.get('filler_count')} |\n"
        f"| Grammar issues | {gram['error_count']} ({gram['engine']}) |\n"
        f"| Analysis engine | {acoustic.get('engine')} |\n"
    )

    st.subheader("✍️ Grammar & Style")
    if gram["error_count"] == 0:
        st.success("No grammar issues detected. 👏")
    else:
        st.write(f"**{gram['error_count']} issue(s) found** (engine: {gram['engine']}):")
        for e in gram["errors"]:
            sugg = f" → *{e['suggestion']}*" if e["suggestion"] else ""
            st.markdown(f"- **{e['message']}**{sugg}  \n"
                        f"  <span style='color:#888;font-size:0.9em'>…{e['context']}…</span>",
                        unsafe_allow_html=True)

    st.subheader("📝 Transcript")
    st.text(transcript)

    st.subheader("🎯 Coaching Feedback")
    st.text_area("", feedback, height=240)

    # 🔊 Voice tutor — speak the feedback aloud (browser speech synthesis, no install)
    st.subheader("🔊 Hear Your Coach")
    st.caption("Your coaching feedback, read aloud — like a voice tutor.")
    safe = _json.dumps(feedback)
    autoplay = "speak();" if speak_auto else ""
    components.html(f"""
        <div style="font-family:sans-serif">
          <button onclick="speak()" style="padding:10px 18px;border:none;border-radius:8px;
            background:#6554c0;color:white;font-size:14px;font-weight:600;cursor:pointer;">
            ▶ Play coaching feedback
          </button>
          <button onclick="window.speechSynthesis.cancel()" style="padding:10px 18px;margin-left:8px;
            border:1px solid #ccc;border-radius:8px;background:white;cursor:pointer;">⏹ Stop</button>
        </div>
        <script>
          function speak() {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance({safe});
            u.rate = 1.0; u.pitch = 1.0; u.lang = 'en-US';
            window.speechSynthesis.speak(u);
          }}
          {autoplay}
        </script>
    """, height=80)

st.markdown("---")
st.caption(
    "Built by Mohammed Abdul Najeeb · open-source demo of a production voice-coaching "
    "app (Flet desktop original). Pairs with the mcp-speech-coach MCP server. "
    "No data stored; audio processed in-session only."
)
