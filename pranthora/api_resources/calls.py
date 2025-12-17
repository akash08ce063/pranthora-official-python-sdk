from typing import Dict, Any
from pranthora.utils.api_requestor import APIRequestor

class Calls:
    def __init__(self, requestor: APIRequestor):
        self.requestor = requestor

    def create(
        self,
        phone_number: str,
        agent_id: str = None, # Optional in API spec? Spec says create_call takes phoneNumber in query. 
                              # Wait, spec says /api/call/create_call takes phoneNumber in query. 
                              # It doesn't seem to take agent_id in the spec shown! 
                              # Let's re-read spec. 
                              # Line 616: /api/call/create_call
                              # Parameters: phoneNumber (query).
                              # It seems the current backend implementation might be simple.
                              # However, usually you need an agent_id. 
                              # Let's stick to the spec: only phoneNumber.
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call.
        """
        params = {"phoneNumber": phone_number}
        # If the backend supports agent_id (which it should), we'd add it here.
        # Based on the spec provided, it only lists phoneNumber. 
        # I will add agent_id as an optional param just in case the spec is incomplete or updated.
        if agent_id:
            params["agent_id"] = agent_id

        # SDK uses the dedicated API-key based calls controller.
        return self.requestor.request("POST", "/calls", params=params)

    def initiate_conference(
        self,
        to_numbers,
        conference_name: str | None = None,
    ) -> Dict[str, Any]:
        """
        Initiate a conference call using the API-key based SDK endpoint.

        Args:
            to_numbers: List of phone numbers to dial into the conference.
            conference_name: Optional custom conference name.
        """
        payload: Dict[str, Any] = {"to_numbers": to_numbers}
        if conference_name:
            payload["conference_name"] = conference_name

        return self.requestor.request(
            "POST",
            "/calls/conference",
            data=payload,
        )
