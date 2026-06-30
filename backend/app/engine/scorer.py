"""Matching Scorer — weighted multi-dimensional similarity scoring (FR-MD-02).

Implements the scoring formula:
    total = 0.50 * interest_sim + 0.30 * personality_compat + 0.20 * social_match
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# Configurable weights (can be loaded from MatchingRule table)
DEFAULT_WEIGHTS = {
    "interest": 0.50,
    "personality": 0.30,
    "social": 0.20,
}


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a).reshape(1, -1)
    b = np.array(vec_b).reshape(1, -1)
    sim = cosine_similarity(a, b)[0][0]
    # Clamp to [0, 1] — cosine can rarely be slightly negative or >1 due to float precision
    return max(0.0, min(1.0, float(sim)))


def compute_personality_compatibility(user_p: dict, cand_p: dict) -> float:
    """Compute personality compatibility score.

    Strategy:
    - Openness: similarity is good (both curious or both practical)
    - Extraversion: complementarity is good (introvert + extrovert balance)
    - Conscientiousness: similarity is good (both organized or both flexible)

    Returns a score in [0, 1].
    """
    u_open = float(user_p.get("openness", 0.5))
    c_open = float(cand_p.get("openness", 0.5))
    u_extra = float(user_p.get("extraversion", 0.5))
    c_extra = float(cand_p.get("extraversion", 0.5))
    u_cons = float(user_p.get("conscientiousness", 0.5))
    c_cons = float(cand_p.get("conscientiousness", 0.5))

    # Openness: similarity (1 - abs(diff))
    openness_match = 1.0 - abs(u_open - c_open)

    # Extraversion: complementarity
    # Ideal: sum ≈ 1.0 (one introvert + one extrovert)
    extraversion_comp = 1.0 - abs((u_extra + c_extra) - 1.0)

    # Conscientiousness: similarity
    conscientiousness_match = 1.0 - abs(u_cons - c_cons)

    # Weighted combination
    score = 0.4 * openness_match + 0.3 * extraversion_comp + 0.3 * conscientiousness_match
    return max(0.0, min(1.0, score))


def compute_social_match(user_profile: dict, cand_profile: dict) -> float:
    """Compute social need match score.

    Components:
    - buddy_type match: 0.4
    - schedule overlap: 0.3
    - city match: 0.3
    """
    score = 0.0
    user_sn = user_profile.get("social_need", {})
    cand_sn = cand_profile.get("social_need", {})

    # Buddy type match
    u_bt = user_sn.get("buddy_type", "")
    c_bt = cand_sn.get("buddy_type", "")
    if u_bt and c_bt:
        if u_bt == c_bt:
            score += 0.4
        else:
            score += 0.1  # partial credit for having any buddy type
    else:
        score += 0.2  # neutral

    # Schedule overlap
    u_sch = user_sn.get("schedule", "")
    c_sch = cand_sn.get("schedule", "")
    if u_sch and c_sch:
        if u_sch == c_sch:
            score += 0.3
        elif u_sch == "flexible" or c_sch == "flexible":
            score += 0.25
        else:
            score += 0.1
    else:
        score += 0.15

    # City match
    u_city = user_profile.get("static_attrs", {}).get("city", "")
    c_city = cand_profile.get("static_attrs", {}).get("city", "")
    if u_city and c_city:
        if u_city == c_city:
            score += 0.3
    else:
        score += 0.15

    return max(0.0, min(1.0, score))


def compute_full_score(
    user_vec: list[float] | None,
    candidate_vec: list[float] | None,
    user_profile: dict,
    candidate_profile: dict,
    weights: dict | None = None,
) -> dict:
    """Compute the full weighted matching score.

    Args:
        user_vec: User's embedding vector (from ChromaDB).
        candidate_vec: Candidate's embedding vector.
        user_profile: Full user profile dict.
        candidate_profile: Full candidate profile dict.
        weights: Optional weight overrides.

    Returns:
        Dict with total_score, breakdown, and detail.
    """
    w = weights or DEFAULT_WEIGHTS

    # 1. Interest similarity (from embeddings)
    if user_vec and candidate_vec:
        interest_sim = compute_cosine_similarity(user_vec, candidate_vec)
    else:
        interest_sim = 0.5  # default if no embeddings

    # 2. Personality compatibility
    user_pers = user_profile.get("personality", {})
    cand_pers = candidate_profile.get("personality", {})
    personality_score = compute_personality_compatibility(user_pers, cand_pers)

    # 3. Social need match
    social_score = compute_social_match(user_profile, candidate_profile)

    # Weighted total (scaled to 0-100)
    interest_weighted = w["interest"] * interest_sim * 100
    personality_weighted = w["personality"] * personality_score * 100
    social_weighted = w["social"] * social_score * 100
    total = interest_weighted + personality_weighted + social_weighted

    return {
        "total_score": round(total, 1),
        "interest_score": round(interest_weighted, 1),
        "personality_score": round(personality_weighted, 1),
        "social_score": round(social_weighted, 1),
        "breakdown": {
            "interest_raw": round(interest_sim, 4),
            "personality_raw": round(personality_score, 4),
            "social_raw": round(social_score, 4),
            "weights_used": w,
        },
        "detail": {
            "user_openness": user_pers.get("openness", 0.5),
            "user_extraversion": user_pers.get("extraversion", 0.5),
            "user_conscientiousness": user_pers.get("conscientiousness", 0.5),
            "cand_openness": cand_pers.get("openness", 0.5),
            "cand_extraversion": cand_pers.get("extraversion", 0.5),
            "cand_conscientiousness": cand_pers.get("conscientiousness", 0.5),
            "same_city": user_profile.get("static_attrs", {}).get("city")
            == candidate_profile.get("static_attrs", {}).get("city"),
        },
    }
