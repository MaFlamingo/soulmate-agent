"""Admin API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from app.schemas.admin import (
    RuleCreateRequest, RuleUpdateRequest,
)
from app.services.admin_service import AdminService


router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_service(request: Request) -> AdminService:
    return request.app.state.admin_service


# --- Dashboard ---

@router.get("/dashboard")
async def get_dashboard(
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get admin dashboard with agent metrics and system info."""
    return admin_service.get_dashboard()


# --- Matching Rules ---

@router.get("/rules")
async def list_rules(
    admin_service: AdminService = Depends(get_admin_service),
):
    """List all matching rules."""
    return admin_service.list_rules()


@router.post("/rules")
async def create_rule(
    body: RuleCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Create a new matching rule (hot-config)."""
    return admin_service.create_rule(body.model_dump())


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    body: RuleUpdateRequest,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Update a matching rule (hot-config)."""
    result = admin_service.update_rule(rule_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Delete a matching rule."""
    success = admin_service.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": f"Rule {rule_id} deleted"}


# --- Audit Logs ---

@router.get("/audit-logs")
async def list_audit_logs(
    user_id: int | None = None,
    action: str | None = None,
    page: int = 1,
    limit: int = 50,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Query audit logs."""
    return admin_service.list_audit_logs(
        user_id=user_id, action=action, page=page, limit=limit,
    )


# --- User Management ---

@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 50,
    admin_service: AdminService = Depends(get_admin_service),
):
    """List all users."""
    return admin_service.list_users(page=page, limit=limit)


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: int,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Deactivate a user."""
    success = admin_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user_id} deactivated"}


# --- Vector Store ---

@router.post("/reset-vector-store")
async def reset_vector_store(
    admin_service: AdminService = Depends(get_admin_service),
):
    """Rebuild all embeddings (admin operation)."""
    from app.core.vector_store import reset_collection
    reset_collection()
    return {"message": "Vector store collection reset"}
