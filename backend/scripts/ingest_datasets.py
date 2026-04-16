import sys
import os
import re
import json
import argparse
import logging

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedder import embed_texts
from services.vector_store import (
    upsert_documents,
    get_collection_count,
    get_client,
    COLLECTIONS,
    KAGGLE_CATEGORIES,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MIN_CHUNK_LEN = 80
MAX_CHUNK_LEN = 1500
UPSERT_BATCH  = 500


# ─── Shared helpers ───────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x20-\x7E]", " ", text)
    return text.strip()


def embed_and_upsert(collection_name: str, chunks: list, batch_size: int):
    """Embed chunk dicts and upsert into ChromaDB in batches."""
    if not chunks:
        logger.warning(f"No chunks to upsert for '{collection_name}'")
        return

    texts = [c["document"] for c in chunks]
    logger.info(f"  Embedding {len(texts)} chunks...")
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        all_embeddings.extend(embed_texts(batch))
        logger.info(f"    {min(i + batch_size, len(texts))}/{len(texts)} embedded")

    for i in range(0, len(chunks), UPSERT_BATCH):
        batch_chunks = chunks[i: i + UPSERT_BATCH]
        batch_emb    = all_embeddings[i: i + UPSERT_BATCH]
        upsert_documents(
            collection_name,
            ids=[c["id"] for c in batch_chunks],
            documents=[c["document"] for c in batch_chunks],
            embeddings=batch_emb,
            metadatas=[c["metadata"] for c in batch_chunks],
        )
        logger.info(f"    {min(i + UPSERT_BATCH, len(chunks))}/{len(chunks)} upserted")

    logger.info(f"  '{collection_name}': {get_collection_count(collection_name)} total docs")


def reset_collections():
    client = get_client()
    for name in COLLECTIONS:
        try:
            client.delete_collection(name)
            logger.info(f"Dropped '{name}'")
        except Exception:
            pass


# ─── Dataset 1: Resume.csv -> resume_examples ────────────────────────────────

SECTION_PATTERNS = {
    "summary": re.compile(
        r"(summary|objective|profile|about me|professional summary|career objective)",
        re.IGNORECASE
    ),
    "skills": re.compile(
        r"(skills|technical skills|core competencies|competencies|expertise|technologies)",
        re.IGNORECASE
    ),
    "experience": re.compile(
        r"(experience|work experience|employment|work history|professional experience)",
        re.IGNORECASE
    ),
    "education": re.compile(
        r"(education|academic|qualifications|degrees|certifications|training)",
        re.IGNORECASE
    ),
}

ANY_HEADER = re.compile(
    r"\b(summary|objective|profile|about me|professional summary|career objective"
    r"|skills|technical skills|core competencies|competencies|expertise|technologies"
    r"|experience|work experience|employment|work history|professional experience"
    r"|education|academic|qualifications|degrees|certifications|training"
    r"|accomplishments|achievements|projects|awards|publications|highlights)\b",
    re.IGNORECASE
)


def extract_section(text: str, pattern: re.Pattern) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    start  = match.end()
    next_h = ANY_HEADER.search(text, start + 10)
    end    = next_h.start() if next_h else start + MAX_CHUNK_LEN
    return text[start:end].strip()[:MAX_CHUNK_LEN]


def chunk_resume(resume_id, category: str, raw_text: str) -> list:
    text = clean_text(raw_text)
    if len(text) < MIN_CHUNK_LEN:
        return []
    chunks = []
    # Full-text chunk
    chunks.append({
        "id": f"res_{resume_id}_full",
        "document": text[:MAX_CHUNK_LEN],
        "metadata": {"category": category, "chunk_type": "full_text", "resume_id": str(resume_id)},
    })
    # Section chunks
    for chunk_type, pattern in SECTION_PATTERNS.items():
        section = extract_section(text, pattern)
        if len(section) >= MIN_CHUNK_LEN:
            chunks.append({
                "id": f"res_{resume_id}_{chunk_type}",
                "document": section,
                "metadata": {"category": category, "chunk_type": chunk_type, "resume_id": str(resume_id)},
            })
    return chunks


def ingest_resumes(csv_path: str, limit_per_category: int, batch_size: int):
    logger.info("=" * 55)
    logger.info("Dataset 1: Resume.csv -> resume_examples")
    logger.info("=" * 55)

    df = pd.read_csv(csv_path, usecols=["ID", "Resume_str", "Category"])
    df = df.dropna(subset=["Resume_str", "Category"])
    df["Category"] = df["Category"].str.strip().str.upper()
    df = df[df["Category"].isin(KAGGLE_CATEGORIES)]
    logger.info(f"Loaded {len(df)} resumes across {df['Category'].nunique()} categories")

    if limit_per_category and limit_per_category > 0:
        df = (
            df.groupby("Category", group_keys=False)
            .apply(lambda g: g.sample(min(len(g), limit_per_category), random_state=42))
            .reset_index(drop=True)
        )
        logger.info(f"Sampled to {len(df)} resumes ({limit_per_category}/category)")

    logger.info("Chunking resumes by section...")
    all_chunks = []
    for _, row in df.iterrows():
        all_chunks.extend(chunk_resume(row["ID"], row["Category"], row["Resume_str"]))

    logger.info(f"Total chunks: {len(all_chunks)}")
    embed_and_upsert("resume_examples", all_chunks, batch_size)

    logger.info("Per-category breakdown:")
    for cat, cnt in df["Category"].value_counts().items():
        logger.info(f"  {cat:<30} {cnt} resumes")


# ─── Dataset 2: training_data.csv -> job_requirements ────────────────────────

def ingest_job_requirements(csv_path: str, batch_size: int):
    logger.info("=" * 55)
    logger.info("Dataset 2: training_data.csv -> job_requirements")
    logger.info("=" * 55)

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["job_description", "model_response"])
    logger.info(f"Loaded {len(df)} job descriptions")

    chunks = []
    for idx, row in df.iterrows():
        jd_text  = clean_text(str(row["job_description"]))
        position = clean_text(str(row.get("position_title", "")))
        company  = clean_text(str(row.get("company_name", "")))

        # Parse model_response JSON
        try:
            parsed      = json.loads(re.sub(r"```json|```", "", str(row["model_response"]).strip()))
            req_skills  = clean_text(parsed.get("Required Skills", ""))
            pref_quals  = clean_text(parsed.get("Preferred Qualifications", ""))
            edu_req     = clean_text(parsed.get("Educational Requirements", ""))
            exp_level   = clean_text(parsed.get("Experience Level", ""))
            core_resp   = clean_text(parsed.get("Core Responsibilities", ""))
        except Exception:
            req_skills = pref_quals = edu_req = exp_level = core_resp = ""

        # Chunk 1: Full JD
        if len(jd_text) >= MIN_CHUNK_LEN:
            chunks.append({
                "id": f"jd_{idx}_full",
                "document": jd_text[:MAX_CHUNK_LEN],
                "metadata": {"position": position, "company": company, "chunk_type": "full_jd"},
            })

        # Chunk 2: Structured requirements (most useful for skills gap)
        parts = []
        if position:   parts.append(f"Role: {position}")
        if req_skills: parts.append(f"Required Skills: {req_skills}")
        if pref_quals: parts.append(f"Preferred Qualifications: {pref_quals}")
        if edu_req:    parts.append(f"Education: {edu_req}")
        if exp_level:  parts.append(f"Experience: {exp_level}")
        if core_resp:  parts.append(f"Responsibilities: {core_resp[:400]}")

        structured = " | ".join(parts)
        if len(structured) >= MIN_CHUNK_LEN:
            chunks.append({
                "id": f"jd_{idx}_structured",
                "document": structured[:MAX_CHUNK_LEN],
                "metadata": {"position": position, "company": company, "chunk_type": "structured_requirements"},
            })

    logger.info(f"Total chunks: {len(chunks)}")
    embed_and_upsert("job_requirements", chunks, batch_size)


# ─── Dataset 3: train_data.json -> ner_profiles ───────────────────────────────

def ingest_ner_profiles(json_path: str, batch_size: int):
    logger.info("=" * 55)
    logger.info("Dataset 3: train_data.json -> ner_profiles")
    logger.info("=" * 55)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} NER-tagged resumes")

    chunks = []
    for idx, item in enumerate(data):
        text     = item.get("text", "")
        entities = item.get("entities", [])

        entity_map: dict = {}
        for start, end, label in entities:
            val = clean_text(text[start:end])
            if val:
                entity_map.setdefault(label, []).append(val)

        # Build structured profile from NER entities
        parts = []
        if entity_map.get("NAME"):
            parts.append(f"Candidate: {entity_map['NAME'][0]}")
        if entity_map.get("DESIGNATION"):
            desigs = list(dict.fromkeys(entity_map["DESIGNATION"]))
            parts.append(f"Designations: {', '.join(desigs[:5])}")
        if entity_map.get("SKILLS"):
            raw = " | ".join(entity_map["SKILLS"])
            tokens = re.split(r"[,•\n|]+", raw)
            tokens = [s.strip() for s in tokens if 2 < len(s.strip()) < 60]
            tokens = list(dict.fromkeys(tokens))[:40]
            if tokens:
                parts.append(f"Skills: {', '.join(tokens)}")
        if entity_map.get("COMPANIES_WORKED_AT"):
            cos = list(dict.fromkeys(entity_map["COMPANIES_WORKED_AT"]))
            parts.append(f"Companies: {', '.join(cos[:5])}")
        if entity_map.get("DEGREE"):
            degs = list(dict.fromkeys(entity_map["DEGREE"]))
            parts.append(f"Degrees: {', '.join(degs[:3])}")
        if entity_map.get("YEARS_OF_EXPERIENCE"):
            parts.append(f"Experience: {entity_map['YEARS_OF_EXPERIENCE'][0]}")

        profile_text = " | ".join(parts)
        full_text    = clean_text(text)

        if len(profile_text) >= MIN_CHUNK_LEN:
            chunks.append({
                "id": f"ner_{idx}_profile",
                "document": profile_text[:MAX_CHUNK_LEN],
                "metadata": {"chunk_type": "ner_profile", "resume_idx": str(idx)},
            })
        if len(full_text) >= MIN_CHUNK_LEN:
            chunks.append({
                "id": f"ner_{idx}_full",
                "document": full_text[:MAX_CHUNK_LEN],
                "metadata": {"chunk_type": "full_text", "resume_idx": str(idx)},
            })

    logger.info(f"Total chunks: {len(chunks)}")
    embed_and_upsert("ner_profiles", chunks, batch_size)


# ─── JSON 1: ats_rules.json -> ats_rules ─────────────────────────────────────

def ingest_ats_rules(kb_dir: str, batch_size: int):
    logger.info("=" * 55)
    logger.info("JSON 1: ats_rules.json -> ats_rules")
    logger.info("=" * 55)

    path = os.path.join(kb_dir, "ats_rules.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} ATS rules")

    chunks = []
    for item in data:
        # Enrich document with title + severity for better embedding signal
        doc = f"[{item['severity'].upper()}] {item['title']}: {item['content']}"
        chunks.append({
            "id": item["id"],
            "document": doc,
            "metadata": {
                "category": item.get("category", ""),
                "title":    item["title"],
                "severity": item.get("severity", ""),
            },
        })

    embed_and_upsert("ats_rules", chunks, batch_size)


# ─── JSON 2: skills_taxonomy.json -> skills_taxonomy ─────────────────────────

def ingest_skills_taxonomy(kb_dir: str, batch_size: int):
    logger.info("=" * 55)
    logger.info("JSON 2: skills_taxonomy.json -> skills_taxonomy")
    logger.info("=" * 55)

    path = os.path.join(kb_dir, "skills_taxonomy.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} skill domains")

    chunks = []
    for item in data:
        related = ", ".join(item.get("related_roles", []))
        doc = f"{item['title']} (Roles: {related}): {item['content']}"
        chunks.append({
            "id": item["id"],
            "document": doc,
            "metadata": {
                "domain":         item.get("domain", ""),
                "title":          item["title"],
                "related_roles":  related,
            },
        })

    embed_and_upsert("skills_taxonomy", chunks, batch_size)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Ingest all 5 knowledge sources into ChromaDB")
    parser.add_argument("--resume", required=True,  help="Path to Resume.csv")
    parser.add_argument("--jobs",   required=True,  help="Path to training_data.csv")
    parser.add_argument("--ner",    required=True,  help="Path to train_data.json")
    parser.add_argument("--kb",     required=True,
                        help="Path to knowledge_base/ folder (containing ats_rules.json and skills_taxonomy.json)")
    parser.add_argument("--limit",  type=int, default=100,
                        help="Max resumes per category for Resume.csv (default 100, 0 = all)")
    parser.add_argument("--reset",  action="store_true",
                        help="Drop all collections before ingesting")
    parser.add_argument("--batch",  type=int, default=64,
                        help="Embedding batch size (default 64)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Validate all paths
    checks = [
        (args.resume, "Resume.csv"),
        (args.jobs,   "training_data.csv"),
        (args.ner,    "train_data.json"),
        (os.path.join(args.kb, "ats_rules.json"),      "ats_rules.json"),
        (os.path.join(args.kb, "skills_taxonomy.json"), "skills_taxonomy.json"),
    ]
    for path, label in checks:
        if not os.path.isfile(path):
            logger.error(f"{label} not found at: {path}")
            sys.exit(1)

    if args.reset:
        reset_collections()

    logger.info("=" * 55)
    logger.info("ResumeIQ — Full Knowledge Base Ingestion")
    logger.info("=" * 55)

    ingest_resumes(args.resume, args.limit, args.batch)
    ingest_job_requirements(args.jobs, args.batch)
    ingest_ner_profiles(args.ner, args.batch)
    ingest_ats_rules(args.kb, args.batch)
    ingest_skills_taxonomy(args.kb, args.batch)

    logger.info("=" * 55)
    logger.info("All 5 collections ingested successfully!")
    for name in COLLECTIONS:
        count = get_collection_count(name)
        logger.info(f"  {name:<25} {count} docs")
    logger.info("")
    logger.info("Run: uvicorn main:app --reload --port 8000")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()