"""Matching Decision Agent — vector similarity + rule engine + MMR ranking.

FR-MD-01: Profile vectorization and embedding
FR-MD-02: Weighted cosine similarity scoring
FR-MD-03: Rule engine hard-constraint filtering
FR-MD-04: Multi-objective ranking with diversity (MMR)
"""

from loguru import logger

from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.core.vector_store import similarity_search, get_profile_embedding, upsert_profile_embedding
from app.engine.scorer import compute_full_score
from app.engine.mmr import mmr_rerank
from app.engine.rule_engine import get_rule_engine


class MatchingDecisionAgent(BaseAgent):
    """Agent that performs matching: filter → score → diversify → rank."""

    agent_name = "matching_decision"

    def __init__(self, llm_adapter, embedding_client, db_session_factory):
        self.llm = llm_adapter
        self.embedding_client = embedding_client
        self.db_factory = db_session_factory

    async def process(self, request: AgentRequest) -> AgentResponse:
        return await self._timed_process(request, self._handle)

    async def _handle(self, request: AgentRequest) -> AgentResponse:
        action = request.payload.get("action", "match")

        match action:
            case "match":
                return await self._handle_match(request)
            case "update_embedding":
                return await self._handle_update_embedding(request)
            case _:
                return AgentResponse(
                    request_id=request.request_id,
                    status="error",
                    error=f"Unknown action: {action}",
                )

    async def _handle_match(self, request: AgentRequest) -> AgentResponse:
        """Execute full matching pipeline for a user."""
        user_id = request.payload["user_id"]
        user_profile = request.payload["user_profile"]  # dict with full profile
        k = request.payload.get("k", 5)
        weights = request.payload.get("weights", None)

        # Step 1: Get or generate user embedding
        user_vec = get_profile_embedding(user_id)
        if user_vec is None:
            # Generate on-the-fly
            profile_text = self.embedding_client.profile_to_text(user_profile)
            user_vec = await self.embedding_client.embed_single(profile_text)
            upsert_profile_embedding(user_id, user_vec,
                                     {"city": user_profile.get("static_attrs", {}).get("city", "")})

        # Step 2: Vector similarity search for initial candidate pool
        # Get more than k to allow for filtering and diversity
        search_results = similarity_search(
            query_embedding=user_vec,
            exclude_user_ids=[user_id],
            top_k=min(k * 10, 50),  # Fetch enough for filtering
        )

        candidate_ids = [r["user_id"] for r in search_results]
        logger.info(f"Vector search returned {len(candidate_ids)} candidates for user {user_id}")

        if not candidate_ids:
            return AgentResponse(
                request_id=request.request_id,
                payload={
                    "candidates": [],
                    "total_searched": 0,
                    "filters_applied": ["No candidates found in vector search"],
                },
            )

        # Step 3: Load candidate profiles from DB
        db = self.db_factory()
        try:
            from app.models.profile import Profile
            from app.models.user import User

            candidates = []
            for sr in search_results:
                cid = sr["user_id"]
                profile = db.query(Profile).filter(Profile.user_id == cid).first()
                user = db.query(User).filter(User.id == cid).first()
                if profile and user and user.is_active:
                    candidates.append({
                        "candidate_id": cid,
                        "candidate_name": user.display_name or user.username,
                        "profile_dict": profile.to_dict(),
                        "similarity": sr["similarity"],
                        "distance": sr["distance"],
                    })
        finally:
            db.close()

        total_before_filter = len(candidates)

        # Step 4: Apply hard-constraint rule engine
        rule_engine = get_rule_engine()
        candidates, filters_applied = rule_engine.filter_candidates(user_profile, candidates)

        logger.info(f"Rules filtered {total_before_filter} → {len(candidates)} candidates")

        # Step 5: Compute full multi-dimensional scores
        scored_candidates = []
        for cand in candidates:
            cand_vec = get_profile_embedding(cand["candidate_id"])
            score_result = compute_full_score(
                user_vec=user_vec,
                candidate_vec=cand_vec,
                user_profile=user_profile,
                candidate_profile=cand["profile_dict"],
                weights=weights,
            )
            cand.update(score_result)
            cand["embedding"] = cand_vec  # For MMR diversity
            scored_candidates.append(cand)

        # Step 6: MMR diversity re-ranking
        diverse_candidates = mmr_rerank(scored_candidates, lambda_=0.7, k=k)

        # Step 7: Extract shared interests for each candidate
        for cand in diverse_candidates:
            user_interests = {
                i.get("sub_category", i.get("category", ""))
                for i in user_profile.get("interests", [])
            }
            cand_interests = {
                i.get("sub_category", i.get("category", ""))
                for i in cand["profile_dict"].get("interests", [])
            }
            shared = user_interests & cand_interests
            cand["shared_interests"] = list(shared)
            cand["brief_reason"] = self._generate_brief_reason(
                cand, list(shared), user_profile
            )

        return AgentResponse(
            request_id=request.request_id,
            payload={
                "candidates": diverse_candidates,
                "total_searched": total_before_filter,
                "filters_applied": filters_applied,
            },
        )

    async def _handle_update_embedding(self, request: AgentRequest) -> AgentResponse:
        """Update a user's embedding vector after profile change."""
        user_id = request.payload["user_id"]
        profile_text = request.payload.get("profile_text", "")

        if not profile_text:
            profile_dict = request.payload.get("profile_dict", {})
            profile_text = self.embedding_client.profile_to_text(profile_dict)

        embedding = await self.embedding_client.embed_single(profile_text)
        metadata = request.payload.get("metadata", {})
        embedding_id = upsert_profile_embedding(user_id, embedding, metadata)

        return AgentResponse(
            request_id=request.request_id,
            payload={
                "embedding_id": embedding_id,
                "vector_dim": len(embedding),
            },
        )

    def _generate_brief_reason(
        self, cand: dict, shared_interests: list[str], user_profile: dict
    ) -> str:
        """Generate a one-line reason for why this candidate was matched."""
        parts = []
        total = cand.get("total_score", 0)
        if total >= 80:
            parts.append("高度匹配")
        elif total >= 60:
            parts.append("比较匹配")

        if shared_interests:
            parts.append(f"共同兴趣: {', '.join(shared_interests[:3])}")

        cand_p = cand.get("profile_dict", {}).get("personality", {})
        user_p = user_profile.get("personality", {})
        if cand_p and user_p:
            u_e = user_p.get("extraversion", 0.5)
            c_e = cand_p.get("extraversion", 0.5)
            if abs(u_e + c_e - 1.0) < 0.3:
                parts.append("性格互补")

        return "，".join(parts) if parts else "综合匹配"
