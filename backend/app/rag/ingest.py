import asyncio
import argparse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.models.db_models import TranscriptChunkModel
from backend.app.rag.transcripts_loader import load_all_transcripts, chunk_transcript
from backend.app.rag.embeddings import embedding_engine


async def ingest_transcripts(
    db: AsyncSession,
    sample_episodes: Optional[int] = None,
    batch_size: int = 20
) -> int:
    """Ingests, chunks, embeds, and saves transcript records into the database."""
    logger.info(f"Starting transcript ingestion (Sample limit: {sample_episodes or 'ALL'})...")
    
    # Check if already indexed
    count_stmt = select(func.count(TranscriptChunkModel.id))
    existing_count = (await db.execute(count_stmt)).scalar() or 0
    if existing_count > 100:
        logger.info(f"Database already contains {existing_count} chunks. Skipping re-indexing.")
        return existing_count

    episodes = load_all_transcripts(settings.TRANSCRIPTS_DIR, max_episodes=sample_episodes)
    logger.info(f"Loaded {len(episodes)} episodes for indexing.")

    all_chunks = []
    for ep in episodes:
        chunks = chunk_transcript(ep, target_chunk_words=450, overlap_words=60)
        all_chunks.extend(chunks)

    logger.info(f"Total chunks to embed and store: {len(all_chunks)}")

    # Process in batches for efficient embedding
    total_saved = 0
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [c.content for c in batch]
        
        # Generate embeddings
        embeddings = await embedding_engine.embed_texts(texts)
        
        db_records = []
        for chunk_data, emb in zip(batch, embeddings):
            record = TranscriptChunkModel(
                episode_id=chunk_data.episode_id,
                episode_title=chunk_data.episode_title,
                guest_name=chunk_data.guest_name,
                episode_url=chunk_data.episode_url,
                publication_date=chunk_data.publication_date,
                chunk_index=chunk_data.chunk_index,
                content=chunk_data.content,
                embedding=emb,
                token_count=chunk_data.token_count
            )
            db_records.append(record)
        
        db.add_all(db_records)
        await db.commit()
        total_saved += len(db_records)
        
        if (i // batch_size) % 5 == 0 or i + batch_size >= len(all_chunks):
            logger.info(f"Indexed {total_saved}/{len(all_chunks)} chunks...")

    logger.info(f"Ingestion complete. Total chunks indexed: {total_saved}")
    return total_saved


async def main():
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast Transcripts")
    parser.add_argument("--sample", type=int, default=30, help="Number of sample episodes to ingest (default: 30)")
    parser.add_argument("--all", action="store_true", help="Ingest all 300+ episodes")
    args = parser.parse_args()

    await init_db()
    limit = None if args.all else args.sample

    async with AsyncSessionLocal() as session:
        await ingest_transcripts(session, sample_episodes=limit)


if __name__ == "__main__":
    asyncio.run(main())
