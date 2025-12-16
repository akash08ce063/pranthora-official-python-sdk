import asyncio
import json
import base64
import threading
import websockets
from typing import Optional, Dict, Any, Callable, List

# Audio Configuration
FORMAT = 8  # pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Matches backend web audio stream sample rate
CHUNK = 1024

# Try to import pyaudio - it's optional
PYAUDIO_AVAILABLE = False
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None


class VoiceClient:
    """
    Real-time voice client for Pranthora SDK.
    Handles WebSocket connections, audio streaming, and event handling.
    """
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.replace("http", "ws")
        self.api_key = api_key
        self.ws = None
        self.p = None
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        self.loop = None
        self.thread = None
        
        # Event callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_first_response: Optional[Callable[[str], None]] = None
        self.on_transcript: Optional[Callable[[str, str], None]] = None  # (role, text)
        self.on_interruption: Optional[Callable] = None
        self.on_agent_speaking_start: Optional[Callable] = None
        self.on_agent_speaking_stop: Optional[Callable] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_message: Optional[Callable[[Dict], None]] = None
        
        # State tracking
        self.agent_speaking = False
        self.user_speaking = False
        self.first_response_received = False
        self.messages_received = 0
        self.audio_bytes_sent = 0
        self.audio_bytes_received = 0
        
        # Message log
        self.message_log: List[Dict[str, Any]] = []

    def start(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]] = None):
        """
        Start a real-time voice session with an agent.
        
        Args:
            agent_id: The ID of the agent to connect to
            assistant_overrides: Optional overrides for the assistant configuration
        """
        if self.is_running:
            print("Session already running.")
            return False

        self.is_running = True
        self.first_response_received = False
        self.messages_received = 0
        self.audio_bytes_sent = 0
        self.audio_bytes_received = 0
        self.message_log = []
        
        # Start the asyncio loop in a separate thread
        self.thread = threading.Thread(
            target=self._run_loop, 
            args=(agent_id, assistant_overrides),
            daemon=True
        )
        self.thread.start()
        return True

    def stop(self):
        """
        Stop the voice session.
        """
        self.is_running = False
        if self.ws:
            # Setting is_running=False should trigger cleanup in the loop
            pass
        
        self._cleanup_audio()

    def _cleanup_audio(self):
        """Clean up audio streams"""
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
            self.input_stream = None
            
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
            self.output_stream = None
            
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
            self.p = None

    def _run_loop(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]]):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect_and_stream(agent_id, assistant_overrides))
        except Exception as e:
            self._log_message("error", f"Loop error: {e}")
            if self.on_error:
                self.on_error(str(e))
        finally:
            self.is_running = False
            self._cleanup_audio()

    def _log_message(self, msg_type: str, message: str, data: Any = None):
        """Log a message"""
        import time
        entry = {
            "timestamp": time.time(),
            "type": msg_type,
            "message": message,
            "data": data
        }
        self.message_log.append(entry)

    async def _connect_and_stream(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]]):
        url = f"{self.base_url}/api/call/web-media-stream?agent_id={agent_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key
        }

        self._log_message("info", f"Connecting to {url}")

        try:
            async with websockets.connect(
                url, 
                additional_headers=headers,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=10
            ) as ws:
                self.ws = ws
                self._log_message("connected", "WebSocket connected")
                print("Connected to Pranthora Voice Gateway.")
                
                if self.on_connected:
                    self.on_connected()

                # Send initial configuration if needed (e.g. overrides)
                if assistant_overrides:
                    config_msg = {
                        "type": "config",
                        "config": assistant_overrides
                    }
                    await ws.send(json.dumps(config_msg))
                    self._log_message("send", "Sent config", assistant_overrides)

                # Start Audio Streams
                self._start_audio_streams()

                # Concurrent tasks: Send Audio & Receive Audio
                await asyncio.gather(
                    self._send_audio(ws),
                    self._receive_audio(ws)
                )
        except websockets.exceptions.InvalidStatus as e:
            error_msg = f"WebSocket connection rejected: {e}"
            self._log_message("error", error_msg)
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)
        except Exception as e:
            error_msg = f"Connection error: {e}"
            self._log_message("error", error_msg)
            print(error_msg)
            if self.on_error:
                self.on_error(str(e))
        finally:
            self.is_running = False
            self._log_message("disconnected", "WebSocket disconnected")
            print("Disconnected.")
            if self.on_disconnected:
                self.on_disconnected()

    def _start_audio_streams(self):
        """Initialize PyAudio streams"""
        if not PYAUDIO_AVAILABLE:
            self._log_message("warning", "PyAudio not available - audio disabled")
            print("Warning: PyAudio not available. Audio streaming disabled.")
            return

        try:
            import pyaudio
            self.p = pyaudio.PyAudio()
            
            # Input Stream (Mic)
            self.input_stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            # Output Stream (Speaker) - Use very small buffer for real-time streaming
            output_chunk = 256  # Very small chunk for minimal latency
            self.output_stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=output_chunk,
                stream_callback=None,  # No callback, we'll write directly
                start=False  # Don't start automatically
            )
            self.output_stream.start_stream()  # Start the stream
            
            self._log_message("audio", "Audio streams started")
        except Exception as e:
            self._log_message("error", f"Failed to start audio: {e}")
            print(f"Error starting audio streams: {e}")

    async def _send_audio(self, ws):
        """Send audio from microphone to WebSocket"""
        while self.is_running:
            try:
                if self.input_stream:
                    data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                    # Backend expects raw PCM bytes for web streams, not JSON
                    await ws.send(data)
                    self.audio_bytes_sent += len(data)
                    
                await asyncio.sleep(0.01)  # Small yield
            except Exception as e:
                self._log_message("error", f"Error sending audio: {e}")
                print(f"Error sending audio: {e}")
                break

    async def _receive_audio(self, ws):
        """Receive and process messages from WebSocket"""
        async for message in ws:
            if not self.is_running:
                break
            try:
                self.messages_received += 1
                
                # Handle binary messages (raw audio) - STREAMING MODE
                if isinstance(message, bytes):
                    self.audio_bytes_received += len(message)
                    if self.output_stream:
                        try:
                            # Write audio IMMEDIATELY in streaming mode - no waiting, no splitting
                            # Write directly to minimize latency
                            self.output_stream.write(message, exception_on_underflow=False)
                        except Exception as e:
                            # If buffer is full, try to write in smaller chunks
                            try:
                                chunk_size = 256
                                for i in range(0, len(message), chunk_size):
                                    chunk = message[i:i + chunk_size]
                                    self.output_stream.write(chunk, exception_on_underflow=False)
                            except Exception:
                                # Buffer might be full, log but continue
                                pass
                    # Track agent speaking state
                    if not self.agent_speaking:
                        self.agent_speaking = True
                        self._log_message("flag", "Agent speaking start")
                        if self.on_agent_speaking_start:
                            self.on_agent_speaking_start()
                    continue
                
                # Handle JSON messages
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                
                # Call general message handler
                if self.on_message:
                    self.on_message(data)
                
                if msg_type == "media":
                    # Decode and play base64 audio
                    audio_data = base64.b64decode(data["media"]["payload"])
                    self.audio_bytes_received += len(audio_data)
                    
                    if self.output_stream:
                        self.output_stream.write(audio_data)
                    
                    # Track agent speaking state
                    if not self.agent_speaking:
                        self.agent_speaking = True
                        self._log_message("flag", "Agent speaking start")
                        if self.on_agent_speaking_start:
                            self.on_agent_speaking_start()
                            
                elif msg_type == "first_response":
                    self.first_response_received = True
                    message_text = data.get("message", "")
                    self._log_message("flag", f"First response: {message_text}")
                    if self.on_first_response:
                        self.on_first_response(message_text)
                        
                elif msg_type == "transcript":
                    role = data.get("role", "unknown")
                    text = data.get("text", "")
                    self._log_message("transcript", f"[{role}] {text}")
                    if self.on_transcript:
                        self.on_transcript(role, text)
                        
                elif msg_type == "interruption":
                    self._log_message("flag", "Interruption detected")
                    self.agent_speaking = False
                    if self.on_interruption:
                        self.on_interruption()
                        
                elif msg_type == "agent_stop" or msg_type == "agent_speaking_stop":
                    self._log_message("flag", "Agent speaking stop")
                    self.agent_speaking = False
                    if self.on_agent_speaking_stop:
                        self.on_agent_speaking_stop()
                        
                elif msg_type == "call-end" or msg_type == "call_end":
                    self._log_message("flag", "Call ended by server")
                    print("Call ended by server.")
                    self.is_running = False
                    break
                    
                elif msg_type == "error":
                    error_msg = data.get("message", "Unknown error")
                    self._log_message("error", f"Server error: {error_msg}")
                    if self.on_error:
                        self.on_error(error_msg)
                        
                else:
                    self._log_message("recv", f"Message type: {msg_type}", data)
                    
            except json.JSONDecodeError:
                # Handle text messages that aren't JSON (like "stop" signal)
                if isinstance(message, str):
                    if message.strip() == "stop" or "stop" in message.lower():
                        # Stop signal = interruption, not disconnect
                        # Clear audio buffer and stop playing, but keep connection alive
                        self._log_message("flag", "Stop signal (interruption) - stopping audio playback")
                        self.agent_speaking = False
                        # Clear the output stream buffer if possible
                        if self.output_stream:
                            try:
                                # Try to stop and restart the stream to clear buffer
                                self.output_stream.stop_stream()
                                self.output_stream.start_stream()
                            except Exception:
                                pass
                        # Trigger interruption callback
                        if self.on_interruption:
                            self.on_interruption()
                        # Continue - don't disconnect
                        continue
                    else:
                        self._log_message("recv", f"Text message: {message[:100]}")
                else:
                    self._log_message("recv", f"Non-JSON message received")
            except Exception as e:
                self._log_message("error", f"Error receiving: {e}")
                print(f"Error receiving audio: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "is_running": self.is_running,
            "messages_received": self.messages_received,
            "audio_bytes_sent": self.audio_bytes_sent,
            "audio_bytes_received": self.audio_bytes_received,
            "first_response_received": self.first_response_received,
            "agent_speaking": self.agent_speaking,
            "log_count": len(self.message_log)
        }

    def get_logs(self) -> List[Dict[str, Any]]:
        """Get message logs"""
        return self.message_log.copy()
