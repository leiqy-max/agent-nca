import os
from .base import BaseLLM, BaseEmbedding

def get_llm_client(model: str = None) -> BaseLLM:
    provider = os.getenv("LLM_PROVIDER", "zhipu").lower()
    if provider == "ollama":
        from .ollama_client import OllamaLLM
        return OllamaLLM(model=model or os.getenv("LLM_MODEL", "qwen:7b"))
    elif provider == "mock":
        from .mock_client import MockLLM
        return MockLLM(model=model or "mock")
    elif provider in ["deepseek-v3", "openai", "siliconflow"]:
        from .openai_client import OpenAICompatibleLLM
        return OpenAICompatibleLLM(
            model=model or os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
            api_key=os.getenv("LLM_API_KEY")
        )
    else:
        from .zhipu_client import ZhipuLLM
        return ZhipuLLM(
            model=model or os.getenv("LLM_MODEL", "glm-4"),
            api_key=os.getenv("LLM_API_KEY")
        )

def get_embedding_client(model: str = None) -> BaseEmbedding:
    provider = os.getenv("LLM_PROVIDER", "zhipu").lower()
    if provider == "ollama":
        from .ollama_client import OllamaEmbedding
        return OllamaEmbedding(model=model or os.getenv("EMBEDDING_MODEL", "m3e"))
    elif provider == "mock":
        from .mock_client import MockEmbedding
        return MockEmbedding(model=model or "mock")
    elif provider in ["deepseek-v3", "openai", "siliconflow"]:
        from .openai_client import OpenAICompatibleEmbedding
        return OpenAICompatibleEmbedding(
            model=model or os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
            base_url=os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1"),
            api_key=os.getenv("LLM_API_KEY")
        )
    else:
        from .zhipu_client import ZhipuEmbedding
        return ZhipuEmbedding(
            model=model or os.getenv("EMBEDDING_MODEL", "embedding-2"),
            api_key=os.getenv("LLM_API_KEY")
        )
