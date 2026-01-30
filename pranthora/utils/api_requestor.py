import requests
import json
from typing import Optional, Dict, Any, Union
from pranthora.exceptions import (
    APIError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
    APIConnectionError,
)


def _looks_like_jwt(token: str) -> bool:
    """Return True if the token looks like a JWT (3 dot-separated segments)."""
    if not token or not isinstance(token, str):
        return False
    parts = token.strip().split(".")
    return len(parts) == 3


class APIRequestor:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _serialize_data(self, data: Any, depth: int = 0) -> Any:
        """Recursively ensure data is JSON-serializable and convert dataclasses/Pydantic models."""
        # Prevent infinite recursion
        if depth > 50:
            return str(data)
        
        # Handle Pydantic models
        if hasattr(data, 'dict'):
            try:
                data = data.dict()
            except:
                pass
        elif hasattr(data, 'model_dump'):
            try:
                data = data.model_dump()
            except:
                pass
        
        # Handle dataclasses - check if it's an instance, not the class itself
        if hasattr(data, '__dataclass_fields__') and not isinstance(data, type):
            try:
                from dataclasses import asdict, is_dataclass
                if is_dataclass(data):
                    data = asdict(data)
            except:
                pass
        
        if isinstance(data, dict):
            return {k: self._serialize_data(v, depth + 1) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._serialize_data(item, depth + 1) for item in data]
        else:
            return data

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Pranthora/Python/1.0.0",
        }
        if _looks_like_jwt(self.api_key):
            default_headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            default_headers["X-API-Key"] = self.api_key
        
        if headers:
            default_headers.update(headers)

        # Serialize data to ensure all dataclasses/Pydantic models are converted to dicts
        serialized_data = self._serialize_data(data) if data else None
        
        # Ensure all values are JSON-serializable primitives
        if serialized_data is not None:
            try:
                # Test serialization
                json.dumps(serialized_data, default=str)
            except (TypeError, ValueError) as e:
                # If serialization fails, convert all non-serializable types
                serialized_data = json.loads(json.dumps(serialized_data, default=str))

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=serialized_data,
                headers=default_headers,
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Error communicating with Pranthora: {e}")

        if not 200 <= response.status_code < 300:
            self._handle_error(response)

        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text

    def _handle_error(self, response: requests.Response):
        try:
            error_data = response.json()
            error_msg = error_data.get("error") or error_data.get("detail") or response.text
        except json.JSONDecodeError:
            error_msg = response.text

        if response.status_code == 401:
            raise AuthenticationError(error_msg, response.status_code, response.text)
        elif response.status_code == 403:
            raise PermissionError(error_msg, response.status_code, response.text)
        elif response.status_code == 404:
            raise NotFoundError(error_msg, response.status_code, response.text)
        elif response.status_code == 429:
            raise RateLimitError(error_msg, response.status_code, response.text)
        else:
            raise APIError(error_msg, response.status_code, response.text)
