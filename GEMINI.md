# Gemini Audio Live Demo

A Python application for real-time audio interaction with Google Gemini models, enabling seamless voice conversations.

## Project Overview

This project provides a demonstration of the Gemini Live API, allowing users to talk to the Gemini model in real-time. It uses the `google-genai` SDK to connect to models capable of native audio processing.

### Key Features
- **Real-time Audio:** Low-latency, bidirectional audio communication.
- **Voice Selection:** Customizable prebuilt voices (defaulting to "Zephyr").
- **Google Search Integration:** The model can use Google Search to provide up-to-date information.

## Architecture

The application is built around an `AudioLoop` class that manages multiple concurrent tasks using Python's `asyncio`:
- `listen_audio`: Captures microphone input.
- `send_realtime`: Streams audio chunks to the model.
- `receive_audio`: Handles model responses.
- `play_audio`: Outputs the model's audio response.

## Getting Started

### Prerequisites
- Python 3.10+
- A Google Gemini API Key.
- **System Dependencies (macOS):** `portaudio` is required for `pyaudio`.
  ```bash
  brew install portaudio
  ```

### Installation
Initialize the project and install dependencies using `uv`:
```bash
uv sync
```

### Environment Setup
Create a `.env` file in the root directory based on `.env.example`:
```bash
cp .env.example .env
```
Then, edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY='your_api_key_here'
```

### Running the Application
Start the demo using `uv run`:
```bash
uv run main.py
```
Type your message or just speak. Type `q` to quit.

## Development Conventions

- **Asyncio Usage:** All network and I/O operations are handled asynchronously.
- **Threading:** Blocking calls (like audio I/O) are offloaded to threads using `asyncio.to_thread`.
- **Audio Configuration:**
  - Format: `paInt16` (16-bit PCM)
  - Channels: `1` (Mono)
  - Send Sample Rate: `16000 Hz`
  - Receive Sample Rate: `24000 Hz`
- **Model:** Uses `models/gemini-2.5-flash-native-audio-preview-12-2025`.

## Repository Structure
- `main.py`: The entry point and core logic of the application.
- `GEMINI.md`: Instructional context for the Gemini CLI.
