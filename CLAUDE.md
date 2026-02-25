# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time voice conversation application using the Google Gemini Live API, designed for the Google AIY Voice Kit (Raspberry Pi). Enables low-latency bidirectional audio conversations with Gemini models that natively process audio.

## Commands

This project uses `uv` as the package manager.

```bash
# Run the application
uv run main.py

# Run with options
uv run main.py --voice Puck --timeout 30 --transcript --log-level DEBUG

# Install system dependencies (macOS)
brew install portaudio

# Install system dependencies (Linux/Raspberry Pi)
sudo apt-get install libportaudio2
```

## Environment Setup

Copy `.env.example` to `.env` and set `GEMINI_API_KEY`. Note: the code reads `GEMINI_API_KEY`, not `GOOGLE_API_KEY`.

## Architecture

The entire application lives in `main.py` with a single `AudioLoop` class that manages 6 concurrent asyncio tasks running in a `TaskGroup`:

| Task | Role |
|------|------|
| `listen_audio()` | Captures mic input (16kHz) → `out_queue` |
| `send_realtime()` | Drains `out_queue` → Gemini Live API WebSocket |
| `receive_audio()` | Gemini responses → `audio_in_queue` + stdout transcription |
| `play_audio()` | Drains `audio_in_queue` → speaker (24kHz) |
| `send_text()` | Reads stdin → Gemini API (also handles `q` quit) |
| `check_timeout()` | Sends "goodbye" to Gemini after silence timeout |

**Data flow:**
```
Mic → listen_audio → out_queue → send_realtime → Gemini API
                                                      ↓
Speaker ← play_audio ← audio_in_queue ← receive_audio ←┘
```

Blocking PyAudio calls are offloaded via `asyncio.to_thread()`. Shutdown is coordinated through a `stop_event` asyncio Event. The model used is `models/gemini-2.5-flash-native-audio-preview-12-2025` with Google Search enabled and context window compression (sliding window).

## Key Configuration

Audio constants in `main.py`:
- Mic input: 16000 Hz, mono, 16-bit PCM, 1024-byte chunks
- Speaker output: 24000 Hz, mono, 16-bit PCM

Voice list with descriptions is in `voices.json` (30 voices). The `--voice` argument is validated against this file at startup.
