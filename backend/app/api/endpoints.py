import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import get_db
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
    get_current_user_required
)
from backend.app.models.db_models import UserModel, SessionModel, MessageModel, ArtifactModel, TranscriptChunkModel
from backend.app.models.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    AuthResponse,
    SessionResponse,
    SessionSummary,
    SessionCreate,
    MessageResponse,
    ChatRequest,
    ProviderInfo,
    ProviderSelectRequest,
    CustomProviderCreate,
    ProviderTestRequest,
    ProviderTestResponse,
    HealthResponse,
    ArtifactResponse
)
from backend.app.rag.retriever import retriever
from backend.app.rag.ingest import ingest_transcripts
from backend.app.agent.router import skill_router
from backend.app.agent.skills import get_skill
from backend.app.agent.providers import provider_registry, OllamaClient

api_router = APIRouter()


# -------------------------------------------------------------------------
# User Authentication Endpoints (Multi-User Isolation)
# -------------------------------------------------------------------------

@api_router.post("/auth/register", response_model=AuthResponse)
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    """Registers a new user and generates an access token."""
    email_clean = payload.email.strip().lower()
    
    # Check if user already exists
    stmt = select(UserModel).where(UserModel.email == email_clean)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Hash password and create user
    hashed_pwd = hash_password(payload.password)
    new_user = UserModel(
        email=email_clean,
        name=payload.get_name(),
        hashed_password=hashed_pwd
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate JWT token
    token = create_access_token({"sub": new_user.id, "email": new_user.email})
    
    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        token=token
    )


@api_router.post("/auth/login", response_model=AuthResponse)
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """Logs in an existing user and returns an access token."""
    email_clean = payload.email.strip().lower()
    
    stmt = select(UserModel).where(UserModel.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=token
    )


@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(user: UserModel = Depends(get_current_user_required)):
    """Returns profile for currently authenticated user."""
    return UserResponse.model_validate(user)


# -------------------------------------------------------------------------
# Health & Status
# -------------------------------------------------------------------------

@api_router.get("/health", response_model=HealthResponse)
async def get_health(db: AsyncSession = Depends(get_db)):
    """System health check verifying DB, Ollama, and index state."""
    db_connected = False
    chunk_count = 0
    try:
        count_stmt = select(func.count(TranscriptChunkModel.id))
        chunk_count = (await db.execute(count_stmt)).scalar() or 0
        db_connected = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    ollama_online = await OllamaClient().is_available()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        active_provider=provider_registry.active_provider_id,
        ollama_online=ollama_online,
        transcripts_indexed_count=chunk_count,
        version=settings.VERSION
    )


# -------------------------------------------------------------------------
# Provider Selection
# -------------------------------------------------------------------------

@api_router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    """Lists available LLM providers and models."""
    return await provider_registry.get_providers_info()


@api_router.post("/providers/select")
async def select_provider(payload: ProviderSelectRequest):
    """Switches active provider without code changes or restarts."""
    provider_registry.set_active_provider(payload.provider, payload.model, payload.api_key)
    return {
        "status": "success",
        "active_provider": provider_registry.active_provider_id,
        "active_model": provider_registry.active_model_name
    }


@api_router.post("/providers/custom", response_model=ProviderInfo)
async def create_custom_provider(payload: CustomProviderCreate):
    """Registers a new user-defined custom LLM provider (OpenAI, Anthropic, or Ollama compatible)."""
    return provider_registry.register_custom_provider(payload)


@api_router.delete("/providers/custom/{provider_id}")
async def delete_custom_provider(provider_id: str):
    """Deletes a custom provider configuration."""
    success = provider_registry.remove_custom_provider(provider_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom provider '{provider_id}' not found."
        )
    return {"status": "success", "deleted_provider_id": provider_id}


@api_router.post("/providers/test", response_model=ProviderTestResponse)
async def test_provider_endpoint(payload: ProviderTestRequest):
    """Probes a target provider endpoint and measures response latency."""
    res = await provider_registry.test_connection(
        api_type=payload.api_type,
        base_url=payload.base_url,
        model_name=payload.model_name,
        api_key=payload.api_key
    )
    return ProviderTestResponse(**res)


# -------------------------------------------------------------------------

# User-Scoped Session Management
# -------------------------------------------------------------------------

@api_router.get("/sessions", response_model=List[SessionSummary])
async def list_sessions(
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Lists conversation sessions scoped to the authenticated user."""
    stmt = (
        select(
            SessionModel.id,
            SessionModel.title,
            SessionModel.created_at,
            SessionModel.updated_at,
            func.count(MessageModel.id).label("message_count")
        )
        .outerjoin(MessageModel, SessionModel.id == MessageModel.session_id)
    )

    if user:
        stmt = stmt.where(SessionModel.user_id == user.id)
    else:
        stmt = stmt.where(SessionModel.user_id.is_(None))

    stmt = stmt.group_by(SessionModel.id).order_by(SessionModel.updated_at.desc())
    result = await db.execute(stmt)
    rows = result.all()
    return [
        SessionSummary(
            id=r[0],
            title=r[1],
            created_at=r[2],
            updated_at=r[3],
            message_count=r[4]
        )
        for r in rows
    ]


@api_router.post("/sessions", response_model=SessionResponse)
async def create_session(
    payload: Optional[SessionCreate] = None,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new isolated conversation session linked to the current user."""
    title = payload.title if payload and payload.title else "New Conversation"
    session = SessionModel(
        title=title,
        user_id=user.id if user else None
    )
    db.add(session)
    await db.commit()
    
    stmt = (
        select(SessionModel)
        .options(
            selectinload(SessionModel.messages).selectinload(MessageModel.artifact),
            selectinload(SessionModel.artifacts)
        )
        .where(SessionModel.id == session.id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@api_router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves session history and attached artifacts with user-access verification."""
    stmt = (
        select(SessionModel)
        .options(
            selectinload(SessionModel.messages).selectinload(MessageModel.artifact),
            selectinload(SessionModel.artifacts)
        )
        .where(SessionModel.id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user ownership if session belongs to a user
    if session.user_id and (not user or session.user_id != user.id):
        raise HTTPException(status_code=403, detail="Access denied to this conversation session.")
        
    return session


@api_router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a conversation session and all its messages."""
    stmt = select(SessionModel).where(SessionModel.id == session_id)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    if not sess:
        return {"status": "deleted", "session_id": session_id}

    if sess.user_id and (not user or sess.user_id != user.id):
        raise HTTPException(status_code=403, detail="Access denied to delete this session.")

    del_stmt = delete(SessionModel).where(SessionModel.id == session_id)
    await db.execute(del_stmt)
    await db.commit()
    return {"status": "deleted", "session_id": session_id}


# -------------------------------------------------------------------------
# Streaming Chat & 3-Skill Dispatch (SSE)
# -------------------------------------------------------------------------

@api_router.post("/chat")
async def chat_endpoint(
    payload: ChatRequest,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Main streaming chat endpoint with user isolation, router rationale, confidence score, citations, and artifacts."""
    
    # 1. Resolve or create session
    session_id = payload.session_id
    if not session_id:
        session = SessionModel(
            title=payload.message[:40] + "...",
            user_id=user.id if user else None
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        session_id = session.id
    else:
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            session = SessionModel(
                id=session_id,
                title=payload.message[:40] + "...",
                user_id=user.id if user else None
            )
            db.add(session)
            await db.commit()
        elif user and session.user_id is None:
            # Associate anonymous session with now-logged-in user
            session.user_id = user.id
            db.add(session)
            await db.commit()

    # 2. Fetch conversation history
    msg_stmt = (
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at)
    )
    hist_result = await db.execute(msg_stmt)
    db_messages = hist_result.scalars().all()
    chat_history = [{"role": m.role, "content": m.content} for m in db_messages]

    # 3. Persist User Message
    user_msg = MessageModel(session_id=session_id, role="user", content=payload.message)
    db.add(user_msg)
    await db.commit()

    # 4. Route intent to skill
    routing_decision = skill_router.route(payload.message, chat_history)

    # 5. Hybrid RAG retrieval & Grounding Confidence scoring
    grounding = await retriever.retrieve(payload.message, db)

    # 6. Resolve LLM client
    llm = provider_registry.get_client(payload.provider, payload.model)
    skill = get_skill(routing_decision.skill)

    async def sse_generator():
        # Step A: Emit session metadata
        yield f"data: {json.dumps({'type': 'session_init', 'session_id': session_id})}\n\n"

        # Step B: Emit routing decision event
        yield f"data: {json.dumps({'type': 'routing', 'skill': routing_decision.skill, 'rationale': routing_decision.rationale, 'confidence': routing_decision.confidence})}\n\n"

        # Step C: Emit grounding confidence event
        grounding_data = {
            "type": "grounding",
            "confidence_level": grounding.confidence_level,
            "confidence_score": grounding.confidence_score,
            "is_refusal": grounding.is_refusal,
            "refusal_reason": grounding.refusal_reason,
            "citations": [c.model_dump() for c in grounding.citations]
        }
        yield f"data: {json.dumps(grounding_data)}\n\n"

        full_response_text = []
        created_artifact = None

        # Step D: Stream skill execution
        async for event in skill.execute_stream(payload.message, chat_history, grounding, llm):
            if event["type"] == "chunk":
                full_response_text.append(event["content"])
                yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']})}\n\n"
            elif event["type"] == "artifact":
                art_base = event["artifact"]
                # Save artifact to database
                db_art = ArtifactModel(
                    session_id=session_id,
                    title=art_base.title,
                    artifact_type=art_base.artifact_type,
                    content=art_base.content,
                    structured_data=art_base.structured_data,
                    version=art_base.version
                )
                db.add(db_art)
                await db.commit()
                await db.refresh(db_art)

                created_artifact = db_art
                yield f"data: {json.dumps({'type': 'artifact', 'artifact': {'id': db_art.id, 'title': db_art.title, 'artifact_type': db_art.artifact_type, 'content': db_art.content, 'structured_data': db_art.structured_data}})}\n\n"

        # Step E: Persist Assistant Message to DB
        assistant_content = "".join(full_response_text)
        assistant_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            skill_used=routing_decision.skill,
            routing_rationale=routing_decision.rationale,
            confidence_level=grounding.confidence_level,
            confidence_score=grounding.confidence_score,
            citations=[c.model_dump() for c in grounding.citations]
        )
        db.add(assistant_msg)
        
        # Link artifact to message if created
        if created_artifact:
            created_artifact.message_id = assistant_msg.id
            db.add(created_artifact)

        await db.commit()

        # Step F: Emit done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


# -------------------------------------------------------------------------
# Artifacts
# -------------------------------------------------------------------------

@api_router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves an artifact by ID."""
    stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
    result = await db.execute(stmt)
    art = result.scalar_one_or_none()
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return art


# -------------------------------------------------------------------------
# Ingestion API
# -------------------------------------------------------------------------

@api_router.post("/ingest/sample")
async def trigger_sample_ingest(sample_size: int = 30, db: AsyncSession = Depends(get_db)):
    """Ingests and indexes a sample batch of transcripts."""
    count = await ingest_transcripts(db, sample_episodes=sample_size)
    return {"status": "success", "indexed_chunks_count": count}
