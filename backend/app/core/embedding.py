"""Embedding client — wraps the LLM embedding API."""

from loguru import logger


class EmbeddingClient:
    """Client for generating text embeddings via the LLM adapter."""

    def __init__(self, llm_adapter):
        self._adapter = llm_adapter

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return await self._adapter.embed(texts)

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self._adapter.embed([text])
        return results[0]

    def profile_to_text(self, profile: dict) -> str:
        """Convert a structured profile dict to natural language for embedding.

        This is the KEY function — the quality of the natural language
        representation directly affects matching quality.
        """
        parts = []

        # Static attributes
        static = profile.get("static_attrs", {})
        if static.get("city"):
            parts.append(f"用户在{static['city']}生活。")
        if static.get("age_range"):
            parts.append(f"年龄段{static['age_range']}。")

        # Interests
        interests = profile.get("interests", [])
        if interests:
            interest_names = [i.get("sub_category", i.get("category", "")) for i in interests]
            parts.append(f"兴趣爱好包括: {', '.join(interest_names)}。")
            for i in interests:
                cat = i.get("category", "")
                sub = i.get("sub_category", "")
                parts.append(f"喜欢{sub}类型的{cat}活动。")

        # Personality
        personality = profile.get("personality", {})
        if personality:
            o = personality.get("openness", "?")
            e = personality.get("extraversion", "?")
            c = personality.get("conscientiousness", "?")
            parts.append(f"性格特征: 开放性{o}, 外向性{e}, 尽责性{c}。")

        # Social needs
        social = profile.get("social_need", {})
        if social:
            bt = social.get("buddy_type", "")
            sch = social.get("schedule", "")
            if bt:
                parts.append(f"希望找{bt}类型的搭子。")
            if sch:
                parts.append(f"时间偏好是{sch}。")

        text = " ".join(parts)
        if not text.strip():
            text = "新用户，画像待完善。"
        return text


# Singleton
_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        raise RuntimeError("EmbeddingClient not initialized. Call init_embedding_client() first.")
    return _embedding_client


def init_embedding_client(llm_adapter):
    global _embedding_client
    _embedding_client = EmbeddingClient(llm_adapter)
    logger.info("EmbeddingClient initialized")
