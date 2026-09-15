from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.api.endpoints import api_router
from backend.app.rag.ingest import ingest_transcripts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup initialization and shutdown."""
    logger.info("Starting up The Lenny Growth Assistant...")
    # Initialize DB tables
    await init_db()
    
    # Auto-index initial batch of transcripts if database is empty
    try:
        async with AsyncSessionLocal() as session:
            await ingest_transcripts(session, sample_episodes=25)
    except Exception as e:
        logger.warning(f"Initial transcript auto-indexing deferred: {e}")

    yield
    logger.info("Shutting down The Lenny Growth Assistant.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-stack AI Growth Assistant strictly grounded in Lenny's Podcast Transcripts.",
    lifespan=lifespan
)

# Enable CORS for local React/Vite development and container network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Graceful Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. The system has logged this incident and degraded gracefully.",
            "detail": str(exc)
        }
    )


# Mount API routes
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
