# Mappings for Pranthora SDK
# This file contains mappings for Providers, Models, and Voices.

from typing import Optional

# --- TTS Providers ---
TTS_PROVIDERS = {
    "eleven_labs": "13ad1a5f-f2cf-46fe-be29-3ef0f9a3d211",
    "cartesia": "3889f8c4-039f-4f28-9b3a-67d4be8ada40",
    "deepgram": "75880080-722d-40fb-9e49-b379f68a89b2",
    "inworld": "bd248e98-da0d-4d30-b2df-99021e4821de",
    "azure": "ef36e21c-5cb5-4d2d-a55b-7b5a80ae5f64",
}

# --- STT Providers / Models ---
# Mapping friendly names to Provider IDs (and Model Names where applicable)
# Note: The API requires provider_id, model_name, language.
STT_CONFIGS = {
    "cartesia": {
        "id": "5add9b5d-cbd0-4e0a-886b-2eecb0bf1b10",
        "model": "ink-whisper",
        "language": "en"
    },
    "deepgram_flux": {
        "id": "63f5e32a-c163-4a4f-8000-e8a996abb183",
        "model": "flux-general-en",
        "language": "en"
    },
    "soniox": {
        "id": "9f653d3b-2c9d-4c9a-9c58-e1a50b81b7dd",
        "model": "stt-rt-preview-v2",
        "language": "en"
    },
    "faster_whisper": {
        "id": "a92491c1-e177-43a1-84dc-08dd3e7309b7",
        "model": "faster_whisper",
        "language": "en"
    },
    "sarvam": {
        "id": "b9d43de9-1728-4a43-ac2c-c4f97f0beffe",
        "model": "saarika:v2.5",
        "language": "en-IN"
    },
    "assembly_ai": {
        "id": "ce6aeefc-fe9b-4710-b16d-907ffca8e2b9",
        "model": "universal",
        "language": "en"
    },
    "deepgram_nova_3": {
        "id": "d8606a97-63c1-416e-83fa-720bb98c69e1",
        "model": "nova-3",
        "language": "en"
    }
}

# --- LLM Models ---
# Mapping model names to Model Provider IDs
LLM_MODELS = {
    # Azure
    "gpt-oss-120b": "19e29673-0885-4a78-9021-372da3647fc2",
    "gpt-4.1": "186b748d-e3a2-49bc-8a4a-53fe66208e4c",
    "model-router": "813c7c9a-fed1-4630-9150-f0ac0c15ef8d",
    "gpt-4.1-mini": "8b1a0f2c-bdc8-4f36-a114-aa2638be43d0",
    
    # DeepInfra
    "mistral-small": "d66a9798-5aab-41a0-b944-ca33a4046c2e",
    "llama-3.3-70b": "608bc6d2-ea00-4cd8-a511-cc6f2aa3d5c2",
    "qwen-14b": "50ef990e-ca6b-42ca-a5d1-4a48f2e42b8b",
    "hermes-3-70b": "7bc7813e-3c5e-4aa1-adec-2c0694d79269",
    "glm-4.5": "571ec61c-5998-4c50-95fc-f32fe3020434",
    "deepinfra-gpt-oss-120b": "7c4322da-5b40-485a-878f-c7f450233473",
    "llama-4-scout": "449c577d-92f1-493a-a99a-e469029b7117",
    "kimi-k2": "9031cf36-95d2-4946-9da8-cd015a1391d0",
    
    # Fireworks
    "fireworks-gpt-oss-120b": "be9b6fec-45ba-479c-9c1d-a48b85068c48",
    "deepseek-v3": "02ca1ec7-674f-45d3-9f89-20a1ea571852",
    
    # Gemini
    "gemini-2.5-flash-lite": "3793b663-01d1-4dc3-a4b3-4fb10b1ccaac",
    "gemini-2.5-flash": "cfee3ffc-b806-4ea0-bd20-6fe6f24ab9d8",
    "gemini-2.0-flash": "89e55bca-3e17-4eae-a9ec-6cbc2a6c275b",
    
    # Groq
    "groq-qwen-32b": "3988e495-744d-4331-aede-06193c5157e8",
    "groq-llama-3.3-70b": "2daa90f6-c0ac-4a90-abfd-d4b5e0390989",
    "groq-gpt-oss-20b": "d7b3a48c-8bbf-4d13-ab32-067e49d9eda5",
    "groq-compound": "3aee8cef-f02d-4732-9c96-21092b8bc972",
    "groq-gpt-oss-120b": "56e7ece1-91e9-498c-8925-de558e48e524",
    
    # OpenAI
    "openai-gpt-4.1-nano": "a0570122-69d3-427a-89ae-73839825c123",
    "openai-gpt-4.1": "b3714a39-3689-4b15-b15f-3f51af9dfad4",
    "openai-gpt-4.1-mini": "223f117d-90d3-4598-ae6b-8f1c49ae6266",
}

# --- Voices ---
# Mapping voice names to voice IDs (and provider)
VOICES = {
    # Cartesia
    "darla": {"id": "996a8b96-4804-46f0-8e05-3fd4ef1a87cd", "provider": "cartesia"},
    "jacqline": {"id": "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc", "provider": "cartesia"},
    "priya": {"id": "f6141af3-5f94-418c-80ed-a45d450e7e2e", "provider": "cartesia"},
    "carolina": {"id": "f9836c6e-a0bd-460e-9d3c-f7299fa60f94", "provider": "cartesia"},
    "blake": {"id": "a167e0f3-df7e-4d52-a9c3-f949145efdab", "provider": "cartesia"},
    "ronald": {"id": "5ee9feff-1265-424a-9d7f-8e4d431a12c7", "provider": "cartesia"},
    "jake": {"id": "729651dc-c6c3-4ee5-97fa-350da1f88600", "provider": "cartesia"},
    
    # Deepgram
    "thalia": {"id": "aura-2-thalia-en", "provider": "deepgram"},
    "aries": {"id": "aura-2-aries-en", "provider": "deepgram"},
    "apollo": {"id": "aura-2-apollo-en", "provider": "deepgram"},
    "andromeda": {"id": "aura-2-andromeda-en", "provider": "deepgram"},
    "asteria": {"id": "aura-2-asteria-en", "provider": "deepgram"},
}

# --- VAD Providers ---
# Assuming a default VAD provider or mapping if needed.
# From the API spec example: "c284bf92-658b-4d1b-a2ff-0cba0892fd29"
VAD_PROVIDERS = {
    "default": "c284bf92-658b-4d1b-a2ff-0cba0892fd29",
    "silero": "c284bf92-658b-4d1b-a2ff-0cba0892fd29", # Assuming this is Silero or standard VAD
}

# --- Reverse Mappings (ID -> Friendly Name) ---
# These are used to convert IDs back to friendly names in responses

# Reverse TTS Provider mapping
TTS_PROVIDERS_REVERSE = {v: k for k, v in TTS_PROVIDERS.items()}

# Reverse LLM Model mapping
LLM_MODELS_REVERSE = {v: k for k, v in LLM_MODELS.items()}

# Reverse STT Config mapping (by provider ID)
STT_CONFIGS_REVERSE = {}
for name, config in STT_CONFIGS.items():
    STT_CONFIGS_REVERSE[config["id"]] = name

# Reverse Voice mapping (by voice ID)
VOICES_REVERSE = {}
for name, voice_info in VOICES.items():
    VOICES_REVERSE[voice_info["id"]] = name

# Reverse VAD Provider mapping
VAD_PROVIDERS_REVERSE = {v: k for k, v in VAD_PROVIDERS.items()}

# Helper functions to get friendly names from IDs
def get_tts_provider_name(provider_id: str) -> Optional[str]:
    """Convert TTS provider ID to friendly name"""
    return TTS_PROVIDERS_REVERSE.get(provider_id, provider_id)

def get_model_name(model_provider_id: str) -> Optional[str]:
    """Convert model provider ID to friendly name"""
    return LLM_MODELS_REVERSE.get(model_provider_id, model_provider_id)

def get_transcriber_name(provider_id: str) -> Optional[str]:
    """Convert transcriber provider ID to friendly name"""
    return STT_CONFIGS_REVERSE.get(provider_id, provider_id)

def get_voice_name(voice_id: str) -> Optional[str]:
    """Convert voice ID to friendly name"""
    return VOICES_REVERSE.get(voice_id, voice_id)

def get_vad_provider_name(vad_provider_id: str) -> Optional[str]:
    """Convert VAD provider ID to friendly name"""
    return VAD_PROVIDERS_REVERSE.get(vad_provider_id, vad_provider_id)
