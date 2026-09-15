import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.db_models import SessionModel, MessageModel, ArtifactModel


@pytest.mark.asyncio
async def test_session_message_artifact_persistence(test_db_session: AsyncSession):
    # 1. Create Session
    session = SessionModel(title="PLG Growth Loops")
    test_db_session.add(session)
    await test_db_session.commit()
    await test_db_session.refresh(session)
    assert session.id is not None

    # 2. Add User and Assistant Messages with Grounding Metadata
    user_msg = MessageModel(
        session_id=session.id,
        role="user",
        content="How do we design a viral growth loop?"
    )
    test_db_session.add(user_msg)
    await test_db_session.commit()

    assistant_msg = MessageModel(
        session_id=session.id,
        role="assistant",
        content="Here is the viral growth loop framework...",
        skill_used="growth_experiment",
        routing_rationale="User requested growth experiment framework.",
        confidence_level="HIGH",
        confidence_score=0.88,
        citations=[{"guest": "Brian Balfour", "episode": "Growth Loops"}]
    )
    test_db_session.add(assistant_msg)
    await test_db_session.commit()
    await test_db_session.refresh(assistant_msg)

    # 3. Add Artifact
    artifact = ArtifactModel(
        session_id=session.id,
        message_id=assistant_msg.id,
        title="Viral Growth Loop Experiment",
        artifact_type="growth_experiment",
        content='{"title": "Viral Loop Experiment"}',
        structured_data={"title": "Viral Loop Experiment", "target_metric": "K-factor"}
    )
    test_db_session.add(artifact)
    await test_db_session.commit()

    # 4. Query back and verify relations
    stmt = select(SessionModel).where(SessionModel.id == session.id)
    res = await test_db_session.execute(stmt)
    retrieved_session = res.scalar_one()

    # Load messages
    msg_stmt = select(MessageModel).where(MessageModel.session_id == session.id)
    msg_res = await test_db_session.execute(msg_stmt)
    messages = msg_res.scalars().all()
    assert len(messages) == 2
    assert messages[1].confidence_level == "HIGH"
    assert messages[1].confidence_score == 0.88

    # Load artifacts
    art_stmt = select(ArtifactModel).where(ArtifactModel.session_id == session.id)
    art_res = await test_db_session.execute(art_stmt)
    artifacts = art_res.scalars().all()
    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == "growth_experiment"
    assert artifacts[0].structured_data["target_metric"] == "K-factor"
