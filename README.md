# 🎙️ VoiceCoach Lite — AI Public-Speaking Coach

> Upload a speech clip and get instant AI coaching: pace, pitch, energy, confidence, and filler-word analysis — plus LLM-generated feedback on your delivery.

**Live demo:** _[add Streamlit link here]_ · **Built by:** [Mohammed Abdul Najeeb](https://github.com/Najeeb-AI-bots)

> 💡 An open-source slice of a full desktop AI coaching app I built with Flet, Vosk, librosa, and AWS Bedrock. This public version demonstrates the core analysis + feedback loop.

---

## What it does

1. **Upload** a short speech clip (or paste a transcript)
2. **Analyze** the audio with `librosa` — pace (words/min), pitch variation, energy, pauses, estimated confidence
3. **Transcribe** with `faster-whisper` (or paste a transcript if STT isn't available on the host)
4. **Coach** via an LLM (AWS Bedrock → Claude, or bring-your-own-key) — feedback on pace, tone, fillers, and confidence
5. **Score** confidence 0–100 from the combined signals

## Why it matters

Public-speaking feedback is usually subjective and infrequent. VoiceCoach Lite shows how multimodal AI (audio features + transcript + LLM) can give objective, instant, repeatable coaching.

## Architecture

```
audio ──▶ librosa (acoustic features) ──┐
      └─▶ faster-whisper (transcript) ───┼──▶ LLM Coach (Bedrock/Claude) ──▶ Coaching + Confidence Score
                                          │
                               filler + pace analysis
```

## Tech stack

- **librosa** — pitch, energy, pace, pause, confidence analysis
- **faster-whisper** — speech-to-text (full desktop app uses offline Vosk)
- **AWS Bedrock → Claude** (or bring-your-own key) — coaching feedback
- **Streamlit** — web UI (desktop original built in Flet)

## Run locally

```bash
git clone https://github.com/Najeeb-AI-bots/voicecoach-lite
cd voicecoach-lite
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud — same as my other apps)

1. Push these files to a public GitHub repo `voicecoach-lite`
2. share.streamlit.io → Create app → repo `Najeeb-AI-bots/voicecoach-lite`, branch `main`, main file `app.py`
3. Deploy → live at `https://<your-subdomain>.streamlit.app`

Runs free with no API key (rule-based coaching + metrics). Add an Anthropic key in the sidebar for Claude-powered feedback.

## Skills demonstrated

Multimodal AI · Audio signal analysis · Speech-to-text · LLM integration (Bedrock) · End-to-end app build

## License

MIT.
