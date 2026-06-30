"""Model-agnostic LLM adapter supporting OpenAI-compatible APIs and Ollama."""

import time
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from loguru import logger


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    api_key: str = ""
    base_url: str | None = None
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 30


class LLMResponse(BaseModel):
    content: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""


class BaseLLMAdapter(ABC):
    """Abstract adapter — swap implementations without changing agent code."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for one or more texts."""
        ...


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI and OpenAI-compatible APIs (DeepSeek, Qwen, etc.)."""

    def __init__(self, config: LLMConfig):
        from openai import AsyncOpenAI

        self.config = config
        kwargs = {"api_key": config.api_key, "timeout": config.timeout_seconds}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self.client = AsyncOpenAI(**kwargs)
        logger.info(f"OpenAIAdapter initialized: model={config.model}, base_url={config.base_url}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
    ) -> LLMResponse:
        start = time.time()
        kwargs: dict = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = await self.client.chat.completions.create(**kwargs)
        elapsed = (time.time() - start) * 1000

        choice = resp.choices[0]
        content = choice.message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0

        logger.debug(f"LLM chat: {len(messages)} msgs, {tokens} tokens, {elapsed:.0f}ms")
        return LLMResponse(content=content, tokens_used=tokens, latency_ms=elapsed, model=self.config.model)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self.client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [d.embedding for d in resp.data]


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for locally-deployed Ollama models."""

    def __init__(self, config: LLMConfig):
        from openai import AsyncOpenAI

        self.config = config
        base = config.base_url or "http://localhost:11434/v1"
        self.client = AsyncOpenAI(base_url=base, api_key="ollama", timeout=config.timeout_seconds)
        logger.info(f"OllamaAdapter initialized: model={config.model}, base_url={base}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
    ) -> LLMResponse:
        start = time.time()
        kwargs: dict = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        # Ollama may not support response_format; pass as best-effort
        if response_format:
            kwargs["response_format"] = response_format
        try:
            resp = await self.client.chat.completions.create(**kwargs)
        except Exception:
            # Fallback: remove response_format for Ollama
            kwargs.pop("response_format", None)
            resp = await self.client.chat.completions.create(**kwargs)

        elapsed = (time.time() - start) * 1000
        choice = resp.choices[0]
        content = choice.message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        return LLMResponse(content=content, tokens_used=tokens, latency_ms=elapsed, model=self.config.model)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self.client.embeddings.create(model=self.config.model, input=texts)
        return [d.embedding for d in resp.data]


class LLMAdapterFactory:
    """Factory: return the correct adapter based on provider."""

    @staticmethod
    def create(config: LLMConfig) -> BaseLLMAdapter:
        match config.provider:
            case LLMProvider.OPENAI:
                return OpenAIAdapter(config)
            case LLMProvider.OLLAMA:
                return OllamaAdapter(config)
            case _:
                raise ValueError(f"Unsupported LLM provider: {config.provider}")


def get_llm_config_from_settings() -> LLMConfig:
    """Build LLMConfig from app settings."""
    from app.config import settings

    return LLMConfig(
        provider=LLMProvider(settings.llm_provider),
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url if settings.llm_base_url else None,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout_seconds=settings.llm_timeout,
    )
