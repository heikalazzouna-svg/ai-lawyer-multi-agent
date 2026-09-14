from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.logging_config import configure_logging
from api.core.telemetry import configure_telemetry, get_metrics
from api.routers import auth, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs setup on startup and teardown on shutdown.
    """
    # ── Startup ──
    configure_logging(level="INFO")
    configure_telemetry()
    yield
    # ── Shutdown ──
    # (cleanup resources like DB pools here)


app = FastAPI(
    title="AI Lawyer Enterprise API",
    description="Production-grade RAG backend for legal document analysis. "
                "Features hybrid search, JWT authentication, streaming responses, "
                "semantic caching, and full observability.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health & Metrics Endpoints ──

@app.get("/health", tags=["ops"])
def health_check():
    """Liveness probe for container orchestrators (Kubernetes, ECS)."""
    return {"status": "healthy", "service": "AI Lawyer API"}


@app.get("/metrics", tags=["ops"])
def metrics():
    """
    Expose application-level metrics (LLM calls, latency, cache performance).
    In production, replace with Prometheus /metrics endpoint.
    """
    return get_metrics()


# ── Route Registration ──

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
