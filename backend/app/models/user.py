"""User ORM model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    age_range: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # "18-24","25-30","31-40","40+"
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # "male","female","other","prefer_not"
    bio: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    matches_as_user = relationship("Match", foreign_keys="Match.user_id", back_populates="user", cascade="all, delete-orphan")
    matches_as_candidate = relationship("Match", foreign_keys="Match.candidate_id", back_populates="candidate")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
