# 🎙️ VoiceCoach Lite — AI Speaking Coach + Live Translator

> Speak, and get honest feedback on how you sounded. Then practise with warm-ups, tongue twisters and a 30-day programme.

**Live demo:** https://voicecoach-lite.streamlit.app/
**Built by:** [Mohammed Abdul Najeeb](https://github.com/Najeeb-AI-bots) · [LinkedIn](https://www.linkedin.com/in/abdul-najeeb-27010347/)

This is the web demo of a fuller desktop app I built. The same coaching engine also runs as two MCP servers: [mcp-speech-coach](https://github.com/Najeeb-AI-bots/mcp-speech-coach) and [mcp-grammar-coach](https://github.com/Najeeb-AI-bots/mcp-grammar-coach).

---

## Why I built it

Most people don't need a speaking course. They need practice, and someone honest telling them how it went. VoiceCoach Lite gives you that feedback in seconds, so you can practise every day.

## What it does

| Feature | What you get |
|---|---|
| 🎙️ **Speaking Coach** | Record or upload a clip. It writes down what you said and measures your pace (words per minute), pauses, filler words, pitch variation, energy and a confidence score |
| ✍️ **Grammar & Style** | Finds grammar, spelling and style mistakes in what you said |
| 🎯 **Coaching Feedback** | Clear tips on what to fix next, with an option to hear your coach read them aloud |
| 🌐 **Live Translator** | Translate between 15 languages (including English, Hindi, Urdu, Telugu, Arabic) and hear the result spoken aloud |
| 🔥 **Vocal Warm-Ups** | A short routine to get your voice ready |
| 👅 **Tongue Twisters** | Sorted by difficulty level |
| 🗣️ **Practice Topics** | Topics and example speeches to practise with |
| 📅 **30-Day Programme** | A daily plan to build the habit |
| 📈 **Progress Tracking** | Session history so you can see how you improve |

## How it works

```
Your voice ─► transcribe.py (faster-whisper) ─► text
          │
          ├─► analysis.py  (librosa: pace, pauses, pitch, energy, fillers, confidence)
          ├─► grammar.py   (LanguageTool: grammar + style)
          └─► coach.py     (turns the metrics into clear tips)

Translator: Claude ─► Google (retry) ─► MyMemory (backup) ─► clear message if all fail
```

**Built to keep working:**
- If the audio library isn't available, the analysis falls back to simple estimates based on clip length, so the demo still runs.
- The translator moves to the next service if one fails, and every result says which service was used.

## Tech stack

Python · Streamlit · faster-whisper · librosa · LanguageTool · deep-translator · Claude (Anthropic) · pandas

## Run it locally

```bash
git clone https://github.com/Najeeb-AI-bots/voicecoach-lite.git
cd voicecoach-lite
pip install -r requirements.txt
streamlit run app.py
```

A Claude API key is optional. Without one, the translator uses the free services.

## Project files

| File | Purpose |
|---|---|
| `app.py` | The Streamlit app and all screens |
| `transcribe.py` | Speech to text |
| `analysis.py` | Voice and text measurements |
| `grammar.py` | Grammar check and score |
| `coach.py` | Coaching tips |
| `translator.py` | Live translation with backup services |
| `features_content.py` | Warm-ups, tongue twisters, topics, 30-day plan |

## Skills demonstrated

Speech analysis · Speech-to-text · Building a backup chain for services · LLM integration · Product design for daily use · Streamlit deployment

## License

MIT
