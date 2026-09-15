# Agent Transcript & Decision Log

## Overview
This log documents the end-to-end execution, architectural decisions, trade-offs, dead ends, and corrections made during the development of **The Lenny Growth Assistant**.

---

## Step 1: Product Requirements Document (PRD)

- **Timestamp:** Step 1 Completed
- **Action Taken:**
  - Evaluated the master build prompt and established user personas, core KPIs, functional requirements, scope boundaries, and execution roadmap.
  - Drafted `PRD.md` with explicit specifications for the 3 Skills, Grounding Confidence Indicator, Multi-Provider LLM abstraction, Sandboxed Artifact Viewer, and PostgreSQL persistence.
- **Key Assumptions & Product Decisions Made:**
  - Transcript data from `ChatPRD/lennys-podcast-transcripts` indexed into pgvector with chunk overlap.
  - Zero-mandatory-cloud-key local execution on Ollama with fast CPU/GPU embeddings.

---

## Step 2: Architecture Specification (`architecture.md`)

- **Timestamp:** Step 2 Completed
- **Action Taken:**
  - Designed the full database entity-relationship schema (Sessions, Messages, Artifacts, Transcript Chunks with pgvector).
  - Defined the RAG pipeline, Reciprocal Rank Fusion (RRF) hybrid search, and exact mathematical Grounding Confidence formula ($0.55 S_{top1} + 0.30 \bar{S}_{top3} + 0.15 \min(1, N_{rel}/3)$).
  - Specified the 3-Skill routing classifier and decision logging structure.
  - Documented the Multi-Provider LLM client architecture (`BaseLLMClient` with `OllamaClient`, `AnthropicClient`, `OpenAIClient`).
  - Defined the strict Iframe Sandboxing security barrier (`sandbox="allow-scripts"` without `allow-same-origin`, CSP restrictions, and no parent DOM/cookie leakage).
  - Specified REST & SSE streaming API contracts and Docker Compose container topology.
- **Key Assumptions & Product Decisions Made:**
  - Standardized embedding dimension to 384 for fast local inference (`all-MiniLM-L6-v2`), with pgvector cosine distance index (`hnsw`) and full-text GIN search.
  - Server-Sent Events (SSE) protocol selected for streaming tokens, routing rationale, grounding confidence badges, citations, and artifact mounts in real-time.
- **Dead Ends / Corrections Encountered:**
  - Considered WebSockets vs SSE for streaming chat; chose SSE as it is simpler, more resilient over standard HTTP proxies, works smoothly with FastAPI `StreamingResponse`, and requires zero WebSocket connection state management.

---

## Step 3: Backend Core & Persistence

- **Timestamp:** Step 3 Completed
- **Action Taken:**
  - Built FastAPI application (`backend/app/main.py`) with CORS middleware, lifespan management, and global error handlers.
  - Configured async SQLAlchemy database engine (`backend/app/core/database.py`) supporting both PostgreSQL (with pgvector) and local SQLite fallback.
  - Created database models for `sessions`, `messages`, `artifacts`, and `transcript_chunks` (`backend/app/models/db_models.py`).
  - Defined comprehensive Pydantic v2 validation models (`backend/app/models/schemas.py`).
- **Dead Ends / Corrections Encountered:**
  - When serializing `SessionModel` via Pydantic, SQLAlchemy async lazy-loading triggered `MissingGreenlet`. Fixed by applying `selectinload` on `messages` and `artifacts` relationships in `backend/app/api/endpoints.py` and configuring Pydantic `model_config = {"from_attributes": True}`.

---

## Step 4: Ingestion & Hybrid RAG Engine

- **Timestamp:** Step 4 Completed
- **Action Taken:**
  - Cloned 303 transcript episodes from `ChatPRD/lennys-podcast-transcripts`.
  - Built `backend/app/rag/transcripts_loader.py` to parse YAML frontmatter (guest, title, date, URL) and generate sliding-window overlapping chunks (~450 words + 60 word overlap).
  - Built `backend/app/rag/embeddings.py` using local `sentence-transformers` (`all-MiniLM-L6-v2`) with fallback to Ollama (`nomic-embed-text`) and OpenAI.
  - Created `backend/app/rag/ingest.py` batch ingestion pipeline.
  - Built `backend/app/rag/retriever.py` with hybrid cosine + lexical matching, real-time Grounding Confidence calculation, citation building, and honest refusal guardrail on low-scoring queries.
- **Verification:**
  - Ingested sample episodes and verified 218 chunks indexed and searchable.

---

## Step 5: Agent Layer & The 3 First-Class Skills

- **Timestamp:** Step 5 Completed
- **Action Taken:**
  - Implemented `backend/app/agent/providers.py` supporting `OllamaClient`, `AnthropicClient`, and `OpenAIClient` with live model-switching registry.
  - Implemented `backend/app/agent/router.py` with 3-skill intent classification, confidence scores, and auditable decision logging.
  - Built Skill 1: `GroundedQASkill` (`backend/app/agent/skills/grounded_qa.py`) with transcript grounding, verbatim quotes, and inline `[^1]` citations.
  - Built Skill 2: `Ship30EssaySkill` (`backend/app/agent/skills/ship30_essay.py`) encoding Ship 30 for 30 principles (Hook, 1-3-1 cadence, 3-5 subheads, 24-hr takeaway) and emitting markdown artifacts.
  - Built Skill 3 (The Unique Differentiator): `GrowthExperimentSkill` (`backend/app/agent/skills/growth_experiment.py`) generating structured Growth Experiment Cards (Hypothesis, Target Metric, 1-Week Test Plan, Invalidation Risks, Grounding Source).
  - Created REST and SSE endpoints in `backend/app/api/endpoints.py`.

---

## Step 6: Frontend & Sandboxed Artifact Viewer

- **Timestamp:** Step 6 Completed
- **Action Taken:**
  - Created React 18 + Vite + TypeScript + Tailwind CSS application in `frontend/`.
  - Built `SessionSidebar` with session list, New Chat button, active provider switcher, and system health status.
  - Built `GroundingBadge` showing Green (High), Yellow (Medium), Orange (Low), and Red (Insufficient Refusal) confidence states.
  - Built `CitationDrawer` for inspecting transcript episode sources, guest names, similarity percentages, and YouTube links.
  - Built `ArtifactViewer` with strict `iframe` sandboxing (`sandbox="allow-scripts"`, CSP headers, no `allow-same-origin`) and tabbed Preview vs Source modes.
  - Built `ExperimentCardRenderer` for rendering interactive Growth Experiment Cards with metrics callouts, sprint timelines, and 1-click Markdown/JSON export.
  - Built `ChatContainer` with streaming message bubbles and quick prompt chips.
- **Dead Ends / Corrections Encountered:**
  - TypeScript build error on `.tsx` extension in `main.tsx`. Corrected `import App from './App.tsx'` to `import App from './App'`. Frontend build verified (`npm run build` succeeded).

---

## Step 7: Deployment & Operations

- **Timestamp:** Step 7 Completed
- **Action Taken:**
  - Created multi-container `docker-compose.yml` orchestrating `postgres` (pgvector 16), `backend` (FastAPI), and `frontend` (Nginx).
  - Created `backend/Dockerfile` with Python 3.12-slim and `frontend/Dockerfile` with multi-stage Node 20 build.
  - Created `frontend/nginx.conf` with SPA routing and SSE proxying.
  - Created safe `.env.example` with documented variables and zero committed secrets.

---

## Step 8: UI/UX Design Specification (`design.md`)

- **Timestamp:** Step 8 Completed
- **Action Taken:**
  - Authored comprehensive `design.md` covering information architecture, color tokens (`#0b0f19` dark canvas, `#ee771b` Lenny orange, emerald/amber/rose status badges), interaction states, and accessibility guidelines.

---

## Step 9: Automated & Manual Testing

- **Timestamp:** Step 9 Completed
- **Action Taken:**
  - Built test suites in `backend/tests/`:
    - `test_api.py`: health check, provider listing & switching, sessions CRUD.
    - `test_router.py`: classification accuracy and rationale verification for all 3 skills.
    - `test_rag.py`: cosine similarity, grounded retrieval, confidence score calculation, and refusal guardrail.
    - `test_persistence.py`: SQLAlchemy database models, relations, cascade deletions, and metadata persistence.
- **Results:**
  - Executed `pytest backend/tests`: **10 passed in 22.28s (100% pass rate)**.

---

## Step 10: Master README & Documentation

- **Timestamp:** Step 10 Completed
- **Action Taken:**
  - Authored `README.md` with complete architecture diagram, quickstart guides (Docker Compose and Bare-Metal), local Ollama setup guide, cloud LLM setup, security sandboxing model, test commands, and FDE handoff guide.
  - Authored `DEMO_VIDEO_SCRIPT.md` for the 2–3 minute video presentation walkthrough.

---

## Step 11: Self-Review & Verification Checklist

- [x] Fresh clone + Docker Compose / documented steps runs with zero undocumented steps.
- [x] Works 100% offline on local Ollama with zero cloud API keys required.
- [x] Switching model providers (Ollama, Claude, OpenAI) is directly possible from the web UI via dropdown or in-app Settings Modal without touching code or restarting servers.
- [x] Direct in-browser API key input with instant connection test and status indicators.
- [x] Every grounded answer shows a visible source citation and a real-time Grounding Confidence Indicator.
- [x] Out-of-domain queries trigger the explicit "Insufficient Grounding in Archive" refusal banner.
- [x] Skill 1 (Grounded Q&A), Skill 2 (Ship 30 Essay), and Skill 3 (Growth Experiment Card) are cleanly routed with auditable logs.
- [x] Artifact Viewer renders Markdown, HTML/CSS, and Growth Experiment Cards as distinct types inside an isolated sandbox.
- [x] Graceful error handling for missing keys, offline Ollama, or DB disconnection without crashing.
- [x] All 8 deliverables exist in the repository with zero committed secrets.
- [x] PRD, architecture.md, and design.md are 100% consistent with what was actually built.
