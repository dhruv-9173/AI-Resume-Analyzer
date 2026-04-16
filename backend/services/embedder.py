from sentence_transformers import SentenceTransformer
import logging
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

# Using a lightweight but powerful model - runs fully locally
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model() -> SentenceTransformer:
    """Lazy load the embedding model (singleton)."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully")
    return _model


def embed_text(text: str) -> List[float]:
    """Generate embedding vector for a single text string."""
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embedding vectors for a list of texts (batch)."""
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False)
    return embeddings.tolist()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))