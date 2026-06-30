"""Audit logging middleware — records key API actions."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


# Actions that should be audited
AUDITABLE_ACTIONS = {
    ("POST", "/api/match/request"): "match_requested",
    ("GET", "/api/match/"): "match_viewed",  # prefix
    ("POST", "/api/match/"): "icebreaker_sent",  # prefix for /icebreaker
    ("POST", "/api/profile/me/export"): "profile_exported",
    ("DELETE", "/api/profile/me"): "profile_deleted",
    ("POST", "/api/chat/sessions"): "conversation_started",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that writes audit log entries for key actions."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Check if this action should be audited
        method = request.method
        path = request.url.path

        action = None
        for (m, p), a in AUDITABLE_ACTIONS.items():
            if method == m and path.startswith(p):
                action = a
                break

        if action and hasattr(request.app.state, "admin_service"):
            try:
                # Extract user_id from query params or body
                user_id = None
                target_user_id = None

                request.app.state.admin_service.write_audit_log(
                    action=action,
                    user_id=user_id,
                    target_user_id=target_user_id,
                    details={
                        "method": method,
                        "path": path,
                        "status_code": response.status_code,
                    },
                    ip_address=request.client.host if request.client else None,
                )
            except Exception as e:
                logger.warning(f"Audit log write failed: {e}")

        return response
