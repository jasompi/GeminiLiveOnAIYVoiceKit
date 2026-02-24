"""
## Documentation
Quickstart: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

## Setup

To install the dependencies for this script, run:

```
pip install google-genai pyaudio python-dotenv
```
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv
import asyncio
import traceback

load_dotenv()

import pyaudio

from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

tools = [
    types.Tool(google_search=types.GoogleSearch()),
]

CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=104857,
        sliding_window=types.SlidingWindow(target_tokens=52428),
    ),
    tools=tools,
)

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None

        self.session = None

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None

        self.audio_stream = None

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            if text:
                print(f"User: {text}")
            if self.session is not None:
                await self.session.send(input=text or ".", end_of_turn=True)

    async def send_realtime(self):
        while True:
            if self.out_queue is not None:
                msg = await self.out_queue.get()
                if self.session is not None:
                    try:
                        await self.session.send(input=msg)
                    except Exception as e:
                        logger.error(f"Error sending realtime data: {e}")

    async def listen_audio(self):
        try:
            mic_info = pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
            if __debug__:
                kwargs = {"exception_on_overflow": False}
            else:
                kwargs = {}
            
            logger.info("Listening to audio...")
            while True:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                if self.out_queue is not None:
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            logger.error(f"Error in listen_audio: {e}")

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        while True:
            if self.session is not None:
                try:
                    first_text = True
                    async for response in self.session.receive():
                        if data := response.data:
                            self.audio_in_queue.put_nowait(data)
                        
                        if text := response.text:
                            if first_text:
                                print("\nGemini: ", end="", flush=True)
                                first_text = False
                            print(text, end="", flush=True)
                        
                        # If a turn is complete, reset the Gemini prefix for the next response
                        if response.server_content and response.server_content.turn_complete:
                            print() # New line after Gemini's turn
                            first_text = True

                    # Empty audio queue if interrupted
                    while not self.audio_in_queue.empty():
                        self.audio_in_queue.get_nowait()
                except Exception as e:
                    logger.error(f"Error in receive_audio: {e}")
                    await asyncio.sleep(1)

    async def play_audio(self):
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            while True:
                if self.audio_in_queue is not None:
                    bytestream = await self.audio_in_queue.get()
                    await asyncio.to_thread(stream.write, bytestream)
        except Exception as e:
            logger.error(f"Error in play_audio: {e}")

    async def run(self):
        try:
            logger.info("Connecting to Gemini...")
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                logger.info("Connected.")

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                logger.info("All tasks started. Ready to chat!")
                
                # Keep the task group alive until manually cancelled or session ends
                while True:
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Session cancelled.")
        except Exception as e:
            logger.error(f"Error in run loop: {e}")
            if self.audio_stream is not None:
                self.audio_stream.close()
            traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Audio Live Demo")
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: WARNING)"
    )
    args = parser.parse_args()
    
    # Update logging level based on argument
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    main = AudioLoop()
    try:
        asyncio.run(main.run())
    except KeyboardInterrupt:
        pass
