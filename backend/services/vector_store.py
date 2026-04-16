import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

_client = None

# 5 collections — 3 from Kaggle datasets + 2 retained JSON files
COLLECTIONS = {
    "resume_examples":  "Real resume examples from Kaggle categorised resume dataset",
    "job_requirements": "Job descriptions with parsed required/preferred skills per role",
    "ner_profiles":     "NER-tagged resume profiles with extracted entities",
    "ats_rules":        "ATS compatibility rules and formatting checks",
    "skills_taxonomy":  "Skills taxonomy by domain and related roles",
}

KAGGLE_CATEGORIES = [
    "INFORMATION-TECHNOLOGY", "BUSINESS-DEVELOPMENT", "ADVOCATE", "CHEF",
    "FINANCE", "ENGINEERING", "ACCOUNTANT", "FITNESS", "AVIATION", "SALES",
    "HEALTHCARE", "CONSULTANT", "BANKING", "CONSTRUCTION", "PUBLIC-RELATIONS",
    "HR", "DESIGNER", "ARTS", "TEACHER", "APPAREL", "DIGITAL-MEDIA",
    "AGRICULTURE", "AUTOMOBILE", "BPO",
]

ROLE_CATEGORY_MAP = {
    "software":           "INFORMATION-TECHNOLOGY",
    "developer":          "INFORMATION-TECHNOLOGY",
    "it ":                "INFORMATION-TECHNOLOGY",
    "data":               "INFORMATION-TECHNOLOGY",
    "devops":             "INFORMATION-TECHNOLOGY",
    "cloud":              "INFORMATION-TECHNOLOGY",
    "network":            "INFORMATION-TECHNOLOGY",
    "cyber":              "INFORMATION-TECHNOLOGY",
    "machine learning":   "INFORMATION-TECHNOLOGY",
    "ai ":                "INFORMATION-TECHNOLOGY",
    "engineer":           "ENGINEERING",
    "mechanical":         "ENGINEERING",
    "electrical":         "ENGINEERING",
    "civil":              "CONSTRUCTION",
    "construction":       "CONSTRUCTION",
    "finance":            "FINANCE",
    "financial":          "FINANCE",
    "investment":         "FINANCE",
    "accountant":         "ACCOUNTANT",
    "accounting":         "ACCOUNTANT",
    "audit":              "ACCOUNTANT",
    "tax":                "ACCOUNTANT",
    "banking":            "BANKING",
    "banker":             "BANKING",
    "business":           "BUSINESS-DEVELOPMENT",
    "sales":              "SALES",
    "marketing":          "BUSINESS-DEVELOPMENT",
    "consultant":         "CONSULTANT",
    "consulting":         "CONSULTANT",
    "bpo":                "BPO",
    "customer service":   "BPO",
    "public relations":   "PUBLIC-RELATIONS",
    "hr ":                "HR",
    "human resources":    "HR",
    "recruiter":          "HR",
    "talent":             "HR",
    "teacher":            "TEACHER",
    "education":          "TEACHER",
    "instructor":         "TEACHER",
    "healthcare":         "HEALTHCARE",
    "nurse":              "HEALTHCARE",
    "doctor":             "HEALTHCARE",
    "medical":            "HEALTHCARE",
    "fitness":            "FITNESS",
    "chef":               "CHEF",
    "cook":               "CHEF",
    "culinary":           "CHEF",
    "designer":           "DESIGNER",
    "design":             "DESIGNER",
    "ux":                 "DESIGNER",
    "digital media":      "DIGITAL-MEDIA",
    "media":              "DIGITAL-MEDIA",
    "content":            "DIGITAL-MEDIA",
    "artist":             "ARTS",
    "fashion":            "APPAREL",
    "apparel":            "APPAREL",
    "advocate":           "ADVOCATE",
    "lawyer":             "ADVOCATE",
    "legal":              "ADVOCATE",
    "attorney":           "ADVOCATE",
    "aviation":           "AVIATION",
    "pilot":              "AVIATION",
    "automobile":         "AUTOMOBILE",
    "automotive":         "AUTOMOBILE",
    "agriculture":        "AGRICULTURE",
    "farming":            "AGRICULTURE",
}


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB client initialized at {CHROMA_DB_PATH}")
    return _client


def get_or_create_collection(name: str) -> chromadb.Collection:
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"description": COLLECTIONS.get(name, name)}
    )


def upsert_documents(
    collection_name: str,
    ids: List[str],
    documents: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]] = None,
) -> None:
    collection = get_or_create_collection(collection_name)
    if metadatas is None:
        metadatas = [{} for _ in ids]
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    logger.info(f"Upserted {len(ids)} docs into '{collection_name}'")


def resolve_category(target_role: str) -> Optional[str]:
    """Map a free-text role string to a Kaggle category label."""
    if not target_role:
        return None
    role_lower = target_role.lower()
    for keyword, category in ROLE_CATEGORY_MAP.items():
        if keyword in role_lower:
            logger.info(f"Role '{target_role}' -> category '{category}'")
            return category
    logger.info(f"No category match for '{target_role}', using unfiltered")
    return None


def _query(
    collection_name: str,
    query_embedding: List[float],
    n_results: int,
    where: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Query a collection with optional metadata filter and automatic unfiltered fallback."""
    collection = get_or_create_collection(collection_name)
    count = collection.count()
    if count == 0:
        logger.warning(f"Collection '{collection_name}' is empty")
        return []
    n = min(n_results, count)
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.warning(f"Filtered query on '{collection_name}' failed ({e}), retrying unfiltered")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
    retrieved = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            retrieved.append({
                "document": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })
    # Retry unfiltered if filter returned nothing
    if not retrieved and where:
        logger.info(f"No results with filter on '{collection_name}', retrying unfiltered")
        return _query(collection_name, query_embedding, n_results, where=None)
    return retrieved


def query_all_collections(
    query_embedding: List[float],
    target_role: Optional[str] = None,
    n_results_per_collection: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Query all 5 collections and return combined results.
    - resume_examples  : filtered by resolved Kaggle category
    - job_requirements : unfiltered (role diversity is useful)
    - ner_profiles     : unfiltered, 2 results (small collection)
    - ats_rules        : unfiltered, 3 results (rules are universal)
    - skills_taxonomy  : unfiltered, 2 results
    """
    category = resolve_category(target_role) if target_role else None
    results = {}

    results["resume_examples"] = _query(
        "resume_examples", query_embedding, n_results_per_collection,
        where={"category": category} if category else None,
    )
    results["job_requirements"] = _query(
        "job_requirements", query_embedding, n_results_per_collection,
    )
    results["ner_profiles"] = _query(
        "ner_profiles", query_embedding, n_results=2,
    )
    results["ats_rules"] = _query(
        "ats_rules", query_embedding, n_results=3,
    )
    results["skills_taxonomy"] = _query(
        "skills_taxonomy", query_embedding, n_results=2,
    )

    total = sum(len(v) for v in results.values())
    logger.info(f"RAG retrieved {total} chunks across 5 collections (category={category or 'any'})")
    return results


def get_collection_count(collection_name: str) -> int:
    return get_or_create_collection(collection_name).count()


def is_knowledge_base_ready() -> bool:
    """All 5 collections must have at least 1 document."""
    for name in COLLECTIONS:
        if get_collection_count(name) == 0:
            logger.warning(f"Collection '{name}' is empty — run scripts/ingest_datasets.py")
            return False
    return True