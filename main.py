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
import time
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

VOICES = [
  {
    "voice_name": "Zephyr",
    "description": "Bright, Higher pitch"
  },
  {
    "voice_name": "Puck",
    "description": "Upbeat, Middle pitch"
  },
  {
    "voice_name": "Charon",
    "description": "Informative, Lower pitch"
  },
  {
    "voice_name": "Kore",
    "description": "Firm, Middle pitch"
  },
  {
    "voice_name": "Fenrir",
    "description": "Excitable, Lower middle pitch"
  },
  {
    "voice_name": "Leda",
    "description": "Youthful, Higher pitch"
  },
  {
    "voice_name": "Orus",
    "description": "Firm, Lower middle pitch"
  },
  {
    "voice_name": "Aoede",
    "description": "Breezy, Middle pitch"
  },
  {
    "voice_name": "Callirrhoe",
    "description": "Easy-going, Middle pitch"
  },
  {
    "voice_name": "Autonoe",
    "description": "Bright, Middle pitch"
  },
  {
    "voice_name": "Enceladus",
    "description": "Breathy, Lower pitch"
  },
  {
    "voice_name": "Iapetus",
    "description": "Clear, Lower middle pitch"
  },
  {
    "voice_name": "Umbriel",
    "description": "Easy-going, Lower middle pitch"
  },
  {
    "voice_name": "Algieba",
    "description": "Smooth, Lower pitch"
  },
  {
    "voice_name": "Despina",
    "description": "Smooth, Middle pitch"
  },
  {
    "voice_name": "Erinome",
    "description": "Clear, Middle pitch"
  },
  {
    "voice_name": "Algenib",
    "description": "Gravelly, Lower pitch"
  },
  {
    "voice_name": "Rasalgethi",
    "description": "Informative, Middle pitch"
  },
  {
    "voice_name": "Laomedeia",
    "description": "Upbeat, Higher pitch"
  },
  {
    "voice_name": "Achernar",
    "description": "Soft, Higher pitch"
  },
  {
    "voice_name": "Alnilam",
    "description": "Firm, Lower middle pitch"
  },
  {
    "voice_name": "Schedar",
    "description": "Even, Lower middle pitch"
  },
  {
    "voice_name": "Gacrux",
    "description": "Mature, Middle pitch"
  },
  {
    "voice_name": "Pulcherrima",
    "description": "Forward, Middle pitch"
  },
  {
    "voice_name": "Achird",
    "description": "Friendly, Lower middle pitch"
  },
  {
    "voice_name": "Zubenelgenubi",
    "description": "Casual, Lower middle pitch"
  },
  {
    "voice_name": "Vindemiatrix",
    "description": "Gentle, Middle pitch"
  },
  {
    "voice_name": "Sadachbia",
    "description": "Lively, Lower pitch"
  },
  {
    "voice_name": "Sadaltager",
    "description": "Knowledgeable, Middle pitch"
  },
  {
    "voice_name": "Sulafat",
    "description": "Warm, Middle pitch"
  }
]

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

tools = [
    types.Tool(google_search=types.GoogleSearch()),
]

CONFIG = types.LiveConnectConfig(
    response_modalities=[
        types.Modality.AUDIO,
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
    def __init__(self, voice="Zephyr", transcript=True, timeout=20):
        self.audio_in_queue = None
        self.out_queue = None

        self.session = None
        self.voice = voice
        self.transcript = transcript
        self.timeout = timeout
        self.stop_event = asyncio.Event()
        self.last_activity_time = time.monotonic()
        self.exit_after_response = False

    def _update_activity(self):
        self.last_activity_time = time.monotonic()

    async def check_timeout(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(1)
            elapsed = time.monotonic() - self.last_activity_time
            if elapsed > self.timeout:
                logger.warning(f"Silence timeout reached ({self.timeout}s). Exiting...")
                # Simulate user saying goodbye to trigger graceful exit
                self.exit_after_response = True
                if self.session is not None:
                    try:
                        await self.session.send_client_content(
                            turns=[types.Content(parts=[types.Part(text="goodbye")])],
                            turn_complete=True
                        )
                    except Exception as e:
                        logger.error(f"Error sending timeout goodbye: {e}")
                        self.stop_event.set()
                else:
                    self.stop_event.set()
                break

    async def send_text(self):
        loop = asyncio.get_running_loop()
        input_queue = asyncio.Queue()

        def stdin_handler():
            line = sys.stdin.readline()
            if line:
                input_queue.put_nowait(line)

        loop.add_reader(sys.stdin, stdin_handler)
        try:
            while not self.stop_event.is_set():
                print("message > ", end="", flush=True)
                # Wait for input or stop signal
                get_input_task = asyncio.create_task(input_queue.get())
                stop_wait_task = asyncio.create_task(self.stop_event.wait())
                done, pending = await asyncio.wait(
                    [get_input_task, stop_wait_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in pending:
                    task.cancel()
                
                if self.stop_event.is_set():
                    break
                
                line = await get_input_task
                text = line.strip()
                if text.lower() == "q":
                    self.stop_event.set()
                    break
                if text:
                    self._update_activity()
                    if self.transcript:
                        print(f"User: {text}")
                    
                    if any(word in text.lower() for word in ["goodbye", "bye-bye"]):
                        self.exit_after_response = True
                        
                if self.session is not None:
                    await self.session.send_client_content(
                        turns=[types.Content(parts=[types.Part(text=text or ".")])],
                        turn_complete=True
                    )
        finally:
            loop.remove_reader(sys.stdin)

    async def send_realtime(self):
        while not self.stop_event.is_set():
            if self.out_queue is not None:
                try:
                    # Use wait_for to check stop_event periodically or just wait on get()
                    msg = await asyncio.wait_for(self.out_queue.get(), timeout=0.1)
                    if self.session is not None:
                        # msg is a dict like {"data": data, "mime_type": "audio/pcm"}
                        await self.session.send_realtime_input(
                            audio=types.Blob(data=msg["data"], mime_type=msg["mime_type"])
                        )
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if not self.stop_event.is_set():
                        logger.error(f"Error sending realtime data: {e}")

    async def listen_audio(self, pya):
        stream = None
        try:
            mic_info = pya.get_default_input_device_info()
            stream = await asyncio.to_thread(
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
            while not self.stop_event.is_set():
                data = await asyncio.to_thread(stream.read, CHUNK_SIZE, **kwargs)
                if self.out_queue is not None:
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            if not self.stop_event.is_set():
                logger.error(f"Error in listen_audio: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        while not self.stop_event.is_set():
            if self.session is not None:
                try:
                    first_text = True
                    async for response in self.session.receive():
                        if self.stop_event.is_set():
                            break
                        
                        # Manually handle server_content to avoid property warnings
                        if response.server_content:
                            self._update_activity()
                            # 1. Handle model turn (audio data and/or text)
                            if response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        self.audio_in_queue.put_nowait(part.inline_data.data)
                                    if part.text and self.transcript:
                                        if first_text:
                                            print("\nGemini: ", end="", flush=True)
                                            first_text = False
                                        print(part.text, end="", flush=True)

                            # 2. Handle User's input audio transcription (can be partial)
                            if in_trans := response.server_content.input_transcription:
                                if in_trans.text:
                                    if self.transcript:
                                        print(f"\rUser (audio): {in_trans.text}", end="", flush=True)
                                    if any(word in in_trans.text.lower() for word in ["goodbye", "bye-bye"]):
                                        self.exit_after_response = True
                                    if in_trans.finished:
                                        if self.transcript:
                                            print() # New line when user is done talking
                                        first_text = True

                            # 3. Handle Gemini's output transcription (streaming)
                            if out_trans := response.server_content.output_transcription:
                                if out_trans.text and self.transcript:
                                    if first_text:
                                        print("\nGemini: ", end="", flush=True)
                                        first_text = False
                                    print(out_trans.text, end="", flush=True)

                        # If a turn is complete, reset the Gemini prefix for the next response
                        if response.server_content and response.server_content.turn_complete:
                            if not first_text:
                                if self.transcript:
                                    print() # New line after Gemini's turn
                            
                            if self.exit_after_response:
                                logger.info("User said goodbye. Exiting...")
                                self.stop_event.set()
                                break
                            
                            first_text = True

                    # Empty audio queue if interrupted
                    while not self.audio_in_queue.empty():
                        self.audio_in_queue.get_nowait()
                except Exception as e:
                    if not self.stop_event.is_set():
                        logger.error(f"Error in receive_audio: {e}")
                    await asyncio.sleep(1)

    async def play_audio(self, pya):
        stream = None
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            while not self.stop_event.is_set():
                if self.audio_in_queue is not None:
                    try:
                        bytestream = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.1)
                        self._update_activity()
                        await asyncio.to_thread(stream.write, bytestream)
                    except asyncio.TimeoutError:
                        continue
        except Exception as e:
            if not self.stop_event.is_set():
                logger.error(f"Error in play_audio: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    async def run(self):
        pya = pyaudio.PyAudio()
        try:
            # Create a copy of the config and update modalities
            config = CONFIG.model_copy(deep=True)
            config.speech_config.voice_config.prebuilt_voice_config.voice_name = self.voice
            if self.transcript:
                # Enable transcription for both input and output
                config.input_audio_transcription = types.AudioTranscriptionConfig()
                config.output_audio_transcription = types.AudioTranscriptionConfig()
            
            logger.info("Connecting to Gemini...")
            async with (
                client.aio.live.connect(model=MODEL, config=config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                logger.info("Connected.")

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                tg.create_task(self.check_timeout())
                tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio(pya))
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio(pya))

                logger.info("All tasks started. Ready to chat!")
                
                # Keep the task group alive until stop_event is set or tg is cancelled
                await self.stop_event.wait()
                logger.info("Stopping tasks...")

        except asyncio.CancelledError:
            logger.info("Session cancelled.")
        except Exception as e:
            logger.error(f"Error in run loop: {e}")
            traceback.print_exc()
        finally:
            self.stop_event.set()
            logger.info("Cleaning up...")
            pya.terminate()
            logger.info("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Audio Live Demo")
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: WARNING)"
    )
    parser.add_argument(
        "--transcript",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Output the transcript of the conversation to stdout (default: True)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Silence timeout in seconds (default: 20)"
    )
    voice_names = [v["voice_name"] for v in VOICES]
    parser.add_argument(
        "--voice",
        type=str,
        default="Zephyr",
        choices=voice_names,
        help="Choose a prebuilt voice for Gemini (default: Zephyr)"
    )
    args = parser.parse_args()
    
    # Update logging level based on argument
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    main = AudioLoop(voice=args.voice, transcript=args.transcript, timeout=args.timeout)
    try:
        asyncio.run(main.run())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, exiting...")
    except Exception:
        traceback.print_exc()
