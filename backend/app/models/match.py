"""Match, MatchFeedback and IceBreakMessage ORM models."""

from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)  # {interest_score, personality_score, social_score}
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)  # Whether icebreaker was sent
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="matches_as_user")
    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="matches_as_candidate")
    feedback = relationship("MatchFeedback", back_populates="match", uselist=False, cascade="all, delete-orphan")
    icebreakers = relationship("IceBreakMessage", back_populates="match", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, u{self.user_id}↔u{self.candidate_id}, score={self.total_score})>"


class MatchFeedback(Base):
    __tablename__ = "match_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True, nullable=False)
    accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # True/False/None
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    match = relationship("Match", back_populates="feedback")


class IceBreakMessage(Base):
    __tablename__ = "icebreak_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    style: Mapped[str] = mapped_column(String(16), nullable=False)  # "humorous", "formal", "warm"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    activity_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    match = relationship("Match", back_populates="icebreakers")
