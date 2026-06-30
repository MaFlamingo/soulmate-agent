"""MMR (Maximal Marginal Relevance) diversity re-ranking (FR-MD-04).

Ensures the Top-K recommendation list is both relevant AND diverse,
preventing all results from being clustered in the same interest group.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def mmr_rerank(
    candidates: list[dict],
    lambda_: float = 0.7,
    k: int = 5,
) -> list[dict]:
    """Re-rank candidates using MMR for diversity.

    MMR formula:
        MMR(c) = λ * relevance(c) - (1-λ) * max_{s in selected} similarity(c, s)

    Args:
        candidates: List of candidate dicts, each with:
            - candidate_id
            - total_score (0-100, used as relevance)
            - embedding (list[float], for diversity measurement)
            - any other fields (passed through)
        lambda_: Relevance vs diversity tradeoff (0-1).
            1.0 = pure relevance ranking
            0.0 = pure diversity ranking
            Default 0.7 balances both.
        k: Number of results to return.

    Returns:
        Re-ranked list of candidate dicts with updated rank field.
    """
    if len(candidates) <= k:
        # Re-sort and re-rank
        candidates.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        for i, c in enumerate(candidates):
            c["rank"] = i + 1
        return candidates

    # Ensure all candidates have embeddings for diversity computation
    valid = [c for c in candidates if c.get("embedding")]
    no_embed = [c for c in candidates if not c.get("embedding")]

    if len(valid) <= 1:
        # Not enough data for diversity — just sort by score
        candidates.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        for i, c in enumerate(candidates):
            c["rank"] = i + 1
        return candidates[:k]

    selected: list[dict] = []
    remaining: list[dict] = list(valid)

    # First pick: highest scoring
    remaining.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    best = remaining.pop(0)
    selected.append(best)

    # Subsequent picks: MMR
    while len(selected) < k and remaining:
        best_score = float("-inf")
        best_idx = -1

        for i, cand in enumerate(remaining):
            relevance = cand.get("total_score", 0) / 100.0  # normalize to 0-1
            # Max similarity to any already-selected candidate
            max_sim = max(
                _cosine_sim(cand["embedding"], sel["embedding"])
                for sel in selected
            )
            mmr_score = lambda_ * relevance - (1 - lambda_) * max_sim

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))
        else:
            break

    # Add back candidates without embeddings (sorted by score)
    no_embed.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    remaining_slots = k - len(selected)
    selected.extend(no_embed[:remaining_slots])

    # Final sort by score within selected, then assign ranks
    selected.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    for i, c in enumerate(selected):
        c["rank"] = i + 1

    return selected[:k]


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    va = np.array(a).reshape(1, -1)
    vb = np.array(b).reshape(1, -1)
    return float(cosine_similarity(va, vb)[0][0])
