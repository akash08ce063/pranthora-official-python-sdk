import asyncio
import json
import base64
import threading
import websockets
import pyaudio
from typing import Optional, Dict, Any, Callable

# Audio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # Default for many modern TTS/STT, can be adjusted
CHUNK = 1024

class VoiceClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.replace("http", "ws")
        self.api_key = api_key
        self.ws = None
        self.p = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        self.loop = None
        self.thread = None

    def start(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]] = None):
        """
        Start a real-time voice session with an agent.
        """
        if self.is_running:
            print("Session already running.")
            return

        self.is_running = True
        
        # Start the asyncio loop in a separate thread
        self.thread = threading.Thread(target=self._run_loop, args=(agent_id, assistant_overrides))
        self.thread.start()

    def stop(self):
        """
        Stop the voice session.
        """
        self.is_running = False
        if self.ws:
            # We can't await here easily if called from main thread, 
            # but setting is_running=False should trigger cleanup in the loop.
            pass
        
        # Cleanup Audio
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.p.terminate()

    def _run_loop(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]]):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_stream(agent_id, assistant_overrides))

    async def _connect_and_stream(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]]):
        url = f"{self.base_url}/api/call/web-media-stream?agent_id={agent_id}"
        # Note: Auth might be needed in headers or query params depending on backend.
        # Spec says "Includes origin validation", doesn't explicitly mention Auth header for WS, 
        # but usually it's good practice.
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with websockets.connect(url, extra_headers=headers) as ws:
                self.ws = ws
                print("Connected to Pranthora Voice Gateway.")

                # Send initial configuration if needed (e.g. overrides)
                if assistant_overrides:
                    await ws.send(json.dumps({
                        "type": "config",
                        "config": assistant_overrides
                    }))

                # Start Audio Streams
                self._start_audio_streams()

                # Concurrent tasks: Send Audio & Receive Audio
                await asyncio.gather(
                    self._send_audio(ws),
                    self._receive_audio(ws)
                )
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.is_running = False
            print("Disconnected.")

    def _start_audio_streams(self):
        # Input Stream (Mic)
        self.input_stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        # Output Stream (Speaker)
        self.output_stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK
        )

    async def _send_audio(self, ws):
        while self.is_running:
            try:
                data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                # Encode to base64 or send bytes depending on protocol. 
                # Assuming JSON with base64 for web compatibility.
                payload = {
                    "type": "media",
                    "media": {
                        "payload": base64.b64encode(data).decode("utf-8")
                    }
                }
                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.01) # Small yield
            except Exception as e:
                print(f"Error sending audio: {e}")
                break

    async def _receive_audio(self, ws):
        async for message in ws:
            if not self.is_running:
                break
            try:
                data = json.loads(message)
                if data.get("type") == "media":
                    # Decode and play
                    audio_data = base64.b64decode(data["media"]["payload"])
                    self.output_stream.write(audio_data)
                elif data.get("type") == "call-end":
                    print("Call ended by server.")
                    self.is_running = False
                    break
            except Exception as e:
                print(f"Error receiving audio: {e}")
