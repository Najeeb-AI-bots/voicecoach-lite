"""
VoiceCoach Lite — AI Speaking Coach + Live Translator + full training suite (Streamlit)

Modes:
  🎙️ Coach          — analyze English delivery (pace, grammar, fillers, confidence) + spoken feedback
  🌐 Translator      — translate text/speech across 15+ languages + spoken output
  🔥 Warm Up         — guided vocal warm-up drills
  👅 Tongue Twisters — articulation drills by difficulty
  🗣️ Practice Topics — speaking models + randomized prompts across 8 categories
  📅 30-Day Programme — the full structured speaking programme
  📈 Progress        — session history & trends

Open-source demo of a full desktop app (Flet + Vosk + librosa + AWS Bedrock).
Built by Mohammed Abdul Najeeb · deploys on Streamlit Community Cloud.
"""

import json as _json
import datetime as _dt
import random as _random
import streamlit as st
import streamlit.components.v1 as components

from analysis import analyze_audio, analyze_text, confidence_score
from transcribe import transcribe
from coach import coach
from grammar import check_grammar, grammar_score
from translator import translate, LANGUAGES, TTS_LANG
from features_content import (
    SPEAKING_MODELS, TOPIC_CATEGORIES, WARMUPS, TONGUE_TWISTERS,
    DAYS, PHASE_NAMES, PHASE_COLORS,
)

st.set_page_config(page_title="VoiceCoach Lite", page_icon="🎙️", layout="wide")

# ---------- modern styling ----------
st.markdown("""
<style>
  .stApp { background: linear-gradient(160deg, #0f1420 0%, #1b2a3a 100%); }
  .block-container { padding-top: 2rem; }
  h1, h2, h3, h4, p, label, .stMarkdown { color: #e8ecf3 !important; }
  .hero {
    background: linear-gradient(135deg, #6554c0 0%, #0b84ff 100%);
    border-radius: 18px; padding: 26px 30px; margin-bottom: 22px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  }
  .hero h1 { color:#fff !important; font-size:30px; margin:0; font-weight:800; }
  .hero p  { color:rgba(255,255,255,0.9) !important; margin:6px 0 0; font-size:14px; }
  .card {
    background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12);
    border-radius:14px; padding:18px 20px; margin-bottom:16px;
    backdrop-filter: blur(6px);
  }
  div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
    border-radius:12px; padding:10px 14px;
  }
  .stButton>button {
    background: linear-gradient(135deg,#6554c0,#0b84ff); color:#fff; border:none;
    border-radius:10px; font-weight:700; padding:10px 20px;
  }
  .stButton>button:hover { filter:brightness(1.1); }
  .badge { display:inline-block; background:rgba(11,132,255,0.2); color:#8fc7ff;
    border:1px solid rgba(11,132,255,0.4); border-radius:100px; padding:3px 12px;
    font-size:12px; font-weight:600; margin-right:6px; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state["history"] = []
if "prog_day" not in st.session_state:
    st.session_state["prog_day"] = 1
if "prog_done" not in st.session_state:
    st.session_state["prog_done"] = []

# ---------- hero ----------
st.markdown("""
<div class="hero">
  <h1>🎙️ VoiceCoach Lite</h1>
  <p>AI Speaking Coach &amp; Live Translator — analyze your delivery, drill your articulation,
  follow a 30-day programme, or translate across languages, with spoken feedback.</p>
  <div style="margin-top:12px">
    <span class="badge">Pace &amp; Fillers</span>
    <span class="badge">Grammar</span>
    <span class="badge">Warm Ups</span>
    <span class="badge">30-Day Programme</span>
    <span class="badge">15+ Languages</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.radio("Mode", [
        "🎙️ Coach (English)",
        "🌐 Translator",
        "🔥 Warm Up",
        "👅 Tongue Twisters",
        "🗣️ Practice Topics",
        "📅 30-Day Programme",
        "📈 Progress",
    ], index=0)

    st.markdown("---")
    st.subheader("🗣️ Voice")
    voice_choice = st.selectbox("Spoken-output voice", [
        "Male — Deep (default)", "Female — Warm (US)", "Male — Confident (US)",
        "Female — Crisp (UK)", "Male — Calm (UK)", "Female — Energetic (AU)",
    ])
    speak_auto = st.checkbox("🔊 Auto-play spoken output", value=True)

    st.markdown("---")
    provider = st.selectbox("AI engine",
                            ["Free (no key)", "Anthropic Claude (bring your own key)"])
    api_key = ""
    if provider.startswith("Anthropic"):
        api_key = st.text_input("Anthropic API key", type="password",
                                help="Used only in this session, never stored.")

_VOICE_MAP = {
    "Female — Warm (US)":      {"gender": "female", "lang": "en-US", "rate": 1.0, "pitch": 1.1},
    "Male — Confident (US)":   {"gender": "male",   "lang": "en-US", "rate": 1.0, "pitch": 0.95},
    "Female — Crisp (UK)":     {"gender": "female", "lang": "en-GB", "rate": 1.05, "pitch": 1.05},
    "Male — Calm (UK)":        {"gender": "male",   "lang": "en-GB", "rate": 0.95, "pitch": 0.9},
    "Female — Energetic (AU)": {"gender": "female", "lang": "en-AU", "rate": 1.1, "pitch": 1.15},
    "Male — Deep (default)":   {"gender": "male",   "lang": "en-US", "rate": 0.95, "pitch": 0.8},
}


def speak_widget(text: str, tts_lang: str, label: str):
    """Render a Play/Stop widget that speaks `text` in `tts_lang`."""
    vcfg = _VOICE_MAP[voice_choice]
    safe = _json.dumps(text)
    autoplay = "speak();" if speak_auto else ""
    components.html(f"""
      <div style="font-family:sans-serif">
        <button onclick="speak()" style="padding:10px 18px;border:none;border-radius:10px;
          background:linear-gradient(135deg,#6554c0,#0b84ff);color:white;font-weight:700;cursor:pointer;">
          ▶ {label}</button>
        <button onclick="window.speechSynthesis.cancel()" style="padding:10px 18px;margin-left:8px;
          border:1px solid #888;border-radius:10px;background:#1b2a3a;color:#fff;cursor:pointer;">⏹ Stop</button>
      </div>
      <script>
        function pickVoice(gender, lang) {{
          const voices = window.speechSynthesis.getVoices();
          const fem = ['female','samantha','victoria','zira','karen','moira','tessa','fiona'];
          const mal = ['male','daniel','alex','david','george','rishi','fred'];
          const hints = gender === 'female' ? fem : mal;
          let m = voices.find(v => v.lang === lang && hints.some(h => v.name.toLowerCase().includes(h)));
          if (!m) m = voices.find(v => v.lang === lang);
          if (!m) m = voices.find(v => v.lang.startsWith(lang.split('-')[0]));
          return m || null;
        }}
        function speak() {{
          window.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance({safe});
          u.rate = {vcfg['rate']}; u.pitch = {vcfg['pitch']}; u.lang = '{tts_lang}';
          const v = pickVoice('{vcfg['gender']}', '{tts_lang}');
          if (v) u.voice = v;
          window.speechSynthesis.speak(u);
        }}
        if (window.speechSynthesis.getVoices().length === 0) {{
          window.speechSynthesis.onvoiceschanged = () => {{ {autoplay} }};
        }} else {{ {autoplay} }}
      </script>
    """, height=70)


def _save_temp(upload, default_name="recording.wav"):
    import tempfile, os
    name = getattr(upload, "name", default_name)
    suffix = os.path.splitext(name)[1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload.read()); tmp.flush()
    return tmp.name


# ======================= TRANSLATOR MODE =======================
if mode == "🌐 Translator":
    st.subheader("🌐 Live Translator")
    langs = list(LANGUAGES.keys())
    c1, c2 = st.columns(2)
    with c1:
        src_lang = st.selectbox("From", langs, index=langs.index("English"))
    with c2:
        tgt_lang = st.selectbox("To", langs, index=langs.index("Hindi"))

    st.markdown("**🎙️ Speak or type what you want to translate**")
    rec = st.audio_input("Record speech to translate")
    src_text = st.text_area("Or type text", height=120,
                            placeholder="Type here, or record above…")

    if st.button("🌐 Translate", type="primary"):
        text_in = src_text.strip()
        stt_failed = False
        if not text_in and rec:
            with st.spinner("Transcribing…"):
                text_in = transcribe(_save_temp(rec)).strip()
            if not text_in:
                stt_failed = True

        if not text_in:
            if stt_failed:
                st.warning("🎙️ Your recording was captured, but automatic speech-to-text "
                           "isn't available on this hosted demo (the server can't run the "
                           "transcription model). **Please type the text above** and translate — "
                           "no API key needed.")
            else:
                st.warning("Please record or type something to translate.")
            st.stop()

        with st.spinner("Translating…"):
            result = translate(text_in, src_lang, tgt_lang, api_key=api_key)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**{src_lang} → {tgt_lang}**  ·  <span class='badge'>{result['engine']}</span>",
                    unsafe_allow_html=True)
        st.markdown(f"**Original:**  {text_in}")
        st.markdown(f"### {result['translated']}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("🔊 Hear the Translation")
        speak_widget(result["translated"], result["tts_lang"], f"Play in {tgt_lang}")

# ======================= WARM UP MODE =======================
elif mode == "🔥 Warm Up":
    st.subheader("🔥 Vocal Warm-Up Routine")
    st.caption("Run through these before any practice session to loosen your voice and reduce strain.")
    total = sum(w.get("duration", 30) for w in WARMUPS)
    st.markdown(f"<span class='badge'>{len(WARMUPS)} drills</span>"
                f"<span class='badge'>~{total}s total</span>", unsafe_allow_html=True)
    for i, w in enumerate(WARMUPS, 1):
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {w.get('icon','🎯')} {i}. {w['name']}  "
                        f"<span class='badge'>{w.get('duration',30)}s</span>", unsafe_allow_html=True)
            st.write(w["desc"])
            if w.get("benefit"):
                st.caption(f"💪 {w['benefit']}")
            speak_widget(f"{w['name']}. {w['desc']}", "en-US", f"▶ Read drill {i}")
            st.markdown('</div>', unsafe_allow_html=True)

# ======================= TONGUE TWISTERS MODE =======================
elif mode == "👅 Tongue Twisters":
    st.subheader("👅 Tongue Twisters")
    st.caption("Articulation drills. Start slow and clear, then speed up while keeping every sound crisp.")
    levels = sorted({t["level"] for t in TONGUE_TWISTERS},
                    key=lambda x: ["Easy", "Medium", "Hard"].index(x) if x in ["Easy", "Medium", "Hard"] else 9)
    pick = st.radio("Difficulty", ["All"] + levels, horizontal=True)
    shown = [t for t in TONGUE_TWISTERS if pick == "All" or t["level"] == pick]
    for i, t in enumerate(shown, 1):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**{i}. {t['text']}**")
        st.caption(f"🎚️ {t['level']} · 🎯 {t['focus']}")
        speak_widget(t["text"], "en-US", f"▶ Hear #{i}")
        st.markdown('</div>', unsafe_allow_html=True)

# ======================= PRACTICE TOPICS MODE =======================
elif mode == "🗣️ Practice Topics":
    st.subheader("🗣️ Practice Topics & Speaking Models")

    st.markdown("#### 1. Pick a speaking model (a structure for your answer)")
    model_name = st.selectbox("Speaking model", list(SPEAKING_MODELS.keys()))
    md = SPEAKING_MODELS[model_name]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### {md.get('icon','⭐')} {model_name}")
    st.markdown(f"**Structure:**  {md['cue']}")
    st.caption(f"💡 {md['tip']}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 2. Get a topic to practise")
    cat = st.selectbox("Category", list(TOPIC_CATEGORIES.keys()))
    colA, colB = st.columns([1, 3])
    if colA.button("🎲 Random topic"):
        st.session_state["cur_topic"] = _random.choice(TOPIC_CATEGORIES[cat])
    topic = st.session_state.get("cur_topic")
    if topic:
        colB.markdown(f"<div class='card'><b>Your topic:</b><br>🗨️ {topic}</div>",
                      unsafe_allow_html=True)
        speak_widget(f"Your topic. {topic}. Using the {model_name} structure.",
                     "en-US", "▶ Read my topic")
    st.info("Tip: speak for 60–90 seconds using the model structure above, then switch to "
            "🎙️ Coach mode and record the same answer to get scored feedback.")

# ======================= 30-DAY PROGRAMME MODE =======================
elif mode == "📅 30-Day Programme":
    st.subheader("📅 30-Day Speaking Programme")
    done = set(st.session_state["prog_done"])
    cur = st.session_state["prog_day"]
    st.progress(len(done) / 30.0, text=f"{len(done)} / 30 days complete")

    # phase legend
    st.markdown(
        " ".join(f"<span class='badge' style='background:{PHASE_COLORS.get(p,'#555')}33;"
                 f"border-color:{PHASE_COLORS.get(p,'#555')}'>{PHASE_NAMES.get(p,'')}</span>"
                 for p in sorted(PHASE_NAMES)),
        unsafe_allow_html=True)

    day = DAYS[min(cur - 1, 29)]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### Day {day['day']} — {day['title']}  "
                f"<span class='badge'>{PHASE_NAMES.get(day['phase'],'')}</span>", unsafe_allow_html=True)
    st.markdown(f"**🎯 Focus:** {day['focus']}")
    st.markdown(f"**🏋️ Drill:** {day['drill']}")
    st.caption(f"💡 {day['tip']}  ·  Suggested format: {day.get('format','—')}")
    speak_widget(f"Day {day['day']}, {day['title']}. {day['drill']}", "en-US", "▶ Read today's mission")
    st.markdown('</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    if cols[0].button("◀ Previous day", disabled=cur <= 1):
        st.session_state["prog_day"] = max(1, cur - 1); st.rerun()
    if cols[1].button("✅ Mark day complete"):
        if cur not in done:
            st.session_state["prog_done"].append(cur)
        if cur < 30:
            st.session_state["prog_day"] = cur + 1
        st.rerun()
    if cols[2].button("Next day ▶", disabled=cur >= 30):
        st.session_state["prog_day"] = min(30, cur + 1); st.rerun()

    with st.expander("📋 See the full 30-day plan"):
        for d in DAYS:
            mark = "✅" if d["day"] in done else ("👉" if d["day"] == cur else "▫️")
            st.markdown(f"{mark} **Day {d['day']}: {d['title']}** — {d['focus']}")

# ======================= PROGRESS MODE =======================
elif mode == "📈 Progress":
    st.subheader("📈 Your Progress")
    hist = st.session_state["history"]
    prog_done = st.session_state["prog_done"]
    c = st.columns(3)
    c[0].metric("Coaching sessions", len(hist))
    c[1].metric("Programme days done", f"{len(prog_done)}/30")
    if hist:
        best = max(h["confidence"] for h in hist)
        c[2].metric("Best confidence", f"{round(best/10,1)}/10")
    if hist:
        import pandas as pd
        df = pd.DataFrame(hist)
        df.index = [f"#{i+1}" for i in range(len(df))]
        st.dataframe(df, use_container_width=True)
        if len(df) > 1:
            st.line_chart(df[["confidence", "grammar"]])
        if st.button("🗑️ Clear coaching history"):
            st.session_state["history"] = []
            st.rerun()
    else:
        st.info("No coaching sessions yet — go to 🎙️ Coach, record or paste a transcript, "
                "and analyze your delivery to start building history.")

# ======================= COACH MODE =======================
else:
    st.subheader("🎙️ Speaking Coach")
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

        audio_path = _save_temp(audio_source) if audio_source else None

        with st.spinner("Analyzing…"):
            acoustic = analyze_audio(audio_path) if audio_path else {"duration_s": None, "engine": "none"}
            transcript = manual.strip()
            stt_failed = False
            if not transcript and audio_path:
                transcript = transcribe(audio_path).strip()
                if not transcript:
                    stt_failed = True
            if not transcript:
                transcript = "(no transcript available — showing acoustic metrics only)"
            text = analyze_text(transcript, acoustic.get("duration_s"))
            conf = confidence_score(acoustic, text)
            gram = check_grammar(transcript)
            gscore = grammar_score(gram["error_count"], text.get("n_words", 0))
            feedback = coach(acoustic, text, conf, transcript,
                             provider=("Anthropic" if api_key else "Rule-based"), api_key=api_key)

        if stt_failed:
            st.info("🎙️ Recording captured — but automatic transcription isn't available on this "
                    "hosted demo, so grammar/filler analysis is limited. Acoustic metrics "
                    "(pace, pitch, pauses) below are still from your audio. For full text "
                    "analysis, paste your transcript on the right.")

        st.session_state["history"].append({
            "time": _dt.datetime.now().strftime("%H:%M:%S"),
            "confidence": conf, "grammar": gscore, "wpm": text.get("wpm"),
            "filler_pct": text.get("filler_rate_pct"), "words": text.get("n_words"),
        })

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Confidence", f"{round(conf/10, 1)}/10")
        m2.metric("Grammar", f"{gscore}/100")
        m3.metric("Words per minute", text.get("wpm") or "—")
        m4.metric("Filler %", f"{text.get('filler_rate_pct')}%")
        m5.metric("Words", text.get("n_words"))

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"| Metric | Value |\n|---|---|\n"
            f"| Duration | {acoustic.get('duration_s')} s |\n"
            f"| Pitch variation | {acoustic.get('pitch_var_hz')} Hz |\n"
            f"| Pauses | {acoustic.get('n_pauses')} (longest {acoustic.get('longest_pause_s')}s) |\n"
            f"| Filler words | {text.get('filler_count')} |\n"
            f"| Grammar issues | {gram['error_count']} ({gram['engine']}) |\n"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if gram["error_count"]:
            st.subheader("✍️ Grammar & Style")
            for e in gram["errors"]:
                sugg = f" → *{e['suggestion']}*" if e["suggestion"] else ""
                st.markdown(f"- **{e['message']}**{sugg}  \n"
                            f"  <span style='color:#9aa7b8;font-size:0.9em'>…{e['context']}…</span>",
                            unsafe_allow_html=True)

        st.subheader("🎯 Coaching Feedback")
        st.text_area("", feedback, height=200)

        st.subheader("🔊 Hear Your Coach")
        speak_widget(feedback, "en-US", "Play coaching")

    # inline history
    if st.session_state["history"]:
        st.markdown("---")
        st.subheader("📈 Session History")
        import pandas as pd
        hist_df = pd.DataFrame(st.session_state["history"])
        hist_df.index = [f"#{i+1}" for i in range(len(hist_df))]
        st.dataframe(hist_df, use_container_width=True)
        if len(hist_df) > 1:
            st.line_chart(hist_df[["confidence", "grammar"]])

st.markdown("---")
st.caption("Built by Mohammed Abdul Najeeb · pairs with the mcp-speech-coach MCP server · "
           "no data stored server-side.")
