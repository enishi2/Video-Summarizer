  YouTube Video AI Summarizer

A Python tool that automatically transcribes and summarizes YouTube videos. After generating the summary, it opens a chatbot so you can ask questions about the video content.

  Features

Automatic transcription — uses YouTube captions when available

Audio transcription — if captions are not available, downloads the audio and transcribes it with Whisper

Text correction — the AI cleans up noise and typical errors from automatic transcriptions

Structured summary — generates a summary with topic, key points, details, and conclusion

Chatbot — ask questions about the video and get answers based on its content

Multiple AI providers — automatically detects which provider is available (Groq, OpenAI, or Claude)

  How to use
1. Clone the repository
git clone https://github.com/seu-usuario/resumidor-youtube.git
cd resumidor-youtube
2. Create and activate the virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
3. Install dependencies
pip install -r requirements.txt
4. Install ffmpeg

Required to download and process audio when the video has no captions.

winget install ffmpeg        # Windows
brew install ffmpeg          # Mac
sudo apt install ffmpeg      # Linux
5. Configure API keys

Rename the .env.example file to .env and fill in your keys:

cp .env.example .env
GROQ_API_KEY=gsk_your_key_here
OPENAI_API_KEY=            # optional
ANTHROPIC_API_KEY=         # optional
TRANSCRIPT_LANGUAGES=pt,en

Groq is free — create your key at https://console.groq.com

6. Run the program
python main.py
  Example usage
  Checking available AI providers...
  Groq available and working.

  Paste the YouTube video URL: https://www.youtube.com/watch?v=...

  Video ID: dQw4w9WgXcQ
  Searching for captions...
  Captions found (8,432 characters).
  Cleaning transcription text...
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

  CHATBOT — Ask about the video
============================================================
You: What were the main points mentioned?
Bot: ...
How it works
Video URL
     ↓
Has captions? ──── yes ──→ Use YouTube captions
     │
     no
     ↓
Download audio (yt-dlp) → Transcribe with Whisper
     ↓
Clean the text with AI
     ↓
Generate structured summary
     ↓
Interactive chatbot about the video

Automatic provider selection:

Priority	Provider	Cost
1st	Groq (LLaMA 3)	Free
2nd	OpenAI (GPT-4o-mini)	Paid
3rd	Anthropic (Claude)	Paid

The program tests each provider in order and uses the first one that is available.

  Project structure
resumidor-youtube/
├── main.py                  ← entry point
├── requirements.txt         ← dependencies
├── .env.example             ← configuration file template
└── modules/
    ├── ai_provider.py       ← detects and calls AI providers
    ├── transcript.py        ← gets transcription (captions or audio)
    ├── processor.py         ← cleans text and generates summary
    └── chatbot.py           ← Q&A chatbot about the video
Main dependencies
Library	Purpose
groq	Main AI provider (free)
youtube-transcript-api	Fetch YouTube captions
yt-dlp	Download audio when captions are unavailable
python-dotenv	Load environment variables from .env
    Notes

Videos without captions require ffmpeg and a provider with Whisper support (Groq or OpenAI)

API keys should never be committed — the .env file is included in .gitignore

Very long transcripts are automatically processed in chunks