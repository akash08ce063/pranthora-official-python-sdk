from typing import Dict, Any, Optional
from pranthora.utils.api_requestor import APIRequestor


class Calls:
    def __init__(self, requestor: APIRequestor):
        self.requestor = requestor

    def create(
        self,
        phone_number: str,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call to a phone number, optionally with a specific agent.

        Args:
            phone_number: The phone number to call (e.g. "+1234567890").
            agent_id: Optional agent ID. If provided, the call is handled by this agent.
                     If omitted, the backend uses the agent mapped to your Twilio number.

        Returns:
            Dict with status, call_sid, from_phone_number, etc.
        """
        params: Dict[str, Any] = {"phoneNumber": phone_number}
        if agent_id:
            params["agent_id"] = agent_id
        return self.requestor.request("POST", "/calls", params=params)

    def stop(
        self,
        call_sid: str,
        from_phone_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Hang up an active call.

        Args:
            call_sid: Twilio call SID returned from create() or start().
            from_phone_number: Your Twilio number that placed the call (required by backend to resolve Twilio client).

        Returns:
            Dict with status from the API.
        """
        data: Dict[str, Any] = {"call_sid": call_sid}
        if from_phone_number:
            data["from_phone_number"] = from_phone_number
        return self.requestor.request("POST", "/calls/stop", data=data)

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
