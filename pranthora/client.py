from pranthora.utils.api_requestor import APIRequestor
from pranthora.api_resources.agents import Agents
from pranthora.api_resources.calls import Calls

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
        self.agents = Agents(self.requestor)
        self.calls = Calls(self.requestor)
