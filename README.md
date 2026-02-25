# Gemini Live on AIY Voice Kit

A Python application for real-time audio interaction with Google Gemini models, designed to bring the power of Gemini Live to voice-activated hardware like the Google AIY Voice Kit.

## Project Overview

This project demonstrates the Gemini Live API, enabling low-latency, bidirectional voice conversations with Gemini. It uses the `google-genai` SDK to connect to models capable of native audio processing.

### Key Features
- **Real-time Audio:** Seamless, natural conversations with minimal latency.
- **Voice Selection:** Choose from 30+ prebuilt voices (defaulting to "Zephyr").
- **Google Search Integration:** The model can use Google Search to provide up-to-date information.
- **Transcription:** Real-time on-screen transcription of both user and model speech.
- **Silence Timeout:** Automatically ends the session after a period of inactivity.

## Architecture

The application is built around an `AudioLoop` class that manages concurrent tasks using Python's `asyncio`:
- `listen_audio`: Captures microphone input via PyAudio.
- `send_realtime`: Streams audio chunks to the Gemini Live API.
- `receive_audio`: Handles model responses (audio and text).
- `play_audio`: Outputs the model's audio response.
- `send_text`: Allows for text-based interaction alongside audio.

## Getting Started

### Prerequisites
- Python 3.12+
- A Google Gemini API Key.
- **System Dependencies (macOS):** `portaudio` is required for `pyaudio`.
  ```bash
  brew install portaudio
  ```
- **System Dependencies (Linux/Raspberry Pi):**
  ```bash
  sudo apt-get install libportaudio2
  ```

### Installation
Initialize the project and install dependencies using `uv`:
```bash
uv sync
```

### Environment Setup
Create a `.env` file in the root directory:
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
- Speak naturally to interact with Gemini.
- Type messages in the CLI if preferred.
- Type `q` or say "goodbye" to quit.

## Configuration

### Command Line Arguments
- `--voice`: Choose a prebuilt voice (e.g., `Zephyr`, `Puck`, `Charon`). See `voices.json` for a full list.
- `--timeout`: Set the silence timeout in seconds (default: 20).
- `--no-transcript`: Disable real-time transcription in the console.
- `--log-level`: Set logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

Example:
```bash
uv run main.py --voice Charon --timeout 30
```

## Repository Structure
- `main.py`: Core application logic and `AudioLoop` implementation.
- `voices.json`: List of available prebuilt voices.
- `GEMINI.md`: Development notes and instructional context.
- `pyproject.toml`: Project metadata and dependencies.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
