# YouTube Video Summarizer with AI

A Python tool that automatically transcribes and summarizes YouTube videos. After generating the summary, it opens an interactive chatbot so you can ask questions about the video content.

---

## Features

- **Automatic transcription** — uses YouTube captions when available
- **Audio transcription** — when no captions exist, downloads the audio and transcribes with Whisper
- **Text correction** — AI fixes noise and common errors from automatic transcriptions
- **Structured summary** — generates a summary with main topic, key points, details, and conclusion
- **Chatbot** — ask questions about the video and get answers based on its content
- **Multiple AI providers** — automatically detects which provider is available (Groq, OpenAI, or Claude)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/enishi2/Video-Summarizer.git
cd youtube-summarizer
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

Required to download and process audio when a video has no captions.

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

```bash
python main.py
```

---

## Example

```
Checking available AI providers...
Groq available and working.

Paste the YouTube video URL: https://www.youtube.com/watch?v=...

Video ID: dQw4w9WgXcQ
Fetching captions...
Captions found (8,432 characters).
Correcting transcription text...
Generating summary...

============================================================
VIDEO SUMMARY
============================================================
## Main Topic
...

## Key Points
...

============================================================

Would you like to ask questions about the video? (y/n): y

CHATBOT — Ask anything about the video
============================================================
You: What were the main points mentioned?
Bot: ...
```

---

## How it works

```
Video URL
     |
Has captions? --- yes ---> Use YouTube captions
     |
     no
     |
Download audio (yt-dlp) -> Transcribe with Whisper
     |
Correct text with AI
     |
Generate structured summary
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
youtube-summarizer/
├── main.py                  <- entry point
├── requirements.txt         <- dependencies
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
| `groq` | Primary AI provider (free) |
| `youtube-transcript-api` | Fetches YouTube captions |
| `yt-dlp` | Downloads audio when no captions are available |
| `python-dotenv` | Reads variables from the .env file |

---

## Notes

- Videos without captions require **ffmpeg** and a provider with Whisper support (Groq or OpenAI)
- API keys must never be committed — the `.env` file is listed in `.gitignore`
- Long transcriptions are automatically split and processed in chunks

---

## License

MIT
