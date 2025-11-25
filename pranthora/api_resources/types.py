from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# --- Agent Configuration Types ---

class ModelConfig(BaseModel):
    model_provider_id: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 150
    system_prompt: Optional[str] = None
    tool_prompt: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None

class TtsConfig(BaseModel):
    tts_provider_id: str
    voice_name: Optional[str] = None
    voice_parameters: Optional[Dict[str, Any]] = None

class TranscriberConfig(BaseModel):
    provider_id: str
    model_name: str
    language: str
    initial_prompt: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None

class VadConfig(BaseModel):
    vad_provider_id: str
    threshold: Optional[float] = 0.5
    min_speech_duration_ms: Optional[float] = 250.0
    min_silence_duration_ms: Optional[float] = 500.0
    max_allowed_silence_duration: Optional[float] = 0.0
    sampling_rate: Optional[float] = 16000.0

class InferencingConfig(BaseModel):
    vad: bool = True
    stt: bool = True
    llm: bool = True
    tts: bool = True

class ToolConfig(BaseModel):
    tool_type: str
    tool_id: str
    config_overrides: Optional[Dict[str, Any]] = None

# --- Agent Types ---

class Agent(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    apply_noise_reduction: bool = False
    recording_enabled: bool = False
    tts_filler_enabled: bool = False

class CompleteAgent(BaseModel):
    id: Optional[str] = None
    agent: Agent
    agent_model_config: Optional[ModelConfig] = None
    tts_config: Optional[TtsConfig] = None
    transcriber_config: Optional[TranscriberConfig] = None
    vad_config: Optional[VadConfig] = None
    inferencing_config: Optional[InferencingConfig] = None
    tools: Optional[List[ToolConfig]] = None

# --- Call Types ---

class CreateCallResponse(BaseModel):
    status: str
    message: str
    call_sid: Optional[str] = None
