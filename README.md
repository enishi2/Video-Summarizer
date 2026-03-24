# YouTube Video Summarizer with AI

A Python tool that automatically transcribes and summarizes YouTube videos. Available as a web app or command-line tool. After generating the summary, an interactive chatbot lets you ask questions about the video content.

Live demo: [video-summarizerenishi2.streamlit.app](https://video-summarizerenishi2.streamlit.app/)

---

## Features

- **Web interface** — runs in the browser via Streamlit, no terminal required
- **Automatic transcription** — uses YouTube captions when available, including auto-generated ones
- **Audio transcription** — when no captions exist, upload an audio file for Whisper transcription
- **Text correction** — AI fixes noise and common errors from automatic transcriptions
- **Structured summary** — generates a summary with main topic, key points, details, and conclusion
- **Multilingual summaries** — choose the summary language regardless of the video's original language
- **Chatbot** — ask questions about the video and get answers based on its content
- **Multiple AI providers** — automatically detects which provider is available (Groq, OpenAI, or Claude)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/enishi2/Video-Summarizer.git
cd Video-Summarizer
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install ffmpeg

Required to process audio files.

```bash
winget install ffmpeg        # Windows
brew install ffmpeg          # Mac
sudo apt install ffmpeg      # Linux
```

### 5. Configure API keys

Rename `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=gsk_your_key_here
OPENAI_API_KEY=            # optional
ANTHROPIC_API_KEY=         # optional
TRANSCRIPT_LANGUAGES=pt,en
```

> Groq is **free** — get your API key at [console.groq.com](https://console.groq.com)

### 6. Run

**Web interface (recommended):**

```bash
streamlit run app.py
```

**Command line:**

```bash
python main.py
```

---

## Web Interface

The Streamlit interface runs locally at `http://localhost:8501` and is also available as a live deployment.

1. Paste a YouTube URL
2. Select the summary language
3. Click Summarize
4. Read the structured summary
5. Ask questions in the chatbot

If a video has no captions, the app guides you to upload an audio file instead.

---

## Supported Summary Languages

English, Portuguese, Spanish, French, German, Italian, Japanese, and Chinese.

The summary is always generated in the selected language, regardless of the video's original language.

---

## How it works

```
Video URL
     |
Has captions? --- yes ---> Use YouTube captions (manual or auto-generated)
     |
     no
     |
User uploads audio file -> Whisper transcribes
     |
Correct text with AI
     |
Generate structured summary in selected language
     |
Interactive chatbot about the video
```

**Automatic provider selection:**

| Priority | Provider | Cost |
|---|---|---|
| 1st | Groq (LLaMA 3) | Free |
| 2nd | OpenAI (GPT-4o-mini) | Paid |
| 3rd | Anthropic (Claude) | Paid |

The program tests each provider in order and uses the first one that is working.

---

## Project structure

```
Video-Summarizer/
├── app.py                   <- Streamlit web interface
├── main.py                  <- command-line entry point
├── requirements.txt         <- dependencies
├── packages.txt             <- system packages for cloud deployment
├── .env.example             <- configuration template
└── modules/
    ├── ai_provider.py       <- detects and calls the AI provider
    ├── transcript.py        <- fetches transcription (captions or audio)
    ├── processor.py         <- corrects text and generates summary
    └── chatbot.py           <- Q&A chatbot about the video
```

---

## Main dependencies

| Library | Purpose |
|---|---|
| `streamlit` | Web interface |
| `groq` | Primary AI provider (free) |
| `youtube-transcript-api` | Fetches YouTube captions |
| `yt-dlp` | Downloads audio when no captions are available |
| `python-dotenv` | Reads variables from the .env file |

---

## Deployment

This app is ready to deploy on [Streamlit Community Cloud](https://streamlit.io/cloud) for free.

1. Push the repository to GitHub
2. Connect it at share.streamlit.io
3. Set your API keys under Settings → Secrets:

```toml
GROQ_API_KEY = "gsk_your_key_here"
TRANSCRIPT_LANGUAGES = "pt,en"
```

The `packages.txt` file handles ffmpeg installation on the server automatically.

---

## Notes

- API keys must never be committed — the `.env` file is listed in `.gitignore`
- Long transcriptions are automatically split and processed in chunks
- Audio download from YouTube may be blocked on cloud servers — use the audio upload feature instead

---

## License

MIT
