"""Admin Service — monitoring, rule management, audit logs, user management."""

import time
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.models.user import User
from app.models.profile import Profile
from app.models.conversation import Conversation
from app.models.match import Match
from app.models.matching_rule import MatchingRule
from app.models.audit_log import AuditLog
from app.engine.rule_engine import get_rule_engine


# Application start time for uptime tracking
APP_START_TIME = time.time()


class AdminService:
    """Admin operations: dashboard, rules, audit, user management."""

    def __init__(self, db_factory):
        self.db_factory = db_factory

    def get_dashboard(self) -> dict:
        """Build admin dashboard with agent metrics and system info."""
        db = self.db_factory()
        try:
            # Aggregate counts
            total_users = db.query(func.count(User.id)).scalar()
            total_conversations = db.query(func.count(Conversation.id)).scalar()
            total_matches = db.query(func.count(Match.id)).scalar()
            total_rules = db.query(func.count(MatchingRule.id)).scalar()

            # Vector store stats
            from app.core.vector_store import get_collection_stats
            vs_stats = get_collection_stats()

            uptime = time.time() - APP_START_TIME

            return {
                "agents": [
                    {
                        "name": "ProfileMiningAgent",
                        "qps": 0.0,  # Would need metrics collector for real values
                        "latency_p95_ms": 0.0,
                        "success_rate": 100.0,
                        "tokens_consumed_today": 0,
                        "total_requests": 0,
                        "error_count": 0,
                    },
                    {
                        "name": "MatchingDecisionAgent",
                        "qps": 0.0,
                        "latency_p95_ms": 0.0,
                        "success_rate": 100.0,
                        "tokens_consumed_today": 0,
                        "total_requests": 0,
                        "error_count": 0,
                    },
                    {
                        "name": "FacilitationAgent",
                        "qps": 0.0,
                        "latency_p95_ms": 0.0,
                        "success_rate": 100.0,
                        "tokens_consumed_today": 0,
                        "total_requests": 0,
                        "error_count": 0,
                    },
                ],
                "system": {
                    "total_users": total_users,
                    "total_conversations": total_conversations,
                    "total_matches": total_matches,
                    "vector_store_count": vs_stats.get("count", 0),
                    "uptime_seconds": round(uptime, 0),
                },
            }
        finally:
            db.close()

    # --- Matching Rules ---

    def list_rules(self) -> list[dict]:
        """List all matching rules."""
        db = self.db_factory()
        try:
            rules = db.query(MatchingRule).order_by(MatchingRule.priority.asc()).all()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "rule_type": r.rule_type,
                    "config": r.config,
                    "priority": r.priority,
                    "enabled": r.enabled,
                    "description": r.description,
                    "updated_by": r.updated_by,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rules
            ]
        finally:
            db.close()

    def create_rule(self, data: dict) -> dict:
        """Create a new matching rule."""
        db = self.db_factory()
        try:
            rule = MatchingRule(
                name=data["name"],
                rule_type=data["rule_type"],
                config=data["config"],
                priority=data.get("priority", 0),
                enabled=data.get("enabled", True),
                description=data.get("description"),
                updated_by=data.get("updated_by", "admin"),
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)
            # Hot-reload rule engine
            self._reload_rules(db)
            return {
                "id": rule.id,
                "name": rule.name,
                "rule_type": rule.rule_type,
                "config": rule.config,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "description": rule.description,
                "updated_by": rule.updated_by,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
            }
        finally:
            db.close()

    def update_rule(self, rule_id: int, data: dict) -> dict | None:
        """Update an existing matching rule (hot-config)."""
        db = self.db_factory()
        try:
            rule = db.query(MatchingRule).filter(MatchingRule.id == rule_id).first()
            if not rule:
                return None

            if "enabled" in data:
                rule.enabled = data["enabled"]
            if "config" in data:
                rule.config = data["config"]
            if "priority" in data:
                rule.priority = data["priority"]
            if "description" in data:
                rule.description = data["description"]
            rule.updated_by = data.get("updated_by", "admin")

            db.commit()
            db.refresh(rule)
            # Hot-reload
            self._reload_rules(db)
            return {
                "id": rule.id,
                "name": rule.name,
                "rule_type": rule.rule_type,
                "config": rule.config,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "description": rule.description,
                "updated_by": rule.updated_by,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
            }
        finally:
            db.close()

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a matching rule."""
        db = self.db_factory()
        try:
            rule = db.query(MatchingRule).filter(MatchingRule.id == rule_id).first()
            if not rule:
                return False
            db.delete(rule)
            db.commit()
            self._reload_rules(db)
            return True
        finally:
            db.close()

    def _reload_rules(self, db: Session):
        """Hot-reload rules into the rule engine."""
        try:
            rules = db.query(MatchingRule).all()
            get_rule_engine().load_rules(rules)
        except Exception as e:
            logger.error(f"Failed to reload rules: {e}")

    # --- Audit Logs ---

    def list_audit_logs(
        self, user_id: int | None = None, action: str | None = None,
        page: int = 1, limit: int = 50,
    ) -> dict:
        """Query audit logs with filters."""
        db = self.db_factory()
        try:
            query = db.query(AuditLog)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)

            query = query.order_by(AuditLog.created_at.desc())
            total = query.count()
            logs = query.offset((page - 1) * limit).limit(limit).all()

            return {
                "items": [
                    {
                        "id": l.id,
                        "action": l.action,
                        "user_id": l.user_id,
                        "target_user_id": l.target_user_id,
                        "details": l.details,
                        "ip_address": l.ip_address,
                        "created_at": l.created_at.isoformat() if l.created_at else None,
                    }
                    for l in logs
                ],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0,
            }
        finally:
            db.close()

    def write_audit_log(
        self, action: str, user_id: int | None = None,
        target_user_id: int | None = None, details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Write an audit log entry (called by middleware/services)."""
        db = self.db_factory()
        try:
            log_entry = AuditLog(
                action=action,
                user_id=user_id,
                target_user_id=target_user_id,
                details=details or {},
                ip_address=ip_address,
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
        finally:
            db.close()

    # --- User Management ---

    def list_users(self, page: int = 1, limit: int = 50) -> dict:
        """List all users with profile completeness."""
        db = self.db_factory()
        try:
            query = db.query(User).order_by(User.created_at.desc())
            total = query.count()
            users = query.offset((page - 1) * limit).limit(limit).all()

            items = []
            for u in users:
                profile = db.query(Profile).filter(Profile.user_id == u.id).first()
                match_count = db.query(func.count(Match.id)).filter(Match.user_id == u.id).scalar()
                profile_complete = bool(
                    profile and profile.interests and len(profile.interests) >= 2
                )
                items.append({
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "city": u.city,
                    "is_active": u.is_active,
                    "profile_complete": profile_complete,
                    "match_count": match_count,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                })

            return {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0,
            }
        finally:
            db.close()

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user (soft delete)."""
        db = self.db_factory()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.is_active = False
            db.commit()
            return True
        finally:
            db.close()
