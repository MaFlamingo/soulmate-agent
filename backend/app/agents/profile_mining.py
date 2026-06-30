"""Profile Mining Agent — multi-turn conversation + implicit profile extraction.

FR-PM-01: Multi-turn conversation management with state machine
FR-PM-02: Implicit preference extraction from natural language
FR-PM-03: Personality trait analysis from conversation style
FR-PM-04: Dynamic profile construction with version history
"""

import json
from typing import Any
from loguru import logger

from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.prompts.conversation_manager import CONVERSATION_MANAGER_SYSTEM, CONVERSATION_MANAGER_USER
from app.prompts.profile_extraction import PROFILE_EXTRACTION_SYSTEM, PROFILE_EXTRACTION_USER
from app.prompts.personality_analysis import PERSONALITY_ANALYSIS_SYSTEM, PERSONALITY_ANALYSIS_USER

# Conversation phases
PHASES = [
    "greeting",
    "interest_gathering",
    "interest_deepening",
    "personality_probing",
    "social_need_clarification",
    "confirmation_loop",
    "ready_to_match",
]

# Minimum messages before personality analysis is meaningful
MIN_MESSAGES_FOR_PERSONALITY = 4


class ProfileMiningAgent(BaseAgent):
    """Agent that conducts multi-turn conversation and extracts user profiles.

    State machine phases:
        greeting → interest_gathering → interest_deepening →
        personality_probing → social_need_clarification →
        confirmation_loop → ready_to_match
    """

    agent_name = "profile_mining"

    def __init__(self, llm_adapter):
        self.llm = llm_adapter

    async def process(self, request: AgentRequest) -> AgentResponse:
        return await self._timed_process(request, self._handle)

    async def _handle(self, request: AgentRequest) -> AgentResponse:
        action = request.payload.get("action", "chat")

        match action:
            case "chat":
                return await self._handle_chat(request)
            case "analyze_personality":
                return await self._handle_personality_analysis(request)
            case "extract_only":
                return await self._handle_extraction_only(request)
            case _:
                return AgentResponse(
                    request_id=request.request_id,
                    status="error",
                    error=f"Unknown action: {action}",
                )

    async def _handle_chat(self, request: AgentRequest) -> AgentResponse:
        """Main chat handler: generate reply + extract profile info."""
        user_message = request.payload["user_message"]
        current_phase = request.payload.get("current_phase", "greeting")
        collected_info = request.payload.get("collected_info", {})
        conversation_context = request.payload.get("conversation_context", "")
        current_profile_json = request.payload.get("current_profile_json", "{}")

        # Step 1: Generate conversational reply
        conv_prompt = CONVERSATION_MANAGER_SYSTEM.format(
            current_phase=current_phase,
            collected_info=json.dumps(collected_info, ensure_ascii=False, indent=2),
        )
        conv_user = CONVERSATION_MANAGER_USER.format(
            user_message=user_message,
            current_phase=current_phase,
        )
        conv_response = await self.llm.chat(
            messages=[
                {"role": "system", "content": conv_prompt},
                {"role": "user", "content": conv_user},
            ],
        )
        conv_data = self._parse_json_response(conv_response.content)
        total_tokens = conv_response.tokens_used

        reply = conv_data.get("reply", "嗯，我了解了。让我再想想...")
        new_phase = conv_data.get("new_phase", current_phase)
        should_suggest_matching = conv_data.get("should_suggest_matching", False)
        matching_readiness = conv_data.get("matching_readiness", 0.0)

        # Step 2: Extract profile information from user message
        extract_prompt = PROFILE_EXTRACTION_SYSTEM
        extract_user = PROFILE_EXTRACTION_USER.format(
            current_profile_json=current_profile_json,
            conversation_context=conversation_context,
            user_message=user_message,
        )
        extract_response = await self.llm.chat(
            messages=[
                {"role": "system", "content": extract_prompt},
                {"role": "user", "content": extract_user},
            ],
        )
        extract_data = self._parse_json_response(extract_response.content)
        total_tokens += extract_response.tokens_used

        extractions = extract_data.get("extractions", [])
        phase_suggestion = extract_data.get("conversation_phase_suggestion", new_phase)
        next_hint = extract_data.get("next_question_hint", "")
        completeness = extract_data.get("profile_completeness_estimate", 0.0)

        # Use phase suggestion if it's more advanced than the conversation manager's
        if PHASES.index(phase_suggestion) > PHASES.index(new_phase):
            new_phase = phase_suggestion

        return AgentResponse(
            request_id=request.request_id,
            payload={
                "reply": reply,
                "new_phase": new_phase,
                "extractions": extractions,
                "next_question_hint": next_hint,
                "should_suggest_matching": should_suggest_matching or completeness >= 0.7,
                "matching_readiness": max(matching_readiness, completeness),
                "questions_asked": conv_data.get("questions_asked_in_reply", []),
            },
            tokens_used=total_tokens,
        )

    async def _handle_personality_analysis(self, request: AgentRequest) -> AgentResponse:
        """Standalone personality analysis from conversation text (FR-PM-03)."""
        conversation_text = request.payload.get("conversation_text", "")

        prompt = PERSONALITY_ANALYSIS_SYSTEM
        user_msg = PERSONALITY_ANALYSIS_USER.format(conversation_text=conversation_text)

        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
        )
        data = self._parse_json_response(response.content)

        return AgentResponse(
            request_id=request.request_id,
            payload={
                "personality": {
                    "openness": data.get("openness", 0.5),
                    "extraversion": data.get("extraversion", 0.5),
                    "conscientiousness": data.get("conscientiousness", 0.5),
                },
                "confidence": {
                    "openness": data.get("openness_confidence", 0.5),
                    "extraversion": data.get("extraversion_confidence", 0.5),
                    "conscientiousness": data.get("conscientiousness_confidence", 0.5),
                },
                "signals": {
                    "openness": data.get("openness_signals", []),
                    "extraversion": data.get("extraversion_signals", []),
                    "conscientiousness": data.get("conscientiousness_signals", []),
                },
                "summary": data.get("summary", ""),
            },
            tokens_used=response.tokens_used,
        )

    async def _handle_extraction_only(self, request: AgentRequest) -> AgentResponse:
        """Extract profile data without generating a reply (for batch processing)."""
        user_message = request.payload["user_message"]
        current_profile_json = request.payload.get("current_profile_json", "{}")
        conversation_context = request.payload.get("conversation_context", "")

        extract_prompt = PROFILE_EXTRACTION_SYSTEM
        extract_user = PROFILE_EXTRACTION_USER.format(
            current_profile_json=current_profile_json,
            conversation_context=conversation_context,
            user_message=user_message,
        )
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": extract_prompt},
                {"role": "user", "content": extract_user},
            ],
        )
        extract_data = self._parse_json_response(response.content)

        return AgentResponse(
            request_id=request.request_id,
            payload={
                "extractions": extract_data.get("extractions", []),
                "completeness": extract_data.get("profile_completeness_estimate", 0.0),
            },
            tokens_used=response.tokens_used,
        )

    def get_greeting(self) -> str:
        """Return the initial greeting message for a new conversation."""
        return "嗨！👋 我是你的社交搭子助手。想找个什么样的搭子呢？可以先跟我聊聊你的兴趣爱好，周末喜欢做什么～"
