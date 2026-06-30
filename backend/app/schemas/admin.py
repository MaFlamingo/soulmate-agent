"""Admin Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AgentMetrics(BaseModel):
    """Per-agent monitoring metrics."""
    name: str
    qps: float = 0.0
    latency_p95_ms: float = 0.0
    success_rate: float = 100.0
    tokens_consumed_today: int = 0
    total_requests: int = 0
    error_count: int = 0


class SystemInfo(BaseModel):
    """System-level info."""
    total_users: int = 0
    total_conversations: int = 0
    total_matches: int = 0
    vector_store_count: int = 0
    uptime_seconds: float = 0.0


class DashboardResponse(BaseModel):
    """Admin dashboard data."""
    agents: list[AgentMetrics]
    system: SystemInfo


class RuleCreateRequest(BaseModel):
    """Create a new matching rule."""
    name: str = Field(..., min_length=1, max_length=64)
    rule_type: str = Field(..., description="hard_filter | weight | diversity")
    config: dict = Field(..., description="Rule configuration")
    priority: int = 0
    enabled: bool = True
    description: Optional[str] = None


class RuleUpdateRequest(BaseModel):
    """Update an existing matching rule."""
    enabled: Optional[bool] = None
    config: Optional[dict] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class RuleResponse(BaseModel):
    """Matching rule response."""
    id: int
    name: str
    rule_type: str
    config: dict
    priority: int
    enabled: bool
    description: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Audit log entry."""
    id: int
    action: str
    user_id: Optional[int] = None
    target_user_id: Optional[int] = None
    details: dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserManagementResponse(BaseModel):
    """User management list item."""
    id: int
    username: str
    email: str
    city: Optional[str] = None
    is_active: bool
    profile_complete: bool = False
    match_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: list
    total: int
    page: int
    limit: int
    pages: int
