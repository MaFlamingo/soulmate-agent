"""MatchingRule ORM model — hot-configurable matching rules."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MatchingRule(Base):
    __tablename__ = "matching_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)  # "hard_filter", "weight", "diversity"
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # {dimension, operator, value, ...}
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<MatchingRule(id={self.id}, name={self.name}, type={self.rule_type})>"
