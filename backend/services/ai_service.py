from typing import Optional
from utils.agent import LLMProvider, GeminiProvider, OpenAICompatibleProvider

class AIService:
    @staticmethod
    def get_provider(provider_type: str, model_name: Optional[str] = None) -> LLMProvider:
        provider_type = provider_type.lower()
        if provider_type == "gemini":
            return GeminiProvider(model_name or "gemini-2.0-flash")
        elif provider_type in ["local", "openai"]:
            return OpenAICompatibleProvider(model_name or "qwen2.5-coder")
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
