from typing import Optional, Dict, Any
from pranthora.utils.api_requestor import APIRequestor
from pranthora.api_resources.agents import Agents
from pranthora.api_resources.calls import Calls
from pranthora.realtime import VoiceClient

class Pranthora:
    def __init__(self, api_key: str, base_url: str = "https://api-pranthora.firstpeak.ai"):
        """
        Initialize the Pranthora client.

        Args:
            api_key: Your Pranthora API key.
            base_url: The base URL for the API. Defaults to production.
                      Use "http://localhost:5050" for local development.
        """
        self.api_key = api_key
        self.base_url = base_url
        
        self.requestor = APIRequestor(api_key, base_url)
        
        # Resources
        # Resources
        self.agents = Agents(self.requestor)
        self.calls = Calls(self.requestor)
        
        self._voice_client = None

    def start(self, agent_id: str, assistant_overrides: Optional[Dict[str, Any]] = None):
        """
        Start a real-time voice session with an agent.
        This connects your local microphone and speaker to the agent.
        
        Args:
            agent_id: The ID of the agent to connect to.
            assistant_overrides: Optional configuration overrides.
                Example: {"variableValues": {"name": "John"}}
        """
        if not self._voice_client:
            self._voice_client = VoiceClient(self.base_url, self.api_key)
        
        self._voice_client.start(agent_id, assistant_overrides)

    def stop(self):
        """
        Stop the current voice session.
        """
        if self._voice_client:
            self._voice_client.stop()
