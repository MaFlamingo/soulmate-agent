"""Facilitation Agent — icebreaker generation + match explanation + activity suggestions.

FR-FA-01: Personalized icebreaker generation (3 styles)
FR-FA-02: Match explanation generation
FR-FA-03: Post-match activity suggestions
"""

import json
from loguru import logger

from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.prompts.icebreaker import ICEBREAKER_SYSTEM, ICEBREAKER_USER
from app.prompts.match_explanation import MATCH_EXPLANATION_SYSTEM, MATCH_EXPLANATION_USER
from app.prompts.activity_suggestion import ACTIVITY_SUGGESTION_SYSTEM, ACTIVITY_SUGGESTION_USER


class FacilitationAgent(BaseAgent):
    """Agent for post-match facilitation: icebreakers, explanations, activity suggestions."""

    agent_name = "facilitation"

    def __init__(self, llm_adapter):
        self.llm = llm_adapter

    async def process(self, request: AgentRequest) -> AgentResponse:
        return await self._timed_process(request, self._handle)

    async def _handle(self, request: AgentRequest) -> AgentResponse:
        action = request.payload.get("action", "explain")

        match action:
            case "explain":
                return await self._handle_explain(request)
            case "icebreaker":
                return await self._handle_icebreaker(request)
            case "activities":
                return await self._handle_activities(request)
            case "full_facilitation":
                return await self._handle_full(request)
            case _:
                return AgentResponse(
                    request_id=request.request_id,
                    status="error",
                    error=f"Unknown action: {action}",
                )

    async def _handle_explain(self, request: AgentRequest) -> AgentResponse:
        """Generate match explanation (FR-FA-02)."""
        user_summary = request.payload.get("user_summary", "")
        candidate_name = request.payload.get("candidate_name", "TA")
        candidate_summary = request.payload.get("candidate_summary", "")
        interest_score = request.payload.get("interest_score", 0)
        personality_score = request.payload.get("personality_score", 0)
        social_score = request.payload.get("social_score", 0)
        total_score = request.payload.get("total_score", 0)
        shared_interests = request.payload.get("shared_interests", [])
        user_openness = request.payload.get("user_openness", 0.5)
        user_extraversion = request.payload.get("user_extraversion", 0.5)
        user_conscientiousness = request.payload.get("user_conscientiousness", 0.5)
        cand_openness = request.payload.get("cand_openness", 0.5)
        cand_extraversion = request.payload.get("cand_extraversion", 0.5)
        cand_conscientiousness = request.payload.get("cand_conscientiousness", 0.5)

        prompt = MATCH_EXPLANATION_SYSTEM
        user_msg = MATCH_EXPLANATION_USER.format(
            user_summary=user_summary,
            candidate_name=candidate_name,
            candidate_summary=candidate_summary,
            interest_score=interest_score,
            personality_score=personality_score,
            social_score=social_score,
            total_score=total_score,
            shared_interests=", ".join(shared_interests) if shared_interests else "暂无",
            user_openness=user_openness,
            user_extraversion=user_extraversion,
            user_conscientiousness=user_conscientiousness,
            cand_openness=cand_openness,
            cand_extraversion=cand_extraversion,
            cand_conscientiousness=cand_conscientiousness,
        )

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
                "explanation": data.get("explanation", ""),
                "key_points": data.get("key_points", []),
                "confidence_note": data.get("confidence_note", ""),
            },
            tokens_used=response.tokens_used,
        )

    async def _handle_icebreaker(self, request: AgentRequest) -> AgentResponse:
        """Generate icebreaker messages (FR-FA-01)."""
        # Build the prompt variables from payload
        user_msg = ICEBREAKER_USER.format(
            user_interests=request.payload.get("user_interests", ""),
            user_openness=request.payload.get("user_openness", 0.5),
            user_extraversion=request.payload.get("user_extraversion", 0.5),
            user_conscientiousness=request.payload.get("user_conscientiousness", 0.5),
            user_social_need=json.dumps(request.payload.get("user_social_need", {}), ensure_ascii=False),
            user_city=request.payload.get("user_city", ""),
            user_age_range=request.payload.get("user_age_range", ""),
            candidate_interests=request.payload.get("candidate_interests", ""),
            candidate_openness=request.payload.get("candidate_openness", 0.5),
            candidate_extraversion=request.payload.get("candidate_extraversion", 0.5),
            candidate_conscientiousness=request.payload.get("candidate_conscientiousness", 0.5),
            candidate_social_need=json.dumps(request.payload.get("candidate_social_need", {}), ensure_ascii=False),
            candidate_city=request.payload.get("candidate_city", ""),
            candidate_age_range=request.payload.get("candidate_age_range", ""),
            shared_interests=request.payload.get("shared_interests", ""),
            personality_compatibility=request.payload.get("personality_compatibility", ""),
            total_score=request.payload.get("total_score", 0),
        )

        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": ICEBREAKER_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )
        data = self._parse_json_response(response.content)

        styles_data = data.get("styles", [])
        return AgentResponse(
            request_id=request.request_id,
            payload={
                "icebreakers": styles_data,
                "shared_highlights": data.get("shared_highlights", []),
                "complementarity_notes": data.get("complementarity_notes", ""),
            },
            tokens_used=response.tokens_used,
        )

    async def _handle_activities(self, request: AgentRequest) -> AgentResponse:
        """Generate activity suggestions (FR-FA-03)."""
        prompt = ACTIVITY_SUGGESTION_SYSTEM
        user_msg = ACTIVITY_SUGGESTION_USER.format(
            user_interests=request.payload.get("user_interests", ""),
            user_city=request.payload.get("user_city", ""),
            user_schedule=request.payload.get("user_schedule", ""),
            candidate_interests=request.payload.get("candidate_interests", ""),
            candidate_city=request.payload.get("candidate_city", ""),
            candidate_schedule=request.payload.get("candidate_schedule", ""),
            shared_interests=request.payload.get("shared_interests", ""),
            same_city=request.payload.get("same_city", "未知"),
        )

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
                "activities": data.get("activities", []),
                "general_tip": data.get("general_tip", ""),
            },
            tokens_used=response.tokens_used,
        )

    async def _handle_full(self, request: AgentRequest) -> AgentResponse:
        """Generate all facilitation content at once (explanation + icebreakers + activities)."""
        # Run all three in sequence
        explain_result = await self._handle_explain(request)
        icebreaker_result = await self._handle_icebreaker(request)
        activities_result = await self._handle_activities(request)

        total_tokens = (
            explain_result.tokens_used
            + icebreaker_result.tokens_used
            + activities_result.tokens_used
        )

        return AgentResponse(
            request_id=request.request_id,
            payload={
                "explanation": explain_result.payload.get("explanation", ""),
                "key_points": explain_result.payload.get("key_points", []),
                "icebreakers": icebreaker_result.payload.get("icebreakers", []),
                "shared_highlights": icebreaker_result.payload.get("shared_highlights", []),
                "activities": activities_result.payload.get("activities", []),
                "general_tip": activities_result.payload.get("general_tip", ""),
            },
            tokens_used=total_tokens,
        )
