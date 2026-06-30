"""Matching Service — orchestrates the full matching pipeline."""

from sqlalchemy.orm import Session
from loguru import logger

from app.models.match import Match, MatchFeedback, IceBreakMessage
from app.models.user import User
from app.models.profile import Profile
from app.agents.matching_decision import MatchingDecisionAgent
from app.agents.facilitation import FacilitationAgent
from app.agents.base import AgentRequest


class MatchingService:
    """Orchestrates the matching and facilitation flow."""

    def __init__(
        self,
        matching_agent: MatchingDecisionAgent,
        facilitation_agent: FacilitationAgent,
        db_factory,
    ):
        self.matching_agent = matching_agent
        self.facilitation_agent = facilitation_agent
        self.db_factory = db_factory

    async def request_match(self, user_id: int, k: int = 5, weights: dict | None = None) -> dict:
        """Execute a full matching run for a user."""
        db = self.db_factory()
        try:
            # Get user profile
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                return {"error": "Profile not found. Please complete a conversation first."}

            user_profile = profile.to_dict()
            # Merge static attrs
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user_profile["static_attrs"] = {
                    "city": user.city or "",
                    "age_range": user.age_range or "",
                    "gender": user.gender or "",
                }

            # Call MatchingDecisionAgent
            response = await self.matching_agent.process(AgentRequest(
                caller="matching_service",
                payload={
                    "action": "match",
                    "user_id": user_id,
                    "user_profile": user_profile,
                    "k": k,
                    "weights": weights,
                },
            ))

            if response.status == "error":
                return {"error": response.error}

            candidates = response.payload.get("candidates", [])

            # Persist matches to DB
            saved_matches = []
            for cand in candidates:
                match = Match(
                    user_id=user_id,
                    candidate_id=cand["candidate_id"],
                    total_score=cand.get("total_score", 0),
                    score_breakdown={
                        "interest_score": cand.get("interest_score", 0),
                        "personality_score": cand.get("personality_score", 0),
                        "social_score": cand.get("social_score", 0),
                        "breakdown": cand.get("breakdown", {}),
                    },
                    rank=cand.get("rank", 0),
                )
                db.add(match)
                db.flush()  # Get match.id

                saved_matches.append({
                    "match_id": match.id,
                    "candidate_id": cand["candidate_id"],
                    "candidate_name": cand.get("candidate_name", f"User_{cand['candidate_id']}"),
                    "total_score": cand.get("total_score", 0),
                    "rank": cand.get("rank", 0),
                    "shared_interests": cand.get("shared_interests", []),
                    "score_breakdown": {
                        "interest_score": cand.get("interest_score", 0),
                        "personality_score": cand.get("personality_score", 0),
                        "social_score": cand.get("social_score", 0),
                        "rule_bonus": 0.0,
                        "detail": cand.get("breakdown", {}),
                    },
                    "brief_reason": cand.get("brief_reason", ""),
                })

            db.commit()

            return {
                "request_id": saved_matches[0]["match_id"] if saved_matches else 0,
                "candidates": saved_matches,
                "total_candidates_searched": response.payload.get("total_searched", 0),
                "filters_applied": response.payload.get("filters_applied", []),
                "latency_ms": response.latency_ms,
            }
        finally:
            db.close()

    def get_results(self, user_id: int, limit: int = 20, offset: int = 0) -> dict:
        """Get match results for a user."""
        db = self.db_factory()
        try:
            query = db.query(Match).filter(Match.user_id == user_id)
            total = query.count()
            matches = (
                query.order_by(Match.rank.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            items = []
            for m in matches:
                cand = db.query(User).filter(User.id == m.candidate_id).first()
                feedback = (
                    db.query(MatchFeedback)
                    .filter(MatchFeedback.match_id == m.id)
                    .first()
                )
                items.append({
                    "match_id": m.id,
                    "candidate_name": (cand.display_name or cand.username) if cand else "unknown",
                    "total_score": m.total_score,
                    "rank": m.rank,
                    "accepted": feedback.accepted if feedback else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })

            return {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        finally:
            db.close()

    async def get_match_detail(self, match_id: int) -> dict | None:
        """Get detailed match info with explanation and icebreakers."""
        db = self.db_factory()
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match:
                return None

            user = db.query(User).filter(User.id == match.user_id).first()
            cand = db.query(User).filter(User.id == match.candidate_id).first()
            user_profile = db.query(Profile).filter(Profile.user_id == match.user_id).first()
            cand_profile = db.query(Profile).filter(Profile.candidate_id == match.candidate_id).first()

            # Get existing icebreakers
            icebreakers = (
                db.query(IceBreakMessage)
                .filter(IceBreakMessage.match_id == match_id)
                .all()
            )

            # Shared interests
            u_interests = {
                i.get("sub_category", i.get("category", ""))
                for i in (user_profile.interests if user_profile else [])
            }
            c_interests = {
                i.get("sub_category", i.get("category", ""))
                for i in (cand_profile.interests if cand_profile else [])
            }
            shared = list(u_interests & c_interests)

            # Generate explanation if not cached
            # We always generate on-demand for freshness
            up = user_profile.to_dict() if user_profile else {}
            cp = cand_profile.to_dict() if cand_profile else {}
            u_pers = up.get("personality", {})
            c_pers = cp.get("personality", {})

            explain_resp = await self.facilitation_agent.process(AgentRequest(
                caller="matching_service",
                payload={
                    "action": "explain",
                    "user_summary": f"兴趣{up.get('interests', [])}，性格开放性{u_pers.get('openness', 0.5)}外向性{u_pers.get('extraversion', 0.5)}",
                    "candidate_name": cand.display_name or cand.username if cand else "TA",
                    "candidate_summary": f"兴趣{cp.get('interests', [])}，性格开放性{c_pers.get('openness', 0.5)}外向性{c_pers.get('extraversion', 0.5)}",
                    "interest_score": match.score_breakdown.get("interest_score", 0),
                    "personality_score": match.score_breakdown.get("personality_score", 0),
                    "social_score": match.score_breakdown.get("social_score", 0),
                    "total_score": match.total_score,
                    "shared_interests": shared,
                    "user_openness": u_pers.get("openness", 0.5),
                    "user_extraversion": u_pers.get("extraversion", 0.5),
                    "user_conscientiousness": u_pers.get("conscientiousness", 0.5),
                    "cand_openness": c_pers.get("openness", 0.5),
                    "cand_extraversion": c_pers.get("extraversion", 0.5),
                    "cand_conscientiousness": c_pers.get("conscientiousness", 0.5),
                },
            ))

            # Complementary traits
            complementary = []
            if u_pers and c_pers:
                if abs(u_pers.get("extraversion", 0.5) + c_pers.get("extraversion", 0.5) - 1.0) < 0.3:
                    complementary.append("外向性互补")

            return {
                "match_id": match.id,
                "user_id": match.user_id,
                "candidate_id": match.candidate_id,
                "candidate_name": (cand.display_name or cand.username) if cand else "unknown",
                "total_score": match.total_score,
                "rank": match.rank,
                "score_breakdown": match.score_breakdown,
                "explanation": explain_resp.payload.get("explanation", ""),
                "shared_interests": shared,
                "complementary_traits": complementary,
                "icebreakers": [
                    {
                        "id": ib.id,
                        "style": ib.style,
                        "content": ib.content,
                        "activity_suggestion": ib.activity_suggestion,
                        "selected": ib.selected,
                        "created_at": ib.created_at.isoformat() if ib.created_at else None,
                    }
                    for ib in icebreakers
                ],
                "created_at": match.created_at.isoformat() if match.created_at else None,
            }
        finally:
            db.close()

    def submit_feedback(self, match_id: int, accepted: bool | None, feedback_text: str | None = None) -> dict:
        """Submit user feedback on a match."""
        db = self.db_factory()
        try:
            fb = db.query(MatchFeedback).filter(MatchFeedback.match_id == match_id).first()
            if fb:
                fb.accepted = accepted
                fb.feedback_text = feedback_text
            else:
                fb = MatchFeedback(
                    match_id=match_id,
                    accepted=accepted,
                    feedback_text=feedback_text,
                )
                db.add(fb)
            db.commit()
            return {"match_id": match_id, "accepted": accepted}
        finally:
            db.close()

    async def generate_icebreakers(self, match_id: int) -> dict:
        """Generate and persist icebreaker messages for a match."""
        db = self.db_factory()
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match:
                return {"error": "Match not found"}

            # Check if already generated
            existing = (
                db.query(IceBreakMessage)
                .filter(IceBreakMessage.match_id == match_id)
                .count()
            )
            if existing >= 3:
                icebreakers = (
                    db.query(IceBreakMessage)
                    .filter(IceBreakMessage.match_id == match_id)
                    .all()
                )
                return {
                    "match_id": match_id,
                    "icebreakers": [
                        {
                            "id": ib.id,
                            "style": ib.style,
                            "content": ib.content,
                            "activity_suggestion": ib.activity_suggestion,
                            "selected": ib.selected,
                            "created_at": ib.created_at.isoformat() if ib.created_at else None,
                        }
                        for ib in icebreakers
                    ],
                }

            # Get profiles for both users
            u_profile = db.query(Profile).filter(Profile.user_id == match.user_id).first()
            c_profile = db.query(Profile).filter(Profile.user_id == match.candidate_id).first()
            u_user = db.query(User).filter(User.id == match.user_id).first()
            c_user = db.query(User).filter(User.id == match.candidate_id).first()

            up = u_profile.to_dict() if u_profile else {}
            cp = c_profile.to_dict() if c_profile else {}
            u_pers = up.get("personality", {})
            c_pers = cp.get("personality", {})
            u_sn = up.get("social_need", {})
            c_sn = cp.get("social_need", {})

            # Shared interests text
            u_ints = {i.get("sub_category", "") for i in up.get("interests", [])}
            c_ints = {i.get("sub_category", "") for i in cp.get("interests", [])}
            shared = u_ints & c_ints

            # Call FacilitationAgent for icebreakers
            response = await self.facilitation_agent.process(AgentRequest(
                caller="matching_service",
                payload={
                    "action": "icebreaker",
                    "user_interests": ", ".join(u_ints),
                    "user_openness": u_pers.get("openness", 0.5),
                    "user_extraversion": u_pers.get("extraversion", 0.5),
                    "user_conscientiousness": u_pers.get("conscientiousness", 0.5),
                    "user_social_need": u_sn,
                    "user_city": u_user.city if u_user else "",
                    "user_age_range": u_user.age_range if u_user else "",
                    "candidate_interests": ", ".join(c_ints),
                    "candidate_openness": c_pers.get("openness", 0.5),
                    "candidate_extraversion": c_pers.get("extraversion", 0.5),
                    "candidate_conscientiousness": c_pers.get("conscientiousness", 0.5),
                    "candidate_social_need": c_sn,
                    "candidate_city": c_user.city if c_user else "",
                    "candidate_age_range": c_user.age_range if c_user else "",
                    "shared_interests": ", ".join(shared) if shared else "暂无共同兴趣",
                    "personality_compatibility": f"用户开放性{u_pers.get('openness',0.5)},外向性{u_pers.get('extraversion',0.5)}; 候选人开放性{c_pers.get('openness',0.5)},外向性{c_pers.get('extraversion',0.5)}",
                    "total_score": match.total_score,
                },
            ))

            # Persist icebreakers
            new_icebreakers = []
            for ib_data in response.payload.get("icebreakers", []):
                ib = IceBreakMessage(
                    match_id=match_id,
                    style=ib_data.get("style", "warm"),
                    content=ib_data.get("message", ""),
                    activity_suggestion=ib_data.get("activity_suggestion", ""),
                )
                db.add(ib)
                db.flush()
                new_icebreakers.append({
                    "id": ib.id,
                    "style": ib.style,
                    "content": ib.content,
                    "activity_suggestion": ib.activity_suggestion,
                    "selected": ib.selected,
                    "created_at": ib.created_at.isoformat() if ib.created_at else None,
                })

            db.commit()

            return {
                "match_id": match_id,
                "icebreakers": new_icebreakers,
                "explanation": "",  # Explanation is separate
            }
        finally:
            db.close()

    def get_icebreakers(self, match_id: int) -> list[dict]:
        """Get all icebreakers for a match."""
        db = self.db_factory()
        try:
            ibs = (
                db.query(IceBreakMessage)
                .filter(IceBreakMessage.match_id == match_id)
                .all()
            )
            return [
                {
                    "id": ib.id,
                    "style": ib.style,
                    "content": ib.content,
                    "activity_suggestion": ib.activity_suggestion,
                    "selected": ib.selected,
                    "created_at": ib.created_at.isoformat() if ib.created_at else None,
                }
                for ib in ibs
            ]
        finally:
            db.close()
