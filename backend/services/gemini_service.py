from google import genai
from google.genai import types
import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set in environment variables")

# Singleton Gemini client
_gemini_client: Optional[genai.Client] = None


def get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured. Set it in your .env file.")
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini client initialised")
    return _gemini_client


def _parse_json_response(raw: str) -> Dict[str, Any]:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw).strip()
    return json.loads(raw)


# ─── Role detection ───────────────────────────────────────────────────────────

async def detect_target_role(resume_snippet: str) -> str:
    """
    Lightweight Gemini call to extract the candidate's target role.
    Used to filter ChromaDB resume_examples by category before full analysis.
    """
    client = get_gemini_client()
    prompt = (
        "Read the following resume snippet and return ONLY the candidate's most likely "
        "target job role as a short phrase (2-4 words max). "
        "Examples: 'Software Engineer', 'Financial Analyst', 'HR Manager', 'Sales Executive'. "
        "Return nothing else — just the role phrase.\n\n"
        f"RESUME:\n{resume_snippet[:1500]}"
    )
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=20),
        )
        role = response.text.strip().strip('"').strip("'")
        return role if role else "General"
    except Exception as e:
        logger.warning(f"Role detection failed: {e} — defaulting to 'General'")
        return "General"


# ─── RAG context builder ──────────────────────────────────────────────────────

def build_rag_context(retrieved_docs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Format retrieved chunks from all 5 collections into a single context block."""
    section_labels = {
        "resume_examples":  "SIMILAR RESUME EXAMPLES (same job category)",
        "job_requirements": "JOB REQUIREMENTS & EXPECTED SKILLS (from real job postings)",
        "ner_profiles":     "CANDIDATE SKILL PROFILES (NER-extracted entities)",
        "ats_rules":        "ATS COMPATIBILITY RULES",
        "skills_taxonomy":  "SKILLS TAXONOMY & DOMAIN KNOWLEDGE",
    }
    parts = []
    for collection_name, docs in retrieved_docs.items():
        if not docs:
            continue
        label = section_labels.get(collection_name, collection_name.upper())
        parts.append(f"--- {label} ---")
        for doc in docs:
            meta  = doc.get("metadata", {})
            if collection_name == "resume_examples":
                cat   = meta.get("category", "")
                ctype = meta.get("chunk_type", "")
                parts.append(f"[{cat} | {ctype}] {doc['document']}")
            elif collection_name == "job_requirements":
                pos   = meta.get("position", "")
                ctype = meta.get("chunk_type", "")
                parts.append(f"[{pos} | {ctype}] {doc['document']}")
            elif collection_name == "ats_rules":
                sev   = meta.get("severity", "")
                title = meta.get("title", "")
                parts.append(f"[{sev.upper()}] {title}: {doc['document']}")
            elif collection_name == "skills_taxonomy":
                domain = meta.get("domain", "")
                parts.append(f"[{domain}] {doc['document']}")
            else:
                parts.append(doc["document"])
        parts.append("")
    return "\n".join(parts)


# ─── Full analysis ────────────────────────────────────────────────────────────

def build_analysis_prompt(
    resume_text: str,
    job_description: str,
    rag_context: str,
    target_role: str,
) -> str:
    return f"""You are an expert resume analyst and career coach with 15+ years of experience \
reviewing thousands of resumes across all industries. You have deep knowledge of ATS systems, \
hiring practices, and industry-specific skill requirements.

DETECTED TARGET ROLE: {target_role}

KNOWLEDGE BASE CONTEXT (use this to ground your analysis — it contains real resume examples, \
job requirements, ATS rules, and skills taxonomy relevant to this candidate):
{rag_context if rag_context.strip() else "No context available. Use your expert knowledge."}

---

RESUME TO ANALYSE:
{resume_text}

---

JOB DESCRIPTION:
{job_description if job_description.strip() else "No job description provided. Perform general analysis."}

---

TASK: Perform a comprehensive resume analysis and return ONLY a valid JSON object \
(no markdown, no explanation, just raw JSON).

The JSON must follow this exact schema:
{{
  "overall_score": <integer 0-100>,
  "ats_score": <integer 0-100>,
  "candidate_name": "<extracted name or Unknown>",
  "target_role": "<detected or inferred target role>",
  "years_of_experience": "<estimated years>",
  "section_feedback": {{
    "summary":        {{"score": <int>, "exists": <bool>, "feedback": "<text>", "improvements": ["<text>"]}},
    "experience":     {{"score": <int>, "exists": <bool>, "feedback": "<text>", "improvements": ["<text>"]}},
    "education":      {{"score": <int>, "exists": <bool>, "feedback": "<text>", "improvements": ["<text>"]}},
    "skills":         {{"score": <int>, "exists": <bool>, "feedback": "<text>", "improvements": ["<text>"]}},
    "projects":       {{"score": <int>, "exists": <bool>, "feedback": "<text>", "improvements": ["<text>"]}},
    "certifications": {{"score": <int>, "exists": <bool>, "feedback": "<text>", "improvements": ["<text>"]}}
  }},
  "skills_gap": {{
    "matched_skills":    ["<skill>"],
    "missing_skills":    ["<skill>"],
    "bonus_skills":      ["<skill>"],
    "match_percentage":  <int 0-100>
  }},
  "ats_report": {{
    "passed_checks":         ["<text>"],
    "failed_checks":         ["<text>"],
    "warnings":              ["<text>"],
    "keyword_match_score":   <int 0-100>,
    "top_missing_keywords":  ["<keyword>"]
  }},
  "top_recommendations": [
    {{"priority": "high",   "category": "<text>", "recommendation": "<text>"}},
    {{"priority": "medium", "category": "<text>", "recommendation": "<text>"}},
    {{"priority": "low",    "category": "<text>", "recommendation": "<text>"}}
  ],
  "strengths": ["<text>"],
  "summary_verdict": "<2-3 sentence verdict>"
}}

Return ONLY the JSON. No markdown, no explanation."""


async def analyse_resume(
    resume_text: str,
    job_description: str,
    rag_context: str,
    target_role: str = "General",
) -> Dict[str, Any]:
    client = get_gemini_client()
    prompt = build_analysis_prompt(resume_text, job_description, rag_context, target_role)
    try:
        logger.info(f"Sending full analysis to Gemini ({GEMINI_MODEL})...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4096),
        )
        analysis = _parse_json_response(response.text)
        logger.info(f"Analysis complete. Overall score: {analysis.get('overall_score', 'N/A')}")
        return analysis
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON: {e}")
        raise ValueError("AI returned invalid JSON. Please try again.")
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise ValueError(f"AI analysis failed: {str(e)}")