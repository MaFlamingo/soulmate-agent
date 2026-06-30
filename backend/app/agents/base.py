"""BaseAgent — abstract base class for all three core agents."""

import time
from abc import ABC, abstractmethod
from uuid import uuid4
from typing import Any
from pydantic import BaseModel, Field
from loguru import logger


class AgentRequest(BaseModel):
    """Standard envelope for inter-agent calls. Enables tracing and future distribution."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    caller: str = "api"  # "profile_mining" | "matching_decision" | "facilitation" | "api"
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standard response envelope from any agent."""

    request_id: str
    status: str = "success"  # "success" | "error" | "degraded"
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class BaseAgent(ABC):
    """Abstract base for all agents. Each agent implements `process()`."""

    agent_name: str = "base"

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Handle an incoming request and return a response."""
        ...

    def build_request(self, payload: dict[str, Any], **metadata) -> AgentRequest:
        """Convenience: build a request to send to another agent."""
        return AgentRequest(
            request_id=str(uuid4()),
            caller=self.agent_name,
            payload=payload,
            metadata=metadata,
        )

    async def _timed_process(self, request: AgentRequest, handler) -> AgentResponse:
        """Wrap handler with timing and error handling."""
        start = time.time()
        try:
            result = await handler(request)
            elapsed = (time.time() - start) * 1000
            if isinstance(result, AgentResponse):
                result.latency_ms = elapsed
                return result
            return AgentResponse(
                request_id=request.request_id,
                payload=result if isinstance(result, dict) else {"data": result},
                latency_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"[{self.agent_name}] Error: {e}")
            return AgentResponse(
                request_id=request.request_id,
                status="error",
                error=str(e),
                latency_ms=elapsed,
            )

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Safely parse JSON from LLM response, handling markdown code blocks."""
        import json

        text = content.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            logger.warning(f"[{self.agent_name}] Failed to parse JSON from: {text[:200]}...")
            return {}
