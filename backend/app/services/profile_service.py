"""Profile Service — CRUD operations and versioning for user profiles."""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from app.models.profile import Profile, ProfileVersion
from app.models.user import User
from app.models.match import Match


class ProfileService:
    """Manages user profile CRUD, versioning, and GDPR data operations."""

    def __init__(self, db_factory):
        self.db_factory = db_factory

    def get_or_create_profile(self, user_id: int) -> Profile:
        """Get user's profile, creating a default one if it doesn't exist."""
        db = self.db_factory()
        try:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                user = db.query(User).filter(User.id == user_id).first()
                profile = Profile(
                    user_id=user_id,
                    static_attrs={
                        "city": user.city if user else "",
                        "age_range": user.age_range if user else "",
                        "gender": user.gender if user else "",
                    },
                    interests=[],
                    personality={"openness": 0.5, "extraversion": 0.5, "conscientiousness": 0.5},
                    social_need={},
                    preferences={},
                )
                db.add(profile)
                db.commit()
                db.refresh(profile)
            return profile
        finally:
            db.close()

    def get_profile(self, user_id: int) -> dict | None:
        """Get full profile for a user."""
        db = self.db_factory()
        try:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                return None

            # Identify low-confidence tags
            low_conf = [
                i for i in (profile.interests or [])
                if i.get("confidence", 0) < 0.5
            ]

            return {
                "user_id": profile.user_id,
                "version": profile.version,
                "static_attrs": profile.static_attrs,
                "interests": profile.interests,
                "personality": profile.personality,
                "social_need": profile.social_need,
                "preferences": profile.preferences,
                "low_confidence_tags": low_conf,
                "conversation_summary": profile.conversation_summary,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }
        finally:
            db.close()

    def get_versions(self, user_id: int) -> list[dict]:
        """Get profile version history."""
        db = self.db_factory()
        try:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                return []
            versions = (
                db.query(ProfileVersion)
                .filter(ProfileVersion.profile_id == profile.id)
                .order_by(ProfileVersion.version.desc())
                .all()
            )
            return [
                {
                    "version": v.version,
                    "snapshot": v.snapshot,
                    "change_reason": v.change_reason,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ]
        finally:
            db.close()

    def get_version(self, user_id: int, version: int) -> dict | None:
        """Get a specific profile version snapshot."""
        db = self.db_factory()
        try:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                return None
            pv = (
                db.query(ProfileVersion)
                .filter(
                    ProfileVersion.profile_id == profile.id,
                    ProfileVersion.version == version,
                )
                .first()
            )
            if not pv:
                return None
            return {
                "version": pv.version,
                "snapshot": pv.snapshot,
                "change_reason": pv.change_reason,
                "created_at": pv.created_at.isoformat() if pv.created_at else None,
            }
        finally:
            db.close()

    def export_profile(self, user_id: int) -> dict | None:
        """GDPR-compliant full data export."""
        db = self.db_factory()
        try:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                return None

            # Get match history
            matches = (
                db.query(Match)
                .filter(Match.user_id == user_id)
                .order_by(Match.created_at.desc())
                .all()
            )

            match_history = []
            for m in matches:
                cand = db.query(User).filter(User.id == m.candidate_id).first()
                match_history.append({
                    "match_id": m.id,
                    "candidate_name": cand.username if cand else "unknown",
                    "total_score": m.total_score,
                    "score_breakdown": m.score_breakdown,
                    "rank": m.rank,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })

            versions = self.get_versions(user_id)
            profile_data = self.get_profile(user_id)

            return {
                "user_id": user_id,
                "exported_at": datetime.utcnow().isoformat(),
                "profile": profile_data,
                "versions": versions,
                "match_history": match_history,
            }
        finally:
            db.close()

    def delete_profile(self, user_id: int) -> dict:
        """GDPR delete: mark user inactive and remove profile data."""
        db = self.db_factory()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = False

            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            version_count = 0
            if profile:
                version_count = (
                    db.query(ProfileVersion)
                    .filter(ProfileVersion.profile_id == profile.id)
                    .count()
                )
                # Delete versions first
                db.query(ProfileVersion).filter(
                    ProfileVersion.profile_id == profile.id
                ).delete()
                # Clear profile data
                profile.interests = []
                profile.personality = {"openness": 0.5, "extraversion": 0.5, "conscientiousness": 0.5}
                profile.social_need = {}
                profile.preferences = {}
                profile.conversation_summary = None

            db.commit()

            # Also remove from vector store
            try:
                from app.core.vector_store import delete_profile_embedding
                delete_profile_embedding(user_id)
            except Exception as e:
                logger.warning(f"Failed to delete vector for user {user_id}: {e}")

            return {
                "message": "Profile data deleted successfully",
                "user_id": user_id,
                "deleted_versions": version_count,
            }
        finally:
            db.close()
