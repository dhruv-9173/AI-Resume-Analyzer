from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Optional

from services.file_parser import parse_file
from services.embedder import embed_text
from services.vector_store import (
    query_all_collections,
    is_knowledge_base_ready,
    get_collection_count,
    COLLECTIONS,
    resolve_category,
)
from services.gemini_service import analyse_resume, build_rag_context, detect_target_role

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/analyse")
async def analyse_resume_endpoint(
    resume: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description: Optional[str] = Form("", description="Job description text (optional)")
):
    """
    Analyse a resume using RAG + Gemini AI.

    Pipeline:
      1. Parse resume (PDF/DOCX) -> plain text
      2. Detect target role via lightweight Gemini call
      3. Resolve target role -> Kaggle category for filtered retrieval
      4. Embed resume text -> query all 3 ChromaDB collections
      5. Full Gemini analysis with retrieved context
    """

    # ── Validate ───────────────────────────────────────────────────────────────
    filename = resume.filename or ""
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF or DOCX file.")

    file_bytes = await resume.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(f"Processing: {filename} ({len(file_bytes)} bytes)")

    # ── Step 1: Extract text ───────────────────────────────────────────────────
    try:
        resume_text = parse_file(file_bytes, filename)
        logger.info(f"Extracted {len(resume_text)} chars from resume")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(resume_text) < 100:
        raise HTTPException(
            status_code=422,
            detail="Resume text too short. Ensure your resume has readable text content."
        )

    # ── Step 2: Detect target role ─────────────────────────────────────────────
    # Use first 1500 chars + JD hint for a fast role detection call
    role_hint_text = resume_text[:1500]
    if job_description and job_description.strip():
        role_hint_text += f"\n\nJob Description: {job_description[:500]}"

    target_role = await detect_target_role(role_hint_text)
    logger.info(f"Detected target role: '{target_role}'")

    # ── Step 3: Check KB readiness ─────────────────────────────────────────────
    if not is_knowledge_base_ready():
        logger.warning("Knowledge base not fully ingested — analysis will proceed without full RAG context")

    # ── Step 4: Embed + retrieve ───────────────────────────────────────────────
    query_text = resume_text[:2000]
    if job_description and job_description.strip():
        query_text += f" {job_description[:500]}"

    logger.info("Generating query embedding...")
    query_embedding = embed_text(query_text)

    logger.info(f"Querying ChromaDB (target_role='{target_role}')...")
    retrieved_docs = query_all_collections(
        query_embedding=query_embedding,
        target_role=target_role,
        n_results_per_collection=3,
    )

    rag_context = build_rag_context(retrieved_docs)
    total_chunks = sum(len(v) for v in retrieved_docs.values())
    logger.info(f"RAG context: {len(rag_context)} chars from {total_chunks} chunks")

    # ── Step 5: Full Gemini analysis ───────────────────────────────────────────
    logger.info("Sending to Gemini for full analysis...")
    try:
        analysis = await analyse_resume(
            resume_text=resume_text,
            job_description=job_description or "",
            rag_context=rag_context,
            target_role=target_role,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ── Step 6: Attach metadata ────────────────────────────────────────────────
    resolved_category = resolve_category(target_role)
    analysis["metadata"] = {
        "filename":                  filename,
        "resume_length":             len(resume_text),
        "rag_chunks_used":           total_chunks,
        "job_description_provided":  bool(job_description and job_description.strip()),
        "model_used":                "gemini-2.0-flash",
        "detected_role":             target_role,
        "resolved_category":         resolved_category or "general",
    }

    return JSONResponse(content=analysis)


@router.get("/health")
async def health_check():
    """Health check with per-collection KB status."""
    kb_status = {name: get_collection_count(name) for name in COLLECTIONS}
    return {
        "status":    "healthy",
        "knowledge_base": kb_status,
        "kb_ready":  all(v > 0 for v in kb_status.values()),
    }