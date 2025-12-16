import json
import threading
import time
import unittest
import sys

from pranthora import Pranthora
from pranthora.realtime import VoiceClient, PYAUDIO_AVAILABLE
from pranthora.exceptions import AuthenticationError, APIError


class TestRealtimeCall(unittest.TestCase):
    """
    End-to-end realtime call test that streams mic audio to the agent and
    plays agent audio back through the terminal session (logs).
    - Keeps the call open until user presses 'q' to quit.
    - Logs interruption and other events for observability.
    """

    # Use the provided agent for this test run
    TARGET_AGENT_ID = "b7d26e2e-d7d8-48e5-b24a-56149235fd3c"

    def setUp(self):
        # Reuse the real API key/base URL from the main SDK tests
        self.api_key = "kxL8EekUH8YNdL2jWvECtLslacdvZNFv"
        self.base_url = "http://localhost:5050"
        self.client = Pranthora(api_key=self.api_key, base_url=self.base_url)

    def _wait_for_q_key(self, vc, connected_event):
        """Wait for 'q' key press - only start after connection is established"""
        # Wait for connection to be established first
        if not connected_event.wait(timeout=10):
            print("⚠️  Connection not established within 10 seconds")
            return
        
        print("\n⌨️  Press 'q' and Enter to end the call...\n")
        
        # Now wait for 'q' input in a separate thread
        def keyboard_monitor():
            try:
                # This will block until user types something and presses Enter
                line = sys.stdin.readline().strip().lower()
                if line == 'q':
                    print("\n🛑 'q' pressed - ending call...")
                    vc.stop()
            except (EOFError, KeyboardInterrupt):
                print("\n🛑 Input interrupted - ending call...")
                vc.stop()
            except Exception as e:
                print(f"⚠️  Error reading input: {e}")
                vc.stop()
        
        # Start keyboard monitoring in a separate thread
        keyboard_thread = threading.Thread(target=keyboard_monitor, daemon=True)
        keyboard_thread.start()
        
        # Wait for the call to end (either by 'q' or other means)
        while vc.is_running:
            time.sleep(0.5)
        
        # Give keyboard thread a moment to finish
        keyboard_thread.join(timeout=1)

    def test_realtime_call_with_timeout_and_audio(self):
        if not PYAUDIO_AVAILABLE:
            self.skipTest("PyAudio is required for realtime audio streaming; not available in this env.")

        vc = VoiceClient(self.base_url, self.api_key)
        disconnected_event = threading.Event()
        connected_event = threading.Event()

        # ---- Callbacks for visibility and control ----
        def on_connected():
            print("🔌 WebSocket connected")
            connected_event.set()

        def on_disconnected():
            print("🔌 WebSocket disconnected")
            disconnected_event.set()

        def on_first_response(message: str):
            print(f"🗣️  First agent response: {message}")

        def on_transcript(role: str, text: str):
            print(f"[{role}] {text}")

        def on_interruption():
            print("⚡ Interruption signaled by server")

        def on_agent_start():
            print("▶️  Agent started speaking")

        def on_agent_stop():
            print("⏹️  Agent stopped speaking")

        def on_error(msg: str):
            print(f"❌ Error: {msg}")

        def on_message(data: dict):
            # Truncate for readability
            try:
                print(f"📨 Event: {json.dumps(data)[:300]}")
            except Exception:
                print(f"📨 Event (non-serializable): {data}")

        # Attach callbacks
        vc.on_connected = on_connected
        vc.on_disconnected = on_disconnected
        vc.on_first_response = on_first_response
        vc.on_transcript = on_transcript
        vc.on_interruption = on_interruption
        vc.on_agent_speaking_start = on_agent_start
        vc.on_agent_speaking_stop = on_agent_stop
        vc.on_error = on_error
        vc.on_message = on_message

        try:
            print(f"\n=== Starting realtime call to agent {self.TARGET_AGENT_ID} ===")
            print("🎤 Speak into your microphone; agent audio will be played through speakers.")
            print("⌨️  Press 'q' and Enter to end the call when done.\n")
            
            started = vc.start(self.TARGET_AGENT_ID)
            self.assertTrue(started, "Voice client failed to start")

            # Wait for connection and then start keyboard monitoring
            # This will keep the call open until 'q' is pressed
            self._wait_for_q_key(vc, connected_event)

            # Wait for the background thread to exit
            if vc.thread:
                vc.thread.join(timeout=5)

            stats = vc.get_stats()
            print(f"\n📊 Session stats: {stats}")
            self.assertFalse(vc.is_running, "Voice client should be stopped after cleanup")
            
            if stats["messages_received"] > 0:
                print(f"✅ Call completed successfully with {stats['messages_received']} messages received")
            else:
                print("⚠️  No messages received during call")

        except AuthenticationError as e:
            print(f"Auth failed: {e}")
            self.skipTest(f"Authentication failed: {e}")
        except APIError as e:
            print(f"API error during realtime call: {e}")
            self.skipTest(f"API error: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            vc.stop()
            if vc.thread:
                vc.thread.join(timeout=2)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            vc.stop()
            if vc.thread:
                vc.thread.join(timeout=2)
            raise


if __name__ == "__main__":
    unittest.main(verbosity=2)

