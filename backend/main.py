from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle using the modern lifespan pattern."""
    logger.info("=" * 60)
    logger.info("ResumeIQ API starting up...")

    # ── Gemini API key ────────────────────────────────────────────────────────
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY is not set! Set it in your .env file.")
    else:
        logger.info("Gemini API key found")

    # ── Pre-warm embedding model ──────────────────────────────────────────────
    # Load the HuggingFace model at startup so the first request isn't slow
    try:
        from services.embedder import get_model
        get_model()
        logger.info("Embedding model pre-warmed")
    except Exception as e:
        logger.error(f"Embedding model pre-warm failed: {e}")

    # ── Pre-warm Gemini client ────────────────────────────────────────────────
    try:
        from services.gemini_service import get_gemini_client
        get_gemini_client()
        logger.info("Gemini client pre-warmed")
    except Exception as e:
        logger.warning(f"Gemini client pre-warm failed: {e}")

    # ── ChromaDB knowledge base status ────────────────────────────────────────
    try:
        from services.vector_store import is_knowledge_base_ready, get_collection_count, COLLECTIONS
        for name in COLLECTIONS:
            count = get_collection_count(name)
            status = "OK" if count > 0 else "EMPTY"
            logger.info(f"  ChromaDB '{name}': {count} docs [{status}]")

        if not is_knowledge_base_ready():
            logger.warning("Knowledge base not fully ingested!")
            logger.warning("  Run: python scripts/ingest_datasets.py --resume Resume.csv --jobs training_data.csv --ner train_data.json")
        else:
            logger.info("Knowledge base ready")
    except Exception as e:
        logger.error(f"ChromaDB startup check failed: {e}")

    logger.info("Server ready!")
    logger.info("=" * 60)

    yield  # App runs here

    logger.info("ResumeIQ API shutting down")


app = FastAPI(
    title="ResumeIQ API",
    description="RAG-powered resume analysis using Gemini AI + ChromaDB + HuggingFace embeddings",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.analyse import router as analyse_router
app.include_router(analyse_router, prefix="/api", tags=["Resume Analysis"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "ResumeIQ API",
        "version": "2.0.0",
        "docs":    "/docs",
        "health":  "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)