import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.db_models import TranscriptChunkModel
from backend.app.rag.retriever import retriever, cosine_similarity
from backend.app.rag.embeddings import embedding_engine


@pytest.mark.asyncio
async def test_cosine_similarity():
    """Tests vector cosine similarity computation."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(v1, v2) == pytest.approx(1.0, rel=1e-3)

    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v3) == pytest.approx(0.0, rel=1e-3)


@pytest.mark.asyncio
async def test_grounded_retrieval_and_confidence(test_db_session: AsyncSession):
    """Verifies that relevant query returns HIGH/MEDIUM grounding and citations."""
    # Seed chunks
    emb1 = await embedding_engine.embed_query("growth loops retention brian balfour")
    emb2 = await embedding_engine.embed_query("b2b plg elena verna monetization")
    
    c1 = TranscriptChunkModel(
        episode_id="brian-balfour",
        episode_title="Why ChatGPT will be the next growth channel",
        guest_name="Brian Balfour",
        episode_url="https://youtube.com/watch?v=123",
        publication_date="2024-01-01",
        chunk_index=0,
        content="Brian Balfour discusses how growth loops compound compared to traditional marketing funnels.",
        embedding=emb1,
        token_count=50
    )
    c2 = TranscriptChunkModel(
        episode_id="elena-verna",
        episode_title="B2B PLG Playbook",
        guest_name="Elena Verna",
        episode_url="https://youtube.com/watch?v=456",
        publication_date="2024-02-01",
        chunk_index=0,
        content="Elena Verna breaks down how B2B product-led growth requires distinct acquisition and monetization loops.",
        embedding=emb2,
        token_count=50
    )
    test_db_session.add_all([c1, c2])
    await test_db_session.commit()
    await retriever.reload_from_db(test_db_session)

    # Query matching Brian Balfour
    result = await retriever.retrieve("What did Brian Balfour say about growth loops?", test_db_session)
    assert not result.is_refusal
    assert result.confidence_level in ["HIGH", "MEDIUM"]
    assert len(result.citations) > 0
    assert result.citations[0].guest_name == "Brian Balfour"


@pytest.mark.asyncio
async def test_out_of_domain_refusal_guardrail(test_db_session: AsyncSession):
    """Verifies that out-of-domain query triggers honest refusal."""
    # Seed specific PM chunk
    emb = await embedding_engine.embed_query("retention cohorts product market fit")
    c = TranscriptChunkModel(
        episode_id="pm-episode",
        episode_title="Product Market Fit",
        guest_name="Casey Winters",
        episode_url="",
        publication_date="2023-01-01",
        chunk_index=0,
        content="Casey Winters describes retention cohort analysis for consumer marketplaces.",
        embedding=emb,
        token_count=50
    )
    test_db_session.add(c)
    await test_db_session.commit()
    await retriever.reload_from_db(test_db_session)

    # Empty DB or completely irrelevant query
    empty_result = await retriever.retrieve("How do I bake sourdough bread in a kitchen oven?", test_db_session)
    # The score should fall below threshold and trigger refusal
    assert empty_result.confidence_level in ["LOW", "INSUFFICIENT"]
