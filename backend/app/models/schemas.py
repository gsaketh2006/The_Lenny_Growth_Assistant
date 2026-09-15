from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# -------------------------------------------------------------------------
# Citation & Grounding Schemas
# -------------------------------------------------------------------------

class Citation(BaseModel):
    chunk_id: str
    episode_id: str
    episode_title: str
    guest_name: str
    episode_url: Optional[str] = None
    publication_date: Optional[str] = None
    snippet: str
    similarity_score: float = 0.0


class GroundingResult(BaseModel):
    confidence_level: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]
    confidence_score: float
    is_refusal: bool = False
    refusal_reason: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)


# -------------------------------------------------------------------------
# Growth Experiment Card Schema (Differentiator)
# -------------------------------------------------------------------------

class TestPlanStep(BaseModel):
    day_range: str = Field(description="Sprint timeframe, e.g., 'Day 1-2'")
    action: str = Field(description="Concrete action item to implement or measure")


class GroundingSource(BaseModel):
    guest: str
    episode: str
    quote_or_concept: str


class GrowthExperimentCard(BaseModel):
    title: str = Field(description="Short, punchy experiment name")
    hypothesis: str = Field(
        description="Strict format: If we [Action], then [Outcome] will happen, because [Mechanism]."
    )
    target_metric: str = Field(description="The primary single metric to move")
    secondary_metrics: List[str] = Field(
        default_factory=list,
        description="Guardrail or secondary conversion metrics"
    )
    test_plan: List[TestPlanStep] = Field(
        description="Step-by-step 1-week minimal testing roadmap"
    )
    risks_and_invalidation: List[str] = Field(
        description="Risks, pitfalls, or failure criteria"
    )
    expected_impact: Literal["High", "Medium", "Low"] = "High"
    grounding_source: GroundingSource


# -------------------------------------------------------------------------
# Artifact Schemas
# -------------------------------------------------------------------------

class ArtifactBase(BaseModel):
    title: str
    artifact_type: Literal["markdown", "html", "growth_experiment"]
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    version: int = 1


class ArtifactCreate(ArtifactBase):
    session_id: str
    message_id: Optional[str] = None


class ArtifactResponse(ArtifactBase):
    id: str
    session_id: str
    message_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Session & Message Schemas
# -------------------------------------------------------------------------

class MessageBase(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class MessageCreate(MessageBase):
    session_id: str


class MessageResponse(MessageBase):
    id: str
    session_id: str
    skill_used: Optional[str] = None
    routing_rationale: Optional[str] = None
    confidence_level: Optional[str] = None
    confidence_score: Optional[float] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    artifact: Optional[ArtifactResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    session_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    id: str
    title: str
    session_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = Field(default_factory=list)
    artifacts: List[ArtifactResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Chat & Routing Request/Response
# -------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(min_length=1)
    provider: Optional[Literal["ollama", "anthropic", "openai"]] = None
    model: Optional[str] = None


class RoutingDecision(BaseModel):
    skill: Literal["grounded_qa", "ship30_essay", "growth_experiment"]
    confidence: float
    rationale: str
    entities: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------------------------------------------------
# Provider & System Health
# -------------------------------------------------------------------------

class ProviderInfo(BaseModel):
    id: str
    name: str
    is_available: bool
    is_active: bool
    current_model: str
    available_models: List[str]
    notes: Optional[str] = None


class ProviderSelectRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None


class CustomProviderCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(min_length=1)
    api_type: Literal["openai_compatible", "anthropic_compatible", "ollama_compatible"] = "openai_compatible"
    base_url: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    api_key: Optional[str] = None
    notes: Optional[str] = None


class ProviderTestRequest(BaseModel):
    api_type: Literal["openai_compatible", "anthropic_compatible", "ollama_compatible"] = "openai_compatible"
    base_url: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    api_key: Optional[str] = None


class ProviderTestResponse(BaseModel):
    success: bool
    latency_ms: float = 0.0
    message: str
    sample_output: Optional[str] = None



class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    active_provider: str
    ollama_online: bool
    transcripts_indexed_count: int
    version: str


# -------------------------------------------------------------------------
# User Authentication Schemas (Multi-User Isolation)
# -------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=4)
    name: Optional[str] = "User"
    full_name: Optional[str] = None

    def get_name(self) -> str:
        return (self.name or self.full_name or "User").strip()


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    full_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: Any) -> None:
        if not self.full_name:
            self.full_name = self.name


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
    access_token: Optional[str] = None
    token_type: str = "bearer"

    def model_post_init(self, __context: Any) -> None:
        if not self.access_token:
            self.access_token = self.token

