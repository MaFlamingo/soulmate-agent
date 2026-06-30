"""Test fixtures: mock LLM, test database, test client."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class MockLLMResponse:
    """Mock LLM response for testing."""
    def __init__(self, content: str, tokens_used: int = 10, latency_ms: float = 100.0):
        self.content = content
        self.tokens_used = tokens_used
        self.latency_ms = latency_ms
        self.model = "mock-model"


class MockLLMAdapter:
    """Mock LLM adapter that returns predetermined responses."""

    def __init__(self, responses: dict | None = None):
        self.responses = responses or {}
        self.chat_calls = []
        self.embed_calls = []

    async def chat(self, messages, response_format=None):
        self.chat_calls.append({"messages": messages, "response_format": response_format})
        # Return a response matching the first message content
        key = messages[-1]["content"] if messages else ""
        content = self.responses.get("default", '{"reply": "Mock reply", "new_phase": "interest_gathering"}')
        return MockLLMResponse(content)

    async def embed(self, texts):
        self.embed_calls.append(texts)
        # Return dummy embeddings (1536 dims)
        return [[0.1] * 1536 for _ in texts]


# Mock profile extraction responses
MOCK_EXTRACTION_RESPONSE = """
{
  "extractions": [
    {
      "type": "interest",
      "category": "outdoor",
      "sub_category": "hiking",
      "weight": 0.9,
      "confidence": 0.85,
      "source_quote": "周末爱去山里吸氧",
      "tentative": false,
      "conflict": false
    }
  ],
  "conversation_phase_suggestion": "interest_deepening",
  "next_question_hint": "可以问问喜欢野山还是景区",
  "profile_completeness_estimate": 0.3
}
"""

MOCK_CONVERSATION_RESPONSE = """
{
  "reply": "山里空气确实好！你一般喜欢什么样的山？野山还是开发好的景区？",
  "new_phase": "interest_deepening",
  "phase_transition_reason": "已经了解到用户喜欢徒步，深入询问偏好",
  "questions_asked_in_reply": ["喜欢野山还是景区？", "一般一个人去还是结伴？"],
  "should_suggest_matching": false,
  "matching_readiness": 0.3
}
"""

MOCK_PERSONALITY_RESPONSE = """
{
  "openness": 0.75,
  "openness_confidence": 0.7,
  "openness_signals": ["使用丰富形容词"],
  "extraversion": 0.4,
  "extraversion_confidence": 0.65,
  "extraversion_signals": ["回复简洁"],
  "conscientiousness": 0.6,
  "conscientiousness_confidence": 0.5,
  "conscientiousness_signals": ["提及固定时间"],
  "summary": "测试用户画像摘要"
}
"""

MOCK_ICEBREAKER_RESPONSE = """
{
  "styles": [
    {
      "style": "humorous",
      "message": "幽默破冰话术",
      "opening_line": "幽默开场白",
      "activity_suggestion": "一起去徒步吧！"
    },
    {
      "style": "formal",
      "message": "正式破冰话术",
      "opening_line": "正式开场白",
      "activity_suggestion": "可以约个咖啡交流"
    },
    {
      "style": "warm",
      "message": "温暖破冰话术",
      "opening_line": "温暖开场白",
      "activity_suggestion": "周末一起去森林公园"
    }
  ],
  "shared_highlights": ["都爱徒步", "都喜欢咖啡"],
  "complementarity_notes": "性格互补"
}
"""

MOCK_EXPLANATION_RESPONSE = """
{
  "explanation": "你们都是户外运动爱好者，兴趣高度相似。",
  "key_points": ["共同兴趣: hiking", "同在上海"],
  "confidence_note": "画像置信度较高",
  "readability_score_estimate": 4.8
}
"""

MOCK_ACTIVITY_RESPONSE = """
{
  "activities": [
    {
      "title": "周末森林公园徒步",
      "type": "offline",
      "description": "一起去XX森林公园徒步",
      "difficulty": "easy",
      "estimated_duration": "2-3小时",
      "why_suitable": "共同兴趣"
    }
  ],
  "general_tip": "首次见面建议选择公共场合"
}
"""


@pytest.fixture
def mock_llm():
    """Create a mock LLM adapter for testing."""
    return MockLLMAdapter()


@pytest.fixture
def mock_llm_with_extraction():
    """Mock LLM that returns realistic extraction responses."""
    return MockLLMAdapter(responses={
        "default": MOCK_EXTRACTION_RESPONSE,
    })
