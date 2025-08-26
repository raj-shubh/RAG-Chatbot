import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


@dataclass
class Message:
    role: str
    content: str


class LLMClient:
    def __init__(self, provider: str = "auto", model: Optional[str] = None):
        self.provider = provider
        self.model = model

        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = model or os.getenv("OLLAMA_MODEL", "llama3.1")

        if self.provider == "auto":
            if self.openai_key:
                self.provider = "openai"
            else:
                self.provider = "ollama"

    def is_available(self) -> bool:
        if self.provider == "openai":
            return bool(self.openai_key and OpenAI is not None)
        if self.provider == "ollama":
            try:
                resp = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
                return resp.status_code == 200
            except Exception:
                return False
        return False

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "openai":
            return self._complete_openai(system_prompt, user_prompt)
        elif self.provider == "ollama":
            return self._complete_ollama(system_prompt, user_prompt)
        else:
            raise RuntimeError("Unknown provider")

    def _complete_openai(self, system_prompt: str, user_prompt: str) -> str:
        if OpenAI is None or not self.openai_key:
            raise RuntimeError("OpenAI client not available")
        client = OpenAI(api_key=self.openai_key)
        resp = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""

    def _complete_ollama(self, system_prompt: str, user_prompt: str) -> str:
        # Use chat API for better instruction following
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        resp = requests.post(
            f"{self.ollama_host}/api/chat",
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        # Fallback for generate API shape
        return data.get("response", "")