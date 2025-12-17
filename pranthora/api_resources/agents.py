from typing import List, Optional, Dict, Any, Union
from pranthora.utils.api_requestor import APIRequestor
from pranthora.mappings import (
    TTS_PROVIDERS, STT_CONFIGS, LLM_MODELS, VOICES, VAD_PROVIDERS,
    get_tts_provider_name, get_model_name, get_transcriber_name, 
    get_voice_name, get_vad_provider_name
)

class Agents:
    def __init__(self, requestor: APIRequestor):
        self.requestor = requestor

    def _transform_agent_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent response to replace IDs with friendly names.
        
        Args:
            response: Raw API response
            
        Returns:
            Transformed response with friendly names
        """
        if not response:
            return response
        
        # Handle list of agents
        if isinstance(response, list):
            return [self._transform_agent_response(agent) for agent in response]
        
        # Transform single agent response
        transformed = response.copy()
        
        # Transform agent model config
        if "configurations" in transformed:
            configs = transformed["configurations"]
            
            # Transform model config
            if "model" in configs and isinstance(configs["model"], dict):
                model_config = configs["model"]
                if "model_provider_id" in model_config:
                    model_name = get_model_name(model_config["model_provider_id"])
                    model_config["model_name"] = model_name
                    # Keep original ID for reference
                    model_config["model_provider_id_original"] = model_config["model_provider_id"]
            
            # Transform TTS config
            if "tts" in configs and isinstance(configs["tts"], dict):
                tts_config = configs["tts"]
                if "tts_provider_id" in tts_config:
                    tts_name = get_tts_provider_name(tts_config["tts_provider_id"])
                    tts_config["tts_provider_name"] = tts_name
                    tts_config["tts_provider_id_original"] = tts_config["tts_provider_id"]
                if "voice_name" in tts_config:
                    voice_name = get_voice_name(tts_config["voice_name"])
                    tts_config["voice_name_friendly"] = voice_name
                    tts_config["voice_name_original"] = tts_config["voice_name"]
            
            # Transform transcriber config
            if "transcriber" in configs and isinstance(configs["transcriber"], dict):
                transcriber_config = configs["transcriber"]
                if "provider_id" in transcriber_config:
                    transcriber_name = get_transcriber_name(transcriber_config["provider_id"])
                    transcriber_config["transcriber_name"] = transcriber_name
                    transcriber_config["provider_id_original"] = transcriber_config["provider_id"]
            
            # Transform VAD config
            if "vad" in configs and isinstance(configs["vad"], dict):
                vad_config = configs["vad"]
                if "vad_provider_id" in vad_config:
                    vad_name = get_vad_provider_name(vad_config["vad_provider_id"])
                    vad_config["vad_provider_name"] = vad_name
                    vad_config["vad_provider_id_original"] = vad_config["vad_provider_id"]
        
        return transformed

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        # Model Config
        model: str = "gpt-4.1-mini", # Default model name
        temperature: float = 0.7,
        system_prompt: str = "You are a helpful assistant.",
        # TTS Config
        voice: str = "thalia", # Default voice name
        # STT Config
        transcriber: str = "deepgram_nova_3", # Default transcriber
        # VAD Config
        vad_provider: str = "default",
        # Other
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a complete agent with all configurations.
        
        Args:
            name: Name of the agent.
            description: Description of the agent.
            is_active: Whether the agent is active.
            model: Name of the LLM model (e.g., 'gpt-4.1', 'llama-3.3-70b').
            temperature: Model temperature.
            system_prompt: System prompt for the model.
            voice: Name of the voice (e.g., 'thalia', 'darla').
            transcriber: Name of the transcriber (e.g., 'deepgram_nova_3', 'faster_whisper').
            vad_provider: Name of the VAD provider.
            tools: List of tools.
            **kwargs: Additional overrides for specific configs.
        """
        
        # --- Resolve Model ---
        model_id = LLM_MODELS.get(model)
        if not model_id:
            # Fallback if user passed an ID directly or unknown name
            model_id = model 
            
        # --- Resolve Voice & TTS ---
        voice_info = VOICES.get(voice)
        if voice_info:
            voice_id = voice_info["id"]
            tts_provider_name = voice_info["provider"]
            tts_provider_id = TTS_PROVIDERS.get(tts_provider_name)
        else:
            # Fallback
            voice_id = voice
            tts_provider_id = TTS_PROVIDERS.get("deepgram") # Default fallback
            
        # --- Resolve Transcriber ---
        stt_info = STT_CONFIGS.get(transcriber)
        if stt_info:
            stt_provider_id = stt_info["id"]
            stt_model_name = stt_info["model"]
            stt_language = stt_info["language"]
        else:
            # Fallback
            stt_provider_id = transcriber
            stt_model_name = "nova-3"
            stt_language = "en"

        # --- Resolve VAD ---
        vad_id = VAD_PROVIDERS.get(vad_provider, VAD_PROVIDERS["default"])

        # Construct the payload - ensure all fields match backend schema
        payload = {
            "agent": {
                "name": name,
                "description": description or f"Agent using {model}",
                "is_active": is_active,
                "apply_noise_reduction": kwargs.get("apply_noise_reduction", False),
                "recording_enabled": kwargs.get("recording_enabled", False),
                "tts_filler_enabled": kwargs.get("tts_filler_enabled", None),
                "first_response_message": kwargs.get("first_response_message", None)
            },
            "agent_model_config": {
                "model_provider_id": model_id,
                "temperature": temperature,
                "system_prompt": system_prompt,
                "max_tokens": kwargs.get("max_tokens", 150),
                "tool_prompt": kwargs.get("tool_prompt", "Use tools when appropriate.")
            },
            "tts_config": {
                "tts_provider_id": tts_provider_id,
                "voice_name": voice_id,
                "voice_parameters": kwargs.get("voice_parameters", {"speed": 1.0, "pitch": 1.0, "volume": 1.0})
            },
            "transcriber_config": {
                "provider_id": stt_provider_id,
                "model_name": stt_model_name,
                "language": stt_language,
                "initial_prompt": kwargs.get("initial_prompt", "")
            },
            "vad_config": {
                "vad_provider_id": vad_id,
                "threshold": kwargs.get("vad_threshold", 0.5),
                "min_speech_duration_ms": kwargs.get("min_speech_duration_ms", 250.0),
                "min_silence_duration_ms": kwargs.get("min_silence_duration_ms", 500.0)
            },
            "inferencing_config": {
                "vad": True,
                "stt": True,
                "llm": True,
                "tts": True
            }
        }
        
        if tools:
            payload["tools"] = tools

        # SDK uses the dedicated API-key based agents controller
        response = self.requestor.request("POST", "/agents", data=payload)
        return self._transform_agent_response(response)

    def list(self) -> List[Dict[str, Any]]:
        """
        Get all agents for the current user.
        
        Returns:
            List of agent dictionaries with complete agent information.
            IDs are converted to friendly names (model_name, tts_provider_name, etc.)
        """
        # SDK uses the dedicated API-key based agents controller
        response = self.requestor.request("GET", "/agents")
        return self._transform_agent_response(response)

    def get(self, agent_id: str) -> Dict[str, Any]:
        """
        Get a specific agent by ID.
        
        Args:
            agent_id: The ID of the agent to retrieve.
            
        Returns:
            Agent dictionary with complete information.
            IDs are converted to friendly names (model_name, tts_provider_name, etc.)
        """
        # SDK uses the dedicated API-key based agents controller
        response = self.requestor.request("GET", f"/agents/{agent_id}")
        return self._transform_agent_response(response)

    def update(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        # Model Config
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        # TTS Config
        voice: Optional[str] = None,
        # STT Config
        transcriber: Optional[str] = None,
        # VAD Config
        vad_provider: Optional[str] = None,
        # Other
        tools: Optional[List[Dict[str, Any]]] = None,
        force_update: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an agent with new configurations.
        
        Args:
            agent_id: The ID of the agent to update.
            name: Name of the agent.
            description: Description of the agent.
            is_active: Whether the agent is active.
            model: Name of the LLM model (e.g., 'gpt-4.1', 'llama-3.3-70b').
            temperature: Model temperature.
            system_prompt: System prompt for the model.
            voice: Name of the voice (e.g., 'thalia', 'darla').
            transcriber: Name of the transcriber (e.g., 'deepgram_nova_3', 'faster_whisper').
            vad_provider: Name of the VAD provider.
            tools: List of tools.
            force_update: If True, allows updating active agents. Default is True.
            **kwargs: Additional overrides for specific configs.
            
        Returns:
            Updated agent dictionary with complete information.
        """
        payload = {}
        
        # Build agent payload - name is required for updates if agent is provided
        agent_data = {}
        
        # If any agent field is being updated, we need to include name
        # If name is not provided, fetch current agent's name
        needs_agent_update = (
            name is not None or 
            description is not None or 
            is_active is not None or
            "apply_noise_reduction" in kwargs or
            "recording_enabled" in kwargs or
            "tts_filler_enabled" in kwargs or
            "first_response_message" in kwargs
        )
        
        if needs_agent_update:
            if name is not None:
                agent_data["name"] = name
            else:
                # Fetch current agent to get existing name
                try:
                    current_agent = self.get(agent_id)
                    agent_info = current_agent.get('agent', {})
                    existing_name = agent_info.get('name')
                    if existing_name:
                        agent_data["name"] = existing_name
                except Exception:
                    # If we can't fetch, let the API return an error
                    pass
            
            if description is not None:
                agent_data["description"] = description
            if is_active is not None:
                agent_data["is_active"] = is_active
            # Include optional fields if provided
            if "apply_noise_reduction" in kwargs:
                agent_data["apply_noise_reduction"] = kwargs["apply_noise_reduction"]
            if "recording_enabled" in kwargs:
                agent_data["recording_enabled"] = kwargs["recording_enabled"]
            if "tts_filler_enabled" in kwargs:
                agent_data["tts_filler_enabled"] = kwargs["tts_filler_enabled"]
            if "first_response_message" in kwargs:
                agent_data["first_response_message"] = kwargs["first_response_message"]
            
            if agent_data:
                payload["agent"] = agent_data
        
        # Build model config if provided
        if model is not None or temperature is not None or system_prompt is not None:
            model_config = {}
            
            # If model is provided, use it
            if model is not None:
                model_id = LLM_MODELS.get(model)
                if not model_id:
                    model_id = model  # Fallback
                model_config["model_provider_id"] = model_id
            # If model is not provided but system_prompt or temperature is, fetch current agent
            elif system_prompt is not None or temperature is not None:
                # Fetch current agent to get existing model_provider_id
                try:
                    current_agent = self.get(agent_id)
                    configs = current_agent.get('configurations', {})
                    if 'model' in configs:
                        existing_model_id = configs['model'].get('model_provider_id')
                        if existing_model_id:
                            model_config["model_provider_id"] = existing_model_id
                        else:
                            # Fallback: try to get from agent_model_config if available
                            if 'agent_model_config' in current_agent:
                                existing_model_id = current_agent['agent_model_config'].get('model_provider_id')
                                if existing_model_id:
                                    model_config["model_provider_id"] = existing_model_id
                except Exception:
                    # If we can't fetch, we'll let the API return an error
                    pass
            
            if temperature is not None:
                model_config["temperature"] = temperature
            if system_prompt is not None:
                model_config["system_prompt"] = system_prompt
            if "max_tokens" in kwargs:
                model_config["max_tokens"] = kwargs["max_tokens"]
            if "tool_prompt" in kwargs:
                model_config["tool_prompt"] = kwargs["tool_prompt"]
            
            # Only add model_config if it has model_provider_id (required)
            if model_config.get("model_provider_id"):
                payload["agent_model_config"] = model_config
            elif model_config:
                # If we have other fields but no model_provider_id, raise an error
                raise ValueError(
                    "Cannot update model configuration without model_provider_id. "
                    "Please provide 'model' parameter or ensure the agent has an existing model configuration."
                )
        
        # Build TTS config if provided
        if voice is not None:
            tts_config = {}
            voice_info = VOICES.get(voice)
            if voice_info:
                voice_id = voice_info["id"]
                tts_provider_name = voice_info["provider"]
                tts_provider_id = TTS_PROVIDERS.get(tts_provider_name)
            else:
                voice_id = voice
                tts_provider_id = TTS_PROVIDERS.get("deepgram")
            tts_config["tts_provider_id"] = tts_provider_id
            tts_config["voice_name"] = voice_id
            if "voice_parameters" in kwargs:
                tts_config["voice_parameters"] = kwargs["voice_parameters"]
            payload["tts_config"] = tts_config
        
        # Build transcriber config if provided
        if transcriber is not None:
            transcriber_config = {}
            stt_info = STT_CONFIGS.get(transcriber)
            if stt_info:
                stt_provider_id = stt_info["id"]
                stt_model_name = stt_info["model"]
                stt_language = stt_info["language"]
            else:
                stt_provider_id = transcriber
                stt_model_name = "nova-3"
                stt_language = "en"
            transcriber_config["provider_id"] = stt_provider_id
            transcriber_config["model_name"] = stt_model_name
            transcriber_config["language"] = stt_language
            if "initial_prompt" in kwargs:
                transcriber_config["initial_prompt"] = kwargs["initial_prompt"]
            payload["transcriber_config"] = transcriber_config
        
        # Build VAD config if provided
        if vad_provider is not None:
            vad_config = {}
            vad_id = VAD_PROVIDERS.get(vad_provider, VAD_PROVIDERS["default"])
            vad_config["vad_provider_id"] = vad_id
            if "vad_threshold" in kwargs:
                vad_config["threshold"] = kwargs["vad_threshold"]
            if "min_speech_duration_ms" in kwargs:
                vad_config["min_speech_duration_ms"] = kwargs["min_speech_duration_ms"]
            if "min_silence_duration_ms" in kwargs:
                vad_config["min_silence_duration_ms"] = kwargs["min_silence_duration_ms"]
            payload["vad_config"] = vad_config
        
        # Add tools if provided
        if tools is not None:
            payload["tools"] = tools
        
        # Add force_update as query parameter
        params = {}
        if force_update:
            params["force_update"] = "true"
        
        # SDK uses the dedicated API-key based agents controller
        response = self.requestor.request("PUT", f"/agents/{agent_id}", data=payload, params=params if params else None)
        return self._transform_agent_response(response)

    def delete(self, agent_id: str, force_delete: bool = True) -> Dict[str, Any]:
        """
        Delete a specific agent by ID.
        
        Args:
            agent_id: The ID of the agent to delete.
            force_delete: If True, allows deletion of active agents. Default is True.
            
        Returns:
            Dictionary with success status.
        """
        params = {"force_delete": "true" if force_delete else "false"}
        # SDK uses the dedicated API-key based agents controller
        return self.requestor.request("DELETE", f"/agents/{agent_id}", params=params)
