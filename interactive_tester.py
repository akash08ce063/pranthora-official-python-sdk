#!/usr/bin/env python3
"""
Pranthora SDK Interactive CLI
A command-based terminal interface to explore and test the Pranthora SDK.

Commands:
  get/all       - List all agents
  get/id        - Get agent by ID (uses active agent)
  set/{index}   - Set active agent by index from last get/all
  create/       - Create a new agent with step-by-step prompts
  update/       - Update active agent with parameter selection
  delete/       - Delete active agent with confirmation
  inspect/      - Inspect last API call details
  call/start    - Start a real-time voice call
  call/stop     - Stop current voice call
  help          - Show available commands
  exit/quit     - Exit the application
"""

import sys
import time
import json
import os
import threading
import asyncio
import base64
from typing import Any, Dict, List, Optional, Callable
from pranthora import Pranthora
from pranthora.exceptions import *
from pranthora.mappings import (
    TTS_PROVIDERS, LLM_MODELS, STT_CONFIGS, VOICES, VAD_PROVIDERS,
    get_tts_provider_name, get_model_name, get_transcriber_name, 
    get_voice_name, get_vad_provider_name
)

# Try to import rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.layout import Layout
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    print("Rich library not found. Please install it: pip install rich")
    sys.exit(1)

# Try to import audio libraries
AUDIO_AVAILABLE = False
try:
    import pyaudio
    import websockets
    AUDIO_AVAILABLE = True
except ImportError:
    pass


class APIInspector:
    """Captures API interactions for display"""
    def __init__(self):
        self.last_request: Dict[str, Any] = {}
        self.last_response: Any = None
        self.last_status_code: int = 0
        self.last_url: str = ""
        self.last_method: str = ""
        self.history: List[Dict[str, Any]] = []

    def capture(self, method, url, params=None, data=None, response=None, status_code=200):
        interaction = {
            "timestamp": time.strftime("%H:%M:%S"),
            "method": method,
            "url": url,
            "params": params,
            "data": data,
            "response": response,
            "status_code": status_code
        }
        self.last_request = {"params": params, "data": data}
        self.last_response = response
        self.last_status_code = status_code
        self.last_url = url
        self.last_method = method
        self.history.append(interaction)

    def clear(self):
        self.last_request = {}
        self.last_response = None
        self.last_status_code = 0
        self.last_url = ""
        self.last_method = ""


class CallSessionHandler:
    """Handles real-time voice call sessions with logging"""
    def __init__(self, console: Console, api_key: str, base_url: str):
        self.console = console
        self.api_key = api_key
        self.base_url = base_url.replace("http", "ws")
        self.is_running = False
        self.ws = None
        self.loop = None
        self.thread = None
        self.logs: List[Dict[str, Any]] = []
        self.p = None
        self.input_stream = None
        self.output_stream = None
        
        # Audio config
        self.FORMAT = 8  # pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 24000
        self.CHUNK = 1024
        
        # State tracking
        self.user_speaking = False
        self.agent_speaking = False
        self.first_response_received = False
        self.call_start_time = None
        self.messages_received = 0
        self.audio_bytes_sent = 0
        self.audio_bytes_received = 0

    def log(self, event_type: str, message: str, data: Any = None):
        """Add a log entry"""
        entry = {
            "time": time.strftime("%H:%M:%S.") + str(int(time.time() * 1000) % 1000).zfill(3),
            "type": event_type,
            "message": message,
            "data": data
        }
        self.logs.append(entry)
        
        # Print to console with color coding
        color_map = {
            "INFO": "cyan",
            "SEND": "green",
            "RECV": "yellow",
            "FLAG": "magenta",
            "ERROR": "red",
            "AUDIO": "blue"
        }
        color = color_map.get(event_type, "white")
        self.console.print(f"[{color}][{entry['time']}] [{event_type}][/{color}] {message}")

    def start(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]] = None):
        """Start a real-time voice session"""
        if self.is_running:
            self.log("ERROR", "Session already running")
            return False

        self.is_running = True
        self.call_start_time = time.time()
        self.logs = []
        
        # Start the asyncio loop in a separate thread
        self.thread = threading.Thread(
            target=self._run_loop, 
            args=(agent_id, assistant_overrides),
            daemon=True
        )
        self.thread.start()
        return True

    def stop(self):
        """Stop the voice session"""
        self.log("INFO", "Stopping call...")
        self.is_running = False
        
        # Cleanup Audio
        try:
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
            if self.p:
                self.p.terminate()
        except Exception as e:
            self.log("ERROR", f"Audio cleanup error: {e}")
        
        self.input_stream = None
        self.output_stream = None
        self.p = None

    def _run_loop(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]]):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect_and_stream(agent_id, assistant_overrides))
        except Exception as e:
            self.log("ERROR", f"Loop error: {e}")
        finally:
            self.is_running = False

    async def _connect_and_stream(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]]):
        url = f"{self.base_url}/api/call/web-media-stream?agent_id={agent_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key
        }

        self.log("INFO", f"Connecting to WebSocket: {url}")

        try:
            async with websockets.connect(
                url, 
                additional_headers=headers,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=10
            ) as ws:
                self.ws = ws
                self.log("FLAG", "🔗 CONNECTED - WebSocket connection established")

                # Send initial configuration if needed
                if assistant_overrides:
                    config_msg = json.dumps({
                        "type": "config",
                        "config": assistant_overrides
                    })
                    await ws.send(config_msg)
                    self.log("SEND", f"Sent config: {assistant_overrides}")

                # Start Audio Streams
                self._start_audio_streams()

                # Concurrent tasks: Send Audio & Receive Audio
                await asyncio.gather(
                    self._send_audio(ws),
                    self._receive_audio(ws)
                )
        except websockets.exceptions.InvalidStatus as e:
            self.log("ERROR", f"WebSocket connection rejected: {e}")
        except Exception as e:
            self.log("ERROR", f"Connection error: {e}")
        finally:
            self.is_running = False
            self.log("FLAG", "🔌 DISCONNECTED")

    def _start_audio_streams(self):
        """Initialize PyAudio streams"""
        if not AUDIO_AVAILABLE:
            self.log("ERROR", "PyAudio not available - audio disabled")
            return

        try:
            import pyaudio
            self.p = pyaudio.PyAudio()
            
            # Input Stream (Mic)
            self.input_stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            self.log("AUDIO", "🎤 Microphone stream started")

            # Output Stream (Speaker) - Use very small buffer for real-time streaming
            # Smaller buffer = lower latency for streaming audio
            output_chunk = 256  # Very small chunk for minimal latency
            self.output_stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=output_chunk,
                stream_callback=None,  # No callback, we'll write directly
                start=False  # Don't start automatically
            )
            self.output_stream.start_stream()  # Start the stream
            self.log("AUDIO", "🔊 Speaker stream started")
        except Exception as e:
            self.log("ERROR", f"Failed to start audio streams: {e}")

    async def _send_audio(self, ws):
        """Send audio from microphone to WebSocket"""
        while self.is_running:
            try:
                if self.input_stream:
                    data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                    # Backend expects raw PCM bytes for web streams, not JSON
                    await ws.send(data)
                    self.audio_bytes_sent += len(data)
                    
                    # Detect user speaking (simple energy-based)
                    energy = sum(abs(b) for b in data) / len(data)
                    was_speaking = self.user_speaking
                    self.user_speaking = energy > 50  # Threshold
                    
                    if self.user_speaking and not was_speaking:
                        self.log("FLAG", "🗣️ USER SPEAKING START")
                    elif not self.user_speaking and was_speaking:
                        self.log("FLAG", "🗣️ USER SPEAKING STOP")
                        
                await asyncio.sleep(0.01)
            except Exception as e:
                self.log("ERROR", f"Error sending audio: {e}")
                break

    async def _receive_audio(self, ws):
        """Receive audio from WebSocket and play/log"""
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
                        self.log("FLAG", "🤖 AGENT SPEAKING START")
                    continue
                
                # Handle JSON messages
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                
                if msg_type == "media":
                    # Decode and play base64 audio
                    audio_data = base64.b64decode(data["media"]["payload"])
                    self.audio_bytes_received += len(audio_data)
                    
                    if self.output_stream:
                        self.output_stream.write(audio_data)
                    
                    # Agent speaking state
                    if not self.agent_speaking:
                        self.agent_speaking = True
                        self.log("FLAG", "🤖 AGENT SPEAKING START")
                        
                elif msg_type == "first_response":
                    self.first_response_received = True
                    self.log("FLAG", f"✨ FIRST RESPONSE: {data.get('message', 'N/A')}")
                    
                elif msg_type == "transcript":
                    role = data.get("role", "unknown")
                    text = data.get("text", "")
                    self.log("RECV", f"📝 Transcript [{role}]: {text}")
                    
                elif msg_type == "interruption":
                    self.log("FLAG", "⚡ INTERRUPTION DETECTED")
                    self.agent_speaking = False
                    
                elif msg_type == "agent_stop":
                    self.log("FLAG", "🤖 AGENT SPEAKING STOP")
                    self.agent_speaking = False
                    
                elif msg_type == "call-end":
                    self.log("FLAG", "📞 CALL ENDED BY SERVER")
                    self.is_running = False
                    break
                    
                elif msg_type == "error":
                    self.log("ERROR", f"Server error: {data.get('message', 'Unknown')}")
                    
                else:
                    self.log("RECV", f"Message type: {msg_type}", data)
                    
            except json.JSONDecodeError:
                # Handle text messages that aren't JSON (like "stop" signal)
                if isinstance(message, str):
                    if message.strip() == "stop" or "stop" in message.lower():
                        # Stop signal = interruption, not disconnect
                        # Clear audio buffer and stop playing, but keep connection alive
                        self.log("FLAG", "⚡ STOP SIGNAL (INTERRUPTION) - Stopping audio playback")
                        self.agent_speaking = False
                        # Clear the output stream buffer if possible
                        if self.output_stream:
                            try:
                                # Try to stop and restart the stream to clear buffer
                                self.output_stream.stop_stream()
                                self.output_stream.start_stream()
                            except Exception:
                                pass
                        # Continue - don't disconnect
                        continue
                    else:
                        self.log("RECV", f"Text message: {message[:100]}...")
                else:
                    self.log("RECV", f"Non-JSON message: {str(message)[:100]}...")
            except Exception as e:
                self.log("ERROR", f"Error receiving: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get call statistics"""
        duration = 0
        if self.call_start_time:
            duration = time.time() - self.call_start_time
        return {
            "duration_seconds": round(duration, 1),
            "messages_received": self.messages_received,
            "audio_bytes_sent": self.audio_bytes_sent,
            "audio_bytes_received": self.audio_bytes_received,
            "first_response_received": self.first_response_received,
            "log_count": len(self.logs)
        }


class InteractiveCLI:
    def __init__(self, api_key: str, base_url: str):
        self.console = Console()
        self.api_key = api_key
        self.base_url = base_url
        self.client = Pranthora(api_key=api_key, base_url=base_url)
        self.inspector = APIInspector()
        self.active_agent_id: Optional[str] = None
        self.active_agent_name: Optional[str] = None
        self.cached_agents: List[Dict[str, Any]] = []
        self.call_handler: Optional[CallSessionHandler] = None
        
        # Update buffer for update/ command
        self.update_buffer: Dict[str, Any] = {}
        
        # Monkey patch the requestor to capture details
        self._original_request = self.client.requestor.request
        self.client.requestor.request = self._intercept_request

    def _intercept_request(self, method, url, params=None, data=None):
        try:
            response = self._original_request(method, url, params=params, data=data)
            self.inspector.capture(method, url, params, data, response, 200)
            return response
        except APIError as e:
            self.inspector.capture(method, url, params, data, e.body, e.status_code)
            raise e
        except Exception as e:
            self.inspector.capture(method, url, params, data, str(e), 500)
            raise e

    def print_header(self):
        """Print the CLI header with status"""
        self.console.clear()
        
        # Title
        self.console.print(Panel(
            Text("🚀 Pranthora SDK CLI", justify="center", style="bold magenta"),
            style="magenta",
            subtitle=f"[dim]{self.base_url}[/dim]"
        ))
        
        # Status line
        status = Text()
        status.append("Agent: ", style="bold")
        if self.active_agent_id:
            status.append(f"{self.active_agent_name or 'Unknown'} ", style="cyan")
            status.append(f"({self.active_agent_id[:16]}...)", style="dim")
        else:
            status.append("None", style="yellow")
        
        if self.call_handler and self.call_handler.is_running:
            status.append("  │  ", style="dim")
            status.append("📞 Call Active", style="green bold")
            
        self.console.print(status)
        self.console.print()

    def print_help(self):
        """Print available commands"""
        help_table = Table(title="Available Commands", show_header=True, header_style="bold cyan", box=box.ROUNDED)
        help_table.add_column("Command", style="green")
        help_table.add_column("Description")
        
        help_table.add_row("get/all", "List all agents")
        help_table.add_row("get/id", "Get details of active agent")
        help_table.add_row("set/{index}", "Set active agent by index from last get/all")
        help_table.add_row("create/", "Create a new agent interactively")
        help_table.add_row("update/", "Update active agent (interactive parameter selection)")
        help_table.add_row("delete/", "Delete active agent")
        help_table.add_row("inspect/", "Inspect last API call")
        help_table.add_row("call/start", "Start real-time voice call")
        help_table.add_row("call/stop", "Stop current voice call")
        help_table.add_row("call/logs", "Show call logs")
        help_table.add_row("help", "Show this help")
        help_table.add_row("exit / quit / q", "Exit the application")
        
        self.console.print(help_table)
        self.console.print()

    def get_command_input(self) -> str:
        """Get command input from user with prompt"""
        try:
            prompt_text = "[bold cyan]pranthora>[/bold cyan] "
            cmd = Prompt.ask(prompt_text, default="", show_default=False)
            return cmd.strip().lower()
        except (KeyboardInterrupt, EOFError):
            return "exit"

    def cmd_get_all(self):
        """Execute get/all command"""
        self.console.print("[cyan]Fetching all agents...[/cyan]")
        
        try:
            agents = self.client.agents.list()
            self.cached_agents = agents
            
            if not agents:
                self.console.print("[yellow]No agents found.[/yellow]")
                return
            
            table = Table(title=f"Agents ({len(agents)} total)", show_header=True, 
                         header_style="bold magenta", box=box.ROUNDED)
            table.add_column("Index", style="cyan bold", width=6)
            table.add_column("Name", style="green")
            table.add_column("ID", style="dim")
            table.add_column("Status", justify="center")
            table.add_column("Model", style="yellow")
            table.add_column("Voice", style="magenta")
            
            for idx, agent in enumerate(agents, 1):
                agent_data = agent.get('agent', {})
                configs = agent.get('configurations', {})
                
                name = agent_data.get('name', 'N/A')
                a_id = agent_data.get('id', 'N/A')
                is_active = agent_data.get('is_active', False)
                status = "[green]●[/green]" if is_active else "[red]○[/red]"
                
                # Get model and voice
                model_name = "N/A"
                voice_name = "N/A"
                if 'model' in configs:
                    model_name = configs['model'].get('model_provider_id', 'N/A')
                if 'tts' in configs:
                    voice_name = configs['tts'].get('voice_name', 'N/A')
                
                table.add_row(str(idx), name, a_id[:16] + "...", status, model_name, voice_name)
            
            self.console.print(table)
            self.console.print(f"\n[dim]Use [cyan]set/{{index}}[/cyan] to select an agent (e.g., set/1)[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")

    def cmd_set(self, index_str: str):
        """Execute set/{index} command"""
        if not self.cached_agents:
            self.console.print("[yellow]No cached agents. Run [cyan]get/all[/cyan] first.[/yellow]")
            # Auto-fetch
            self.console.print("[dim]Fetching agents...[/dim]")
            try:
                self.cached_agents = self.client.agents.list()
                self.cmd_get_all()  # Show the list
            except Exception as e:
                self.console.print(f"[red]Error fetching agents:[/red] {e}")
            return
        
        try:
            index = int(index_str)
            if 1 <= index <= len(self.cached_agents):
                agent = self.cached_agents[index - 1]
                self.active_agent_id = agent['agent']['id']
                self.active_agent_name = agent['agent'].get('name', 'Unknown')
                self.console.print(f"[green]✓ Selected agent:[/green] {self.active_agent_name} ({self.active_agent_id[:16]}...)")
            else:
                self.console.print(f"[red]Invalid index. Please use 1-{len(self.cached_agents)}[/red]")
        except ValueError:
            self.console.print("[red]Invalid index. Please provide a number.[/red]")

    def cmd_get_id(self):
        """Execute get/id command"""
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent. Use [cyan]set/{{index}}[/cyan] to select one.[/yellow]")
            return
        
        self.console.print(f"[cyan]Fetching details for {self.active_agent_id}...[/cyan]")
        
        try:
            agent = self.client.agents.get(self.active_agent_id)
            agent_info = agent.get('agent', {})
            configs = agent.get('configurations', {})
            
            # Agent Info Panel
            info_text = Text()
            info_text.append("Name: ", style="bold")
            info_text.append(f"{agent_info.get('name')}\n")
            info_text.append("ID: ", style="bold")
            info_text.append(f"{agent_info.get('id')}\n", style="dim")
            info_text.append("Status: ", style="bold")
            status = "Active" if agent_info.get('is_active') else "Inactive"
            info_text.append(f"{status}\n", style="green" if agent_info.get('is_active') else "red")
            info_text.append("Description: ", style="bold")
            info_text.append(f"{agent_info.get('description', 'N/A')}\n")
            info_text.append("Created: ", style="bold")
            info_text.append(f"{agent_info.get('created_at')}\n")
            
            self.console.print(Panel(info_text, title="Agent Information", border_style="cyan"))
            
            # Configurations
            if configs:
                config_tree = Tree("📋 Configurations")
                
                if 'model' in configs:
                    m = configs['model']
                    model_branch = config_tree.add("🧠 [bold]Model[/bold]")
                    model_branch.add(f"Provider: {m.get('model_provider_id', 'N/A')}")
                    model_branch.add(f"Prompt: {(m.get('system_prompt', 'N/A') or 'N/A')[:50]}...")
                    model_branch.add(f"Temperature: {m.get('temperature', 'N/A')}")
                
                if 'tts' in configs:
                    t = configs['tts']
                    tts_branch = config_tree.add("🗣️ [bold]TTS (Text-to-Speech)[/bold]")
                    tts_branch.add(f"Provider: {t.get('tts_provider_id', 'N/A')}")
                    tts_branch.add(f"Voice: {t.get('voice_name', 'N/A')}")
                
                if 'transcriber' in configs:
                    s = configs['transcriber']
                    stt_branch = config_tree.add("👂 [bold]Transcriber (STT)[/bold]")
                    stt_branch.add(f"Provider: {s.get('provider_id', 'N/A')}")
                    stt_branch.add(f"Model: {s.get('model_name', 'N/A')}")
                    stt_branch.add(f"Language: {s.get('language', 'N/A')}")
                
                if 'vad' in configs:
                    v = configs['vad']
                    vad_branch = config_tree.add("🎯 [bold]VAD (Voice Activity Detection)[/bold]")
                    vad_branch.add(f"Provider: {v.get('vad_provider_id', 'N/A')}")
                
                self.console.print(config_tree)
            
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")

    def cmd_create(self):
        """Execute create/ command with interactive prompts"""
        self.console.print(Panel("[bold]Create New Agent[/bold]", style="green"))
        
        # Name
        name = Prompt.ask("[cyan]Agent Name[/cyan]", default=f"Agent {int(time.time())}")
        
        # Description
        description = Prompt.ask("[cyan]Description[/cyan]", default="Created via SDK CLI")
        
        # First Response Message
        first_response = Prompt.ask(
            "[cyan]First Response Message[/cyan]", 
            default="Hello! How can I help you today?"
        )
        
        # System Prompt
        system_prompt = Prompt.ask(
            "[cyan]System Prompt[/cyan]",
            default="You are a helpful AI assistant."
        )
        
        # Model Selection
        self.console.print("\n[bold]Available LLM Models:[/bold]")
        models = list(LLM_MODELS.keys())
        for i, m in enumerate(models, 1):
            self.console.print(f"  {i}. {m}")
        model_idx = Prompt.ask("[cyan]Select Model (number or name)[/cyan]", default="gpt-4.1-mini")
        if model_idx.isdigit() and 1 <= int(model_idx) <= len(models):
            model = models[int(model_idx) - 1]
        else:
            model = model_idx
        
        # TTS Provider Selection
        self.console.print("\n[bold]Available TTS Providers:[/bold]")
        tts_providers = list(TTS_PROVIDERS.keys())
        for i, p in enumerate(tts_providers, 1):
            self.console.print(f"  {i}. {p}")
        tts_idx = Prompt.ask("[cyan]Select TTS Provider (number or name)[/cyan]", default="deepgram")
        if tts_idx.isdigit() and 1 <= int(tts_idx) <= len(tts_providers):
            tts_provider = tts_providers[int(tts_idx) - 1]
        else:
            tts_provider = tts_idx
        
        # Voice Selection (filtered by TTS provider)
        self.console.print(f"\n[bold]Available Voices for {tts_provider}:[/bold]")
        available_voices = [v for v, info in VOICES.items() if info.get('provider') == tts_provider]
        if not available_voices:
            available_voices = list(VOICES.keys())
            self.console.print(f"[dim](showing all voices)[/dim]")
        for i, v in enumerate(available_voices, 1):
            self.console.print(f"  {i}. {v}")
        voice_idx = Prompt.ask("[cyan]Select Voice (number or name)[/cyan]", default=available_voices[0] if available_voices else "thalia")
        if voice_idx.isdigit() and 1 <= int(voice_idx) <= len(available_voices):
            voice = available_voices[int(voice_idx) - 1]
        else:
            voice = voice_idx
        
        # Transcriber Selection
        self.console.print("\n[bold]Available Transcribers:[/bold]")
        transcribers = list(STT_CONFIGS.keys())
        for i, t in enumerate(transcribers, 1):
            self.console.print(f"  {i}. {t}")
        transcriber_idx = Prompt.ask("[cyan]Select Transcriber (number or name)[/cyan]", default="deepgram_nova_3")
        if transcriber_idx.isdigit() and 1 <= int(transcriber_idx) <= len(transcribers):
            transcriber = transcribers[int(transcriber_idx) - 1]
        else:
            transcriber = transcriber_idx
        
        # Confirm
        self.console.print("\n[bold]Summary:[/bold]")
        summary = Table(show_header=False, box=box.SIMPLE)
        summary.add_column("Field", style="cyan")
        summary.add_column("Value")
        summary.add_row("Name", name)
        summary.add_row("Description", description)
        summary.add_row("First Response", first_response[:50] + "..." if len(first_response) > 50 else first_response)
        summary.add_row("Model", model)
        summary.add_row("TTS Provider", tts_provider)
        summary.add_row("Voice", voice)
        summary.add_row("Transcriber", transcriber)
        self.console.print(summary)
        
        if not Confirm.ask("\n[yellow]Create this agent?[/yellow]", default=True):
            self.console.print("[dim]Cancelled.[/dim]")
            return
        
        # Create
        try:
            with self.console.status("[bold green]Creating agent...[/bold green]"):
                response = self.client.agents.create(
                    name=name,
                    description=description,
                    model=model,
                    voice=voice,
                    transcriber=transcriber,
                    first_response_message=first_response,
                    system_prompt=system_prompt
                )
            
            if 'agent' in response:
                new_id = response['agent']['id']
            else:
                new_id = response.get('id')
            
            self.active_agent_id = new_id
            self.active_agent_name = name
            self.console.print(f"\n[bold green]✅ Agent Created Successfully![/bold green]")
            self.console.print(f"[dim]ID: {new_id}[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]Error creating agent:[/red] {e}")

    def cmd_update(self):
        """Execute update/ command with interactive parameter selection"""
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent. Use [cyan]set/{{index}}[/cyan] to select one.[/yellow]")
            return
        
        self.console.print(Panel(f"[bold]Update Agent: {self.active_agent_name}[/bold]", style="yellow"))
        self.console.print("[dim]Select parameters to update. Type [cyan]/save[/cyan] to apply changes or [cyan]/cancel[/cyan] to abort.[/dim]\n")
        
        self.update_buffer = {}
        
        params = [
            ("name", "Agent Name", "str"),
            ("description", "Description", "str"),
            ("system_prompt", "System Prompt", "str"),
            ("first_response_message", "First Response Message", "str"),
            ("model", "LLM Model", "select_model"),
            ("voice", "Voice", "select_voice"),
            ("transcriber", "Transcriber", "select_transcriber"),
            ("temperature", "Temperature (0.0-1.0)", "float"),
        ]
        
        for param_key, param_label, param_type in params:
            self.console.print(f"\n[bold cyan]{param_label}[/bold cyan]")
            
            if param_type == "select_model":
                models = list(LLM_MODELS.keys())
                for i, m in enumerate(models[:10], 1):  # Show first 10
                    self.console.print(f"  {i}. {m}")
                if len(models) > 10:
                    self.console.print(f"  [dim]... and {len(models) - 10} more[/dim]")
                value = Prompt.ask(f"[cyan]Select or skip (Enter)[/cyan]", default="")
                if value:
                    if value.isdigit() and 1 <= int(value) <= len(models):
                        self.update_buffer["model"] = models[int(value) - 1]
                    else:
                        self.update_buffer["model"] = value
                        
            elif param_type == "select_voice":
                voices = list(VOICES.keys())
                for i, v in enumerate(voices, 1):
                    self.console.print(f"  {i}. {v}")
                value = Prompt.ask(f"[cyan]Select or skip (Enter)[/cyan]", default="")
                if value:
                    if value.isdigit() and 1 <= int(value) <= len(voices):
                        self.update_buffer["voice"] = voices[int(value) - 1]
                    else:
                        self.update_buffer["voice"] = value
                        
            elif param_type == "select_transcriber":
                transcribers = list(STT_CONFIGS.keys())
                for i, t in enumerate(transcribers, 1):
                    self.console.print(f"  {i}. {t}")
                value = Prompt.ask(f"[cyan]Select or skip (Enter)[/cyan]", default="")
                if value:
                    if value.isdigit() and 1 <= int(value) <= len(transcribers):
                        self.update_buffer["transcriber"] = transcribers[int(value) - 1]
                    else:
                        self.update_buffer["transcriber"] = value
                        
            elif param_type == "float":
                value = Prompt.ask(f"[cyan]Enter value or skip (Enter)[/cyan]", default="")
                if value:
                    try:
                        self.update_buffer[param_key] = float(value)
                    except ValueError:
                        self.console.print("[red]Invalid number, skipping.[/red]")
            else:
                value = Prompt.ask(f"[cyan]Enter value or skip (Enter)[/cyan]", default="")
                if value:
                    if value == "/save":
                        break
                    elif value == "/cancel":
                        self.console.print("[dim]Cancelled.[/dim]")
                        return
                    else:
                        self.update_buffer[param_key] = value
        
        # Show summary
        if not self.update_buffer:
            self.console.print("[yellow]No parameters to update.[/yellow]")
            return
        
        self.console.print("\n[bold]Parameters to Update:[/bold]")
        for k, v in self.update_buffer.items():
            self.console.print(f"  [cyan]{k}:[/cyan] {v}")
        
        if not Confirm.ask("\n[yellow]Apply these changes?[/yellow]", default=True):
            self.console.print("[dim]Cancelled.[/dim]")
            return
        
        # Apply update
        try:
            with self.console.status("[bold green]Updating agent...[/bold green]"):
                self.client.agents.update(self.active_agent_id, **self.update_buffer)
            self.console.print("[bold green]✅ Agent updated successfully![/bold green]")
        except ValueError as e:
            self.console.print(f"[red]Validation Error:[/red] {e}")
            self.console.print("[yellow]Tip: If updating system_prompt or temperature, make sure the agent has a model configured.[/yellow]")
        except Exception as e:
            error_str = str(e)
            # Parse API error messages for better display
            if "Field required" in error_str or "missing" in error_str.lower():
                self.console.print(f"[red]Missing Required Field:[/red]")
                self.console.print(f"[dim]{error_str}[/dim]")
                self.console.print("[yellow]Tip: Some fields require related configuration. Try updating the model first.[/yellow]")
            else:
                self.console.print(f"[red]Error updating agent:[/red] {e}")

    def cmd_delete(self):
        """Execute delete/ command"""
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent. Use [cyan]set/{{index}}[/cyan] to select one.[/yellow]")
            return
        
        self.console.print(Panel(
            f"[bold red]⚠️ Delete Agent[/bold red]\n\n"
            f"Name: [cyan]{self.active_agent_name}[/cyan]\n"
            f"ID: [dim]{self.active_agent_id}[/dim]",
            style="red"
        ))
        
        if not Confirm.ask("[red]Are you sure you want to delete this agent?[/red]", default=False):
            self.console.print("[dim]Cancelled.[/dim]")
            return
        
        try:
            with self.console.status("[bold red]Deleting agent...[/bold red]"):
                self.client.agents.delete(self.active_agent_id)
            self.console.print("[bold green]✅ Agent deleted successfully![/bold green]")
            self.active_agent_id = None
            self.active_agent_name = None
        except Exception as e:
            self.console.print(f"[red]Error deleting agent:[/red] {e}")

    def cmd_inspect(self):
        """Execute inspect/ command"""
        if not self.inspector.last_url:
            self.console.print("[yellow]No API calls made yet.[/yellow]")
            return
        
        self.console.print(Panel("[bold]Last API Call[/bold]", style="blue"))
        
        # Request info
        req_table = Table(show_header=False, box=box.SIMPLE)
        req_table.add_column("Key", style="bold cyan")
        req_table.add_column("Value")
        req_table.add_row("Method", self.inspector.last_method)
        req_table.add_row("URL", self.inspector.last_url)
        req_table.add_row("Status", str(self.inspector.last_status_code))
        req_table.add_row("Time", self.inspector.history[-1]["timestamp"] if self.inspector.history else "N/A")
        self.console.print(req_table)
        
        # Request payload
        if self.inspector.last_request.get("data"):
            self.console.print("\n[bold cyan]Request Payload:[/bold cyan]")
            req_json = json.dumps(self.inspector.last_request["data"], indent=2, default=str)
            self.console.print(Syntax(req_json, "json", theme="monokai"))
        
        # Response
        self.console.print("\n[bold green]Response:[/bold green]")
        res_json = json.dumps(self.inspector.last_response, indent=2, default=str)
        self.console.print(Syntax(res_json, "json", theme="monokai"))

    def cmd_call_start(self):
        """Execute call/start command"""
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent. Use [cyan]set/{{index}}[/cyan] to select one.[/yellow]")
            return
        
        if self.call_handler and self.call_handler.is_running:
            self.console.print("[yellow]A call is already in progress. Use [cyan]call/stop[/cyan] first.[/yellow]")
            return
        
        if not AUDIO_AVAILABLE:
            self.console.print("[red]Audio libraries not available. Install pyaudio and websockets:[/red]")
            self.console.print("[dim]pip install pyaudio websockets[/dim]")
            return
        
        self.console.print(Panel(f"[bold green]📞 Starting Voice Call[/bold green]\nAgent: {self.active_agent_name}", style="green"))
        
        # Ask for overrides
        use_overrides = Confirm.ask("Use assistant overrides?", default=False)
        overrides = None
        if use_overrides:
            var_name = Prompt.ask("Variable name", default="name")
            var_value = Prompt.ask("Variable value", default="User")
            overrides = {"variableValues": {var_name: var_value}}
        
        # Initialize call handler
        self.call_handler = CallSessionHandler(self.console, self.api_key, self.base_url)
        
        self.console.print("\n[dim]Starting call... Press Ctrl+C or type [cyan]call/stop[/cyan] to end.[/dim]\n")
        self.console.print("[bold]═══ Call Logs ═══[/bold]\n")
        
        success = self.call_handler.start(self.active_agent_id, overrides)
        
        if success:
            # Show status until manually stopped
            time.sleep(1)  # Give it a moment to connect
            
            if self.call_handler.is_running:
                self.console.print("\n[green]Call is active. Use [cyan]call/stop[/cyan] to end.[/green]")
            else:
                self.console.print("\n[yellow]Call ended or failed to connect.[/yellow]")

    def cmd_call_stop(self):
        """Execute call/stop command"""
        if not self.call_handler or not self.call_handler.is_running:
            self.console.print("[yellow]No active call to stop.[/yellow]")
            return
        
        self.call_handler.stop()
        
        # Show stats
        stats = self.call_handler.get_stats()
        self.console.print(Panel(
            f"[bold]Call Statistics[/bold]\n\n"
            f"Duration: {stats['duration_seconds']}s\n"
            f"Messages Received: {stats['messages_received']}\n"
            f"Audio Sent: {stats['audio_bytes_sent']} bytes\n"
            f"Audio Received: {stats['audio_bytes_received']} bytes\n"
            f"First Response: {'Yes' if stats['first_response_received'] else 'No'}",
            style="cyan"
        ))

    def cmd_call_logs(self):
        """Show call logs"""
        if not self.call_handler:
            self.console.print("[yellow]No call session. Use [cyan]call/start[/cyan] first.[/yellow]")
            return
        
        if not self.call_handler.logs:
            self.console.print("[yellow]No logs yet.[/yellow]")
            return
        
        self.console.print(Panel(f"[bold]Call Logs ({len(self.call_handler.logs)} entries)[/bold]", style="blue"))
        
        for log in self.call_handler.logs[-50:]:  # Last 50 logs
            color_map = {
                "INFO": "cyan",
                "SEND": "green",
                "RECV": "yellow",
                "FLAG": "magenta",
                "ERROR": "red",
                "AUDIO": "blue"
            }
            color = color_map.get(log['type'], "white")
            self.console.print(f"[{color}][{log['time']}] [{log['type']}][/{color}] {log['message']}")

    def run(self):
        """Main CLI loop"""
        self.print_header()
        self.print_help()
        
        while True:
            try:
                cmd = self.get_command_input()
                
                if not cmd:
                    continue
                
                # Parse command
                if cmd in ["exit", "quit", "q"]:
                    if self.call_handler and self.call_handler.is_running:
                        self.call_handler.stop()
                    self.console.print("[bold]Goodbye! 👋[/bold]")
                    break
                    
                elif cmd == "help":
                    self.print_help()
                    
                elif cmd == "get/all":
                    self.cmd_get_all()
                    
                elif cmd == "get/id":
                    self.cmd_get_id()
                    
                elif cmd.startswith("set/"):
                    index = cmd.replace("set/", "").strip()
                    if index:
                        self.cmd_set(index)
                    else:
                        # Tab completion - show agents
                        self.cmd_get_all()
                        idx = Prompt.ask("[cyan]Enter index[/cyan]", default="1")
                        self.cmd_set(idx)
                    
                elif cmd == "create/":
                    self.cmd_create()
                    
                elif cmd == "update/":
                    self.cmd_update()
                    
                elif cmd == "delete/":
                    self.cmd_delete()
                    
                elif cmd == "inspect/":
                    self.cmd_inspect()
                    
                elif cmd == "call/start":
                    self.cmd_call_start()
                    
                elif cmd == "call/stop":
                    self.cmd_call_stop()
                    
                elif cmd == "call/logs":
                    self.cmd_call_logs()
                    
                elif cmd == "clear":
                    self.print_header()
                    
                else:
                    self.console.print(f"[red]Unknown command:[/red] {cmd}")
                    self.console.print("[dim]Type [cyan]help[/cyan] for available commands.[/dim]")
                    
            except KeyboardInterrupt:
                self.console.print("\n[dim]Use [cyan]exit[/cyan] to quit or [cyan]call/stop[/cyan] to stop a call.[/dim]")
            except Exception as e:
                self.console.print(f"[red]Error:[/red] {e}")


def main():
    API_KEY = "1317d2fdec128bfd086fbcc2f10de57d"
    BASE_URL = "http://localhost:5050"
    
    console = Console()
    console.print(Panel(
        "[bold magenta]🚀 Pranthora SDK CLI[/bold magenta]\n"
        "[dim]Interactive command-line interface for the Pranthora SDK[/dim]",
        style="magenta"
    ))
    
    cli = InteractiveCLI(API_KEY, BASE_URL)
    try:
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting...[/bold]")
        sys.exit(0)


if __name__ == "__main__":
    main()
