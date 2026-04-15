#!/bin/bash

set -e

echo ""
echo "============================================================"
echo "  YouTube Summarizer - Building macOS desktop app"
echo "============================================================"
echo ""

source venv/bin/activate
pip install -r requirements.txt pyinstaller --quiet

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Installing ffmpeg..."
    brew install ffmpeg
fi

FFMPEG_PATH=$(which ffmpeg)

echo ""
echo "Building app..."
pyinstaller \
    --onefile \
    --windowed \
    --name "YouTube Summarizer" \
    --add-data "Modulos:Modulos" \
    --add-binary "$FFMPEG_PATH:." \
    --hidden-import "PySide6" \
    --hidden-import "youtube_transcript_api" \
    --hidden-import "groq" \
    --hidden-import "anthropic" \
    --hidden-import "openai" \
    --hidden-import "yt_dlp" \
    launcher_mac.py

echo ""
echo "App generated in: dist/YouTube Summarizer.app"
echo ""
echo "To distribute it, compress the dist/ output into a zip file."
read -p "Press Enter to exit..."
