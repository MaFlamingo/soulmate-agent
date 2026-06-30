"""Profile and ProfileVersion ORM models."""

from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    static_attrs: Mapped[dict] = mapped_column(JSON, default=dict)  # {gender, city, age_range}
    interests: Mapped[list[dict]] = mapped_column(JSON, default=list)  # [{category, sub_category, weight, source, confidence}]
    personality: Mapped[dict] = mapped_column(JSON, default=dict)  # {openness, extraversion, conscientiousness, ...}
    social_need: Mapped[dict] = mapped_column(JSON, default=dict)  # {buddy_type, schedule, ideal_group_size}
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)  # {hard_constraints: [...], soft_preferences: {...}}
    embedding_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # ChromaDB doc ID
    conversation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")
    versions = relationship("ProfileVersion", back_populates="profile", cascade="all, delete-orphan", order_by="ProfileVersion.version")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for embedding / API serialization."""
        return {
            "static_attrs": self.static_attrs or {},
            "interests": self.interests or [],
            "personality": self.personality or {},
            "social_need": self.social_need or {},
            "preferences": self.preferences or {},
        }

    def create_snapshot(self) -> dict[str, Any]:
        """Create a full snapshot for versioning."""
        return {
            "static_attrs": self.static_attrs,
            "interests": self.interests,
            "personality": self.personality,
            "social_need": self.social_need,
            "preferences": self.preferences,
            "conversation_summary": self.conversation_summary,
        }


class ProfileVersion(Base):
    __tablename__ = "profile_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="versions")

    def __repr__(self) -> str:
        return f"<ProfileVersion(profile_id={self.profile_id}, v={self.version})>"
