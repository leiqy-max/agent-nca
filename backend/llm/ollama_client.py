import os
import requests
from typing import List
from .base import BaseLLM, BaseEmbedding

class OllamaLLM(BaseLLM):
    def __init__(self, base_url: str = None, model: str = "qwen:7b"):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))

    def _normalize_messages(self, messages: List[dict]) -> List[dict]:
        normalized = []
        for message in messages:
            item = dict(message)
            if item.get("images"):
                item["images"] = [
                    image.split(",", 1)[1] if isinstance(image, str) and "," in image else image
                    for image in item["images"]
                ]
            normalized.append(item)
        return normalized

    def chat(self, messages: List[dict], temperature: float = 0.7, options: dict = None, timeout: int = None) -> str:
        # Ollama API: POST /api/chat
        url = f"{self.base_url}/api/chat"
        request_options = {
            "temperature": temperature
        }
        if options:
            request_options.update(options)
        payload = {
            "model": self.model,
            "messages": self._normalize_messages(messages),
            "stream": False,
            "options": request_options
        }
        keep_alive = os.getenv("OLLAMA_KEEP_ALIVE")
        if keep_alive:
            payload["keep_alive"] = keep_alive
        try:
            resp = requests.post(url, json=payload, timeout=timeout or self.timeout)
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

class OllamaEmbedding(BaseEmbedding):
    def __init__(self, base_url: str = None, model: str = "nomic-embed-text"):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model
        self.timeout = int(os.getenv("EMBEDDING_TIMEOUT", "120"))

    def embed_text(self, text: str) -> List[float]:
        # Ollama API: POST /api/embeddings
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("embedding", [])
        except Exception as e:
            print(f"Error calling Ollama embedding: {e}")
            return []
