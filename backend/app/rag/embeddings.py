import os
from typing import List
import numpy as np
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger

# Lazy-loaded sentence-transformer model
_local_st_model = None


class EmbeddingEngine:
    """Unified embedding engine supporting local models, Ollama, and OpenAI."""

    def __init__(self):
        self.dim = settings.EMBEDDING_DIM

    def _get_local_model(self):
        global _local_st_model
        if _local_st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local embedding model: {settings.LOCAL_EMBEDDING_MODEL}")
                _local_st_model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer: {e}")
                _local_st_model = False
        return _local_st_model

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of strings into normalized float vectors."""
        if not texts:
            return []

        # 1. Try local SentenceTransformer (Fast & Offline)
        st_model = self._get_local_model()
        if st_model:
            try:
                embeddings = st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.warning(f"Local SentenceTransformer embedding error: {e}")

        # 2. Try Ollama Embedding endpoint
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embed",
                    json={"model": settings.OLLAMA_EMBED_MODEL, "input": texts}
                )
                if res.status_code == 200:
                    data = res.json()
                    if "embeddings" in data:
                        raw_vecs = np.array(data["embeddings"])
                        # L2 normalize
                        norms = np.linalg.norm(raw_vecs, axis=1, keepdims=True)
                        norms[norms == 0] = 1.0
                        return (raw_vecs / norms).tolist()
        except Exception:
            pass

        # 3. Try OpenAI Embedding if key exists
        if settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={"model": settings.OPENAI_EMBED_MODEL, "input": texts}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return [item["embedding"] for item in data["data"]]
            except Exception as e:
                logger.warning(f"OpenAI embedding error: {e}")

        # 4. Deterministic fallback embedding (for robust test & offline simulation)
        logger.info("Using fallback deterministic embedding.")
        embeddings = []
        for text in texts:
            # Deterministic hash-based pseudo-vector of length 384
            vec = np.zeros(self.dim, dtype=np.float32)
            for i, word in enumerate(text.lower().split()):
                idx = hash(word) % self.dim
                vec[idx] += 1.0 / (i + 1)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string."""
        results = await self.embed_texts([query])
        return results[0] if results else [0.0] * self.dim


embedding_engine = EmbeddingEngine()
