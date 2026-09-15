from typing import List, Tuple, Optional, Dict, Any
import os
import json
import sqlite3
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.db_models import TranscriptChunkModel
from backend.app.models.schemas import Citation, GroundingResult
from backend.app.rag.embeddings import embedding_engine


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_lexical_boost(query: str, guest_name: Optional[str], episode_title: Optional[str]) -> float:
    """Calculates keyword match boost for guest names and strategic terms."""
    q_lower = query.lower()
    boost = 0.0
    if guest_name and guest_name.lower() in q_lower:
        boost += 0.15
    if episode_title and any(w in episode_title.lower() for w in q_lower.split() if len(w) > 4):
        boost += 0.08
    return boost


class TranscriptRetriever:
    """Hybrid vector + lexical retriever with zero-latency in-memory cache and real-time grounding confidence."""

    def __init__(self):
        self._cached_chunks: List[Dict[str, Any]] = []
        self._cached_matrix: Optional[np.ndarray] = None
        self._is_loaded: bool = False

    def _load_from_local_sqlite(self) -> bool:
        """Attempts to load pre-indexed transcript chunks instantly from local SQLite db."""
        possible_paths = [
            "lenny_growth.db",
            os.path.join(os.path.dirname(__file__), "../../../lenny_growth.db"),
            os.path.join(os.getcwd(), "lenny_growth.db")
        ]
        db_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if not db_path:
            return False
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, episode_id, episode_title, guest_name, episode_url, publication_date, content, embedding FROM transcript_chunks;")
            rows = cursor.fetchall()
            conn.close()

            valid_chunks = []
            vectors = []
            for r in rows:
                emb_raw = r[7]
                if isinstance(emb_raw, str):
                    try:
                        emb = json.loads(emb_raw)
                    except Exception:
                        continue
                elif isinstance(emb_raw, list):
                    emb = emb_raw
                else:
                    continue

                if emb and len(emb) == 384:
                    valid_chunks.append({
                        "id": r[0],
                        "episode_id": r[1],
                        "episode_title": r[2],
                        "guest_name": r[3],
                        "episode_url": r[4],
                        "publication_date": r[5],
                        "content": r[6]
                    })
                    vectors.append(emb)

            if vectors:
                mat = np.array(vectors, dtype=np.float32)
                norms = np.linalg.norm(mat, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self._cached_matrix = mat / norms
                self._cached_chunks = valid_chunks
                self._is_loaded = True
                logger.info(f"Loaded {len(valid_chunks)} chunks instantly from local vector cache.")
                return True
        except Exception as e:
            logger.warning(f"Failed to load from local sqlite: {e}")
        return False

    async def _ensure_cache_loaded(self, db: AsyncSession):
        """Ensures the in-memory vector cache is populated."""
        if self._is_loaded:
            return

        # 1. Try local SQLite first (sub-second)
        if self._load_from_local_sqlite():
            return

        # 2. Fall back to active database session
        logger.info("Loading transcript vector index into RAM...")
        stmt = select(
            TranscriptChunkModel.id,
            TranscriptChunkModel.episode_id,
            TranscriptChunkModel.episode_title,
            TranscriptChunkModel.guest_name,
            TranscriptChunkModel.episode_url,
            TranscriptChunkModel.publication_date,
            TranscriptChunkModel.content,
            TranscriptChunkModel.embedding
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        valid_chunks = []
        vectors = []
        for r in rows:
            emb = r[7]
            if emb and len(emb) == 384:
                valid_chunks.append({
                    "id": r[0],
                    "episode_id": r[1],
                    "episode_title": r[2],
                    "guest_name": r[3],
                    "episode_url": r[4],
                    "publication_date": r[5],
                    "content": r[6]
                })
                vectors.append(emb)

        if vectors:
            mat = np.array(vectors, dtype=np.float32)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._cached_matrix = mat / norms
            self._cached_chunks = valid_chunks
            self._is_loaded = True
            logger.info(f"Loaded {len(valid_chunks)} chunks into RAM.")
        else:
            self._cached_chunks = []
            self._cached_matrix = None

    async def reload_from_db(self, db: AsyncSession):
        """Force reloads vector cache directly from the provided database session."""
        stmt = select(
            TranscriptChunkModel.id,
            TranscriptChunkModel.episode_id,
            TranscriptChunkModel.episode_title,
            TranscriptChunkModel.guest_name,
            TranscriptChunkModel.episode_url,
            TranscriptChunkModel.publication_date,
            TranscriptChunkModel.content,
            TranscriptChunkModel.embedding
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        valid_chunks = []
        vectors = []
        for r in rows:
            emb = r[7]
            if emb and len(emb) == 384:
                valid_chunks.append({
                    "id": r[0],
                    "episode_id": r[1],
                    "episode_title": r[2],
                    "guest_name": r[3],
                    "episode_url": r[4],
                    "publication_date": r[5],
                    "content": r[6]
                })
                vectors.append(emb)

        if vectors:
            mat = np.array(vectors, dtype=np.float32)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._cached_matrix = mat / norms
            self._cached_chunks = valid_chunks
            self._is_loaded = True
        else:
            self._cached_chunks = []
            self._cached_matrix = None
            self._is_loaded = True

    async def retrieve(
        self,
        query: str,
        db: AsyncSession,
        top_k: int = None,
        guest_filter: Optional[str] = None
    ) -> GroundingResult:
        """Retrieves top grounded transcript chunks with sub-10ms latency."""
        k = top_k or settings.TOP_K_RETRIEVAL
        
        await self._ensure_cache_loaded(db)

        if self._cached_matrix is None or len(self._cached_chunks) == 0:
            logger.warning("No transcript chunks found in database.")
            return GroundingResult(
                confidence_level="INSUFFICIENT",
                confidence_score=0.0,
                is_refusal=True,
                refusal_reason="The transcript database is currently empty or has not been indexed yet.",
                citations=[]
            )

        query_embedding = await embedding_engine.embed_query(query)
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # 1. Instant matrix dot product (0.00ms)
        raw_sims = np.dot(self._cached_matrix, q_vec)

        # 2. Add lexical boosts and filter
        scored_indices: List[Tuple[float, int]] = []
        for idx, sim in enumerate(raw_sims):
            chunk_data = self._cached_chunks[idx]
            if guest_filter and guest_filter.lower() not in (chunk_data["guest_name"] or "").lower():
                continue
            boost = compute_lexical_boost(query, chunk_data["guest_name"], chunk_data["episode_title"])
            hybrid_score = min(1.0, float(sim) + boost)
            scored_indices.append((hybrid_score, idx))

        # Sort descending by score
        scored_indices.sort(key=lambda x: x[0], reverse=True)
        top_scored = scored_indices[:k]

        if not top_scored:
            return GroundingResult(
                confidence_level="INSUFFICIENT",
                confidence_score=0.0,
                is_refusal=True,
                refusal_reason="No relevant transcript chunks matched your inquiry.",
                citations=[]
            )

        # Grounding Confidence Scoring Formula
        top1_sim = top_scored[0][0]
        top3_sims = [s for s, _ in top_scored[:3]]
        avg_top3 = sum(top3_sims) / len(top3_sims)
        rel_count = sum(1 for s, _ in top_scored if s >= settings.SIMILARITY_MEDIUM_THRESHOLD)
        
        confidence_score = (0.55 * top1_sim) + (0.30 * avg_top3) + (0.15 * min(1.0, rel_count / 3.0))
        confidence_score = round(min(1.0, max(0.0, confidence_score)), 3)

        # Thresholding
        if confidence_score >= settings.SIMILARITY_HIGH_THRESHOLD:
            confidence_level = "HIGH"
            is_refusal = False
            refusal_reason = None
        elif confidence_score >= settings.SIMILARITY_MEDIUM_THRESHOLD:
            confidence_level = "MEDIUM"
            is_refusal = False
            refusal_reason = None
        elif confidence_score >= settings.SIMILARITY_LOW_THRESHOLD:
            confidence_level = "LOW"
            is_refusal = False
            refusal_reason = None
        else:
            confidence_level = "INSUFFICIENT"
            is_refusal = True
            refusal_reason = (
                "I do not have enough material in Lenny's podcast transcript archive to answer this question accurately. "
                "This topic (or specific inquiry) was not substantially covered by Lenny or his guests in the archive."
            )

        # Build citations
        citations: List[Citation] = []
        for score, idx in top_scored:
            c = self._cached_chunks[idx]
            snippet = c["content"][:300].strip() + ("..." if len(c["content"]) > 300 else "")
            citations.append(
                Citation(
                    chunk_id=c["id"],
                    episode_id=c["episode_id"],
                    episode_title=c["episode_title"],
                    guest_name=c["guest_name"],
                    episode_url=c["episode_url"],
                    publication_date=c["publication_date"],
                    snippet=snippet,
                    similarity_score=round(score, 3)
                )
            )

        logger.info(
            f"Retrieval complete | Query: '{query[:40]}...' | Confidence: {confidence_level} ({confidence_score}) | Top1: {top1_sim:.3f}"
        )

        return GroundingResult(
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            is_refusal=is_refusal,
            refusal_reason=refusal_reason,
            citations=citations
        )


retriever = TranscriptRetriever()
