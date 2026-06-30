"""Profile Pydantic schemas."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class InterestItem(BaseModel):
    category: str
    sub_category: str
    weight: float = 0.5
    confidence: float = 0.5
    source: str = "dialogue"  # "dialogue", "explicit", "inferred"


class PersonalityScores(BaseModel):
    openness: float = 0.5
    extraversion: float = 0.5
    conscientiousness: float = 0.5


class SocialNeed(BaseModel):
    buddy_type: Optional[str] = None  # "workout_partner", "study_buddy", "travel_mate", etc.
    schedule: Optional[str] = None  # "weekends", "weekday_evenings", "flexible"
    ideal_group_size: Optional[str] = None  # "1on1", "small_group", "any"


class ProfilePreferences(BaseModel):
    hard_constraints: list[dict] = Field(default_factory=list)  # [{dimension, operator, value}]
    soft_preferences: dict = Field(default_factory=dict)  # {preferred_age_range, preferred_gender, ...}


class ProfileResponse(BaseModel):
    """Current user profile."""
    user_id: int
    version: int
    static_attrs: dict = Field(default_factory=dict)
    interests: list[InterestItem] = Field(default_factory=list)
    personality: PersonalityScores = Field(default_factory=PersonalityScores)
    social_need: SocialNeed = Field(default_factory=SocialNeed)
    preferences: ProfilePreferences = Field(default_factory=ProfilePreferences)
    low_confidence_tags: list[dict] = Field(default_factory=list)  # Tags marked "tentative"
    conversation_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileVersionResponse(BaseModel):
    """A single profile version snapshot."""
    version: int
    snapshot: dict
    change_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileExportResponse(BaseModel):
    """GDPR-compliant data export."""
    user_id: int
    exported_at: str
    profile: ProfileResponse
    versions: list[ProfileVersionResponse]
    match_history: list[dict] = Field(default_factory=list)


class ProfileDeleteResponse(BaseModel):
    """Response after profile deletion."""
    message: str
    user_id: int
    deleted_versions: int
