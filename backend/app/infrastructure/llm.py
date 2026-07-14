from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import httpx
from structlog import get_logger

logger = get_logger()


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...


class GroqProvider(LLMProvider):
    BASE = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(base_url=self.BASE, timeout=60.0) as client:
            resp = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Groq does not provide embeddings")


class OpenAIProvider(LLMProvider):
    BASE = "https://api.openai.com/v1"

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(base_url=self.BASE, timeout=60.0) as client:
            resp = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(base_url=self.BASE, timeout=30.0) as client:
            resp = await client.post(
                "/embeddings",
                json={"model": "text-embedding-3-small", "input": text},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]


class AnthropicProvider(LLMProvider):
    BASE = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        body: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(base_url=self.BASE, timeout=60.0) as client:
            resp = await client.post(
                "/messages",
                json=body,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Anthropic does not provide embeddings")


class OpenRouterProvider(LLMProvider):
    BASE = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: str = "mistralai/mixtral-8x22b-instruct") -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(base_url=self.BASE, timeout=60.0) as client:
            resp = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://devpilot.local",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("OpenRouter embeddings not implemented")


def get_llm_provider() -> LLMProvider:
    from app.core.config import settings

    provider_map = {
        "groq": GroqProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "openrouter": OpenRouterProvider,
    }

    key_map = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    provider_name = settings.LLM_PROVIDER.lower()
    provider_cls = provider_map.get(provider_name)
    if not provider_cls:
        raise ValueError(f"Unknown LLM provider: {provider_name}")

    api_key = getattr(settings, key_map[provider_name], "")
    return provider_cls(api_key=api_key)
