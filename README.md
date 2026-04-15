# YouTube Video Summarizer

Desktop-first YouTube summarizer built with Python and PySide6.

## Overview

This project summarizes YouTube videos from a native desktop app instead of relying on a browser-based workflow.
It tries to fetch YouTube captions first and, when captions are not available, falls back to downloading audio locally and transcribing it with Whisper through Groq or OpenAI.

Version `v1.0.0` is the first desktop-focused release.

## Features

- Native desktop interface built with PySide6
- Local setup screen for AI provider API keys
- Background processing so the UI stays responsive
- Automatic transcript retrieval from YouTube captions when available
- Local audio fallback with `yt-dlp` + `ffmpeg` when captions are missing
- Structured summary generation
- Built-in chat about the processed video
- Windows and macOS build scripts

## Supported AI Providers

- Groq
- OpenAI
- Anthropic

Groq is the recommended default because it also supports Whisper transcription in this project.

## How It Works

1. Paste a YouTube URL into the desktop app
2. The app tries to fetch captions from YouTube
3. If captions are unavailable, it downloads the video audio locally
4. The transcript is cleaned with AI
5. A structured summary is generated
6. You can ask follow-up questions in the built-in chat

## Local Setup

### 1. Create and activate a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install `ffmpeg`

Windows:

```bash
winget install ffmpeg
```

macOS:

```bash
brew install ffmpeg
```

### 4. Run the desktop app

```bash
python desktop_app.py
```

You can also use:

```bash
python app.py
```

Both entry points now open the desktop app.

## Build Windows Executable

From the project root:

```bash
build_windows.bat
```

The generated executable will be available in `dist/`.

## Build macOS App

On macOS, make sure Homebrew is installed because the build script installs `ffmpeg` with `brew` when needed.

```bash
chmod +x build_mac.sh
./build_mac.sh
```

The generated app will be available at `dist/YouTube Summarizer.app`.

## Configuration

API keys are stored locally on the user's machine in:

```text
~/.youtube_summarizer/config.json
```

They are not meant to be committed to the repository.

## Notes

- This repository is now desktop-first and no longer depends on Streamlit for its main workflow
- Build artifacts such as `build/`, `dist/`, `ffmpeg_static/`, and `*.spec` should not be committed
- If a video has no captions, audio transcription requires a provider that supports Whisper in this project

## Release

Recommended first stable tag:

```bash
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0
```
