"""Match Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    """Trigger a matching run."""
    user_id: int
    k: int = Field(default=5, ge=1, le=20, description="Number of candidates to return")


class ScoreBreakdown(BaseModel):
    """Detailed score decomposition."""
    interest_score: float  # 0-50
    personality_score: float  # 0-30
    social_score: float  # 0-20
    rule_bonus: float = 0.0
    detail: dict = Field(default_factory=dict)


class MatchCandidate(BaseModel):
    """A single matching candidate in the result list."""
    match_id: int
    candidate_id: int
    candidate_name: str
    total_score: float  # 0-100
    rank: int
    shared_interests: list[str] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown
    brief_reason: str = ""


class MatchResultResponse(BaseModel):
    """Response after a matching run."""
    request_id: int
    candidates: list[MatchCandidate]
    total_candidates_searched: int
    filters_applied: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class MatchDetailResponse(BaseModel):
    """Detailed view of a single match."""
    match_id: int
    user_id: int
    candidate_id: int
    candidate_name: str
    total_score: float
    rank: int
    score_breakdown: ScoreBreakdown
    explanation: str = Field(..., description="Natural language explanation of the match")
    shared_interests: list[str] = Field(default_factory=list)
    complementary_traits: list[str] = Field(default_factory=list)
    icebreakers: list["IceBreakerResponse"] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchFeedbackRequest(BaseModel):
    """Submit feedback on a match."""
    accepted: Optional[bool] = None
    feedback_text: Optional[str] = Field(default=None, max_length=1024)


class IceBreakerRequest(BaseModel):
    """Request to generate icebreaker messages."""
    style: str = Field(default="warm", description="humorous | formal | warm")


class IceBreakerResponse(BaseModel):
    """A generated icebreaker message."""
    id: int
    style: str
    content: str
    activity_suggestion: Optional[str] = None
    selected: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class IceBreakerGenerateResponse(BaseModel):
    """All generated icebreaker styles."""
    match_id: int
    icebreakers: list[IceBreakerResponse]
    explanation: str = ""


class MatchHistoryItem(BaseModel):
    """Summary item for user's match history."""
    match_id: int
    candidate_name: str
    total_score: float
    rank: int
    accepted: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True
