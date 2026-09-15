import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserModel(Base):
    """Registered Users Table for Multi-User Isolation."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    sessions = relationship(
        "SessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="SessionModel.updated_at.desc()"
    )


class SessionModel(Base):
    """Conversation Session Table."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    session_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("UserModel", back_populates="sessions")
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    artifacts = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan", order_by="ArtifactModel.created_at")


class MessageModel(Base):
    """Chat Messages Table."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Skill & Grounding Metadata
    skill_used = Column(String(64), nullable=True)  # 'grounded_qa', 'ship30_essay', 'growth_experiment'
    routing_rationale = Column(Text, nullable=True)
    confidence_level = Column(String(32), nullable=True)  # 'HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT'
    confidence_score = Column(Float, nullable=True)
    citations = Column(JSON, default=list)  # List of retrieved chunk citation objects
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("SessionModel", back_populates="messages")
    artifact = relationship("ArtifactModel", back_populates="message", uselist=False)


class ArtifactModel(Base):
    """Generated Live Artifacts Table."""
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), nullable=False)
    artifact_type = Column(String(64), nullable=False)  # 'markdown', 'html', 'growth_experiment'
    content = Column(Text, nullable=False)
    structured_data = Column(JSON, default=dict)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("SessionModel", back_populates="artifacts")
    message = relationship("MessageModel", back_populates="artifact")


class TranscriptChunkModel(Base):
    """Chunked and indexed podcast transcript segments."""
    __tablename__ = "transcript_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    episode_id = Column(String(128), nullable=False, index=True)
    episode_title = Column(String(512), nullable=False)
    guest_name = Column(String(255), nullable=False, index=True)
    episode_url = Column(Text, nullable=True)
    publication_date = Column(String(64), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # Store embedding vector as JSON list of floats for universal compatibility
    embedding = Column(JSON, nullable=True)
    token_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
