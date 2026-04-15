# YouTube Video Summarizer

Desktop-first YouTube summarizer built with Python and PySide6.

## What changed

- Native desktop UI instead of opening Streamlit in the browser
- Local configuration screen for AI provider keys
- Background processing so the window stays responsive
- Summary, transcript, and video chat inside the same desktop app
- Streamlit entry point kept only as a compatibility note

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python desktop_app.py
```

## Build Windows executable

```bash
build_windows.bat
```

## Environment and config

API keys are stored locally in:

```text
~/.youtube_summarizer/config.json
```

Supported providers:

- Groq
- OpenAI
- Anthropic

Transcript priority:

1. YouTube captions
2. Audio download with yt-dlp
3. Whisper transcription via Groq or OpenAI
