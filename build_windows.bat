@echo off
chcp 65001 >nul
title YouTube Summarizer - Build Windows

echo.
echo ============================================================
echo   YouTube Summarizer - Building Windows desktop executable
echo ============================================================
echo.

call venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller --quiet

echo Downloading static ffmpeg...
if not exist "ffmpeg_static" (
    mkdir ffmpeg_static
    curl -L "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" -o ffmpeg.zip
    tar -xf ffmpeg.zip --strip-components=2 -C ffmpeg_static "*/bin/ffmpeg.exe"
    del ffmpeg.zip
)

echo.
echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "YouTube Summarizer" ^
    --add-data "Modulos;Modulos" ^
    --add-data "ffmpeg_static/ffmpeg.exe;." ^
    --hidden-import "PySide6" ^
    --hidden-import "youtube_transcript_api" ^
    --hidden-import "groq" ^
    --hidden-import "anthropic" ^
    --hidden-import "openai" ^
    --hidden-import "yt_dlp" ^
    launcher_windows.py

echo.
echo Executable generated in: dist\YouTube Summarizer.exe
pause
