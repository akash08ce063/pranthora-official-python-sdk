from typing import Optional, Dict, Any

from pranthora.utils.api_requestor import APIRequestor
from pranthora.api_resources.agents import Agents
from pranthora.api_resources.calls import Calls


class Pranthora:
    def __init__(self, api_key: str, base_url: str = "https://api.pranthora.com/api/v1"):
        """
        Initialize the Pranthora client.

        Args:
            api_key: Your Pranthora API key.
            base_url: The base URL for the API (must include /api/v1).
                      Defaults to https://api.pranthora.com/api/v1.
                      Use "http://localhost:5050/api/v1" for local development.
        """
        self.api_key = api_key
        self.base_url = base_url

        self.requestor = APIRequestor(api_key, base_url)

        # Resources
        self.agents = Agents(self.requestor)
        self.calls = Calls(self.requestor)

        # Track last outbound call for stop()
        self._last_call_sid: Optional[str] = None
        self._last_from_phone_number: Optional[str] = None

    def start(
        self,
        agent_id: str,
        to_phone_number: Optional[str] = None,
        assistant_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Start a real-time voice call.

        For outbound phone calls: pass agent_id and to_phone_number.
        The backend will use your attached Twilio number to call to_phone_number
        and connect the call to the specified agent.

        Args:
            agent_id: The agent ID to use for the call.
            to_phone_number: Phone number to call (e.g. "+1234567890"). Required for outbound.
            assistant_overrides: Optional overrides (e.g. variableValues). Reserved for future use.

        Returns:
            Dict with status, call_sid, from_phone_number, etc. Use call_sid with stop() to hang up.
        """
        if not to_phone_number:
            raise ValueError(
                "to_phone_number is required for outbound calls. "
                "Example: client.start(agent_id='...', to_phone_number='+1234567890')"
            )
        result = self.calls.create(phone_number=to_phone_number, agent_id=agent_id)
        self._last_call_sid = result.get("call_sid")
        self._last_from_phone_number = result.get("from_phone_number")
        return result

    def stop(
        self,
        call_sid: Optional[str] = None,
        from_phone_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stop (hang up) an active call.

        Args:
            call_sid: Twilio call SID. If omitted, uses the call from the last start().
            from_phone_number: Your Twilio number that placed the call. If omitted, uses the one from last start().

        Returns:
            Dict with status from the API.
        """
        sid = call_sid or self._last_call_sid
        if not sid:
            raise ValueError(
                "No call_sid provided and no recent call. "
                "Pass call_sid (and optionally from_phone_number) or call start() first."
            )
        from_phone = from_phone_number or self._last_from_phone_number
        return self.calls.stop(call_sid=sid, from_phone_number=from_phone)
