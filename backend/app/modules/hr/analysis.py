"""HR Analysis: Skill extraction, JD matching, and candidate scoring.

All computation is deterministic — no LLM. Same principle as inventory analysis.
"""
from __future__ import annotations

import re

# ──────────────────────────────────────────────────────────────────────────────
# Skill Taxonomy (pharma industry focus)
# ──────────────────────────────────────────────────────────────────────────────

SKILL_SYNONYMS: dict[str, str] = {
    "ms excel": "excel",
    "microsoft excel": "excel",
    "ms word": "word",
    "microsoft word": "word",
    "ms office": "ms office",
    "powerpoint": "ms office",
    "ppt": "ms office",
    "sql server": "sql",
    "mysql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "python3": "python",
    "py": "python",
    "data analysis": "data analysis",
    "data analytics": "data analysis",
    "communication skills": "communication",
    "verbal communication": "communication",
    "written communication": "communication",
    "team work": "teamwork",
    "team player": "teamwork",
    "team management": "team management",
    "leadership skills": "leadership",
    "project management": "project management",
    "pharma sales": "pharma sales",
    "pharmaceutical sales": "pharma sales",
    "medical representative": "medical rep",
    "mr": "medical rep",
    "drug regulatory": "regulatory",
    "regulatory affairs": "regulatory",
    "good manufacturing practices": "gmp",
    "quality control": "qc",
    "quality assurance": "qa",
    "supply chain": "supply chain management",
    "scm": "supply chain management",
    "inventory management": "inventory management",
    "erp": "erp",
    "sap": "erp",
    "tally": "tally",
    "gst": "gst",
    "accounts": "accounting",
    "accounting": "accounting",
    "b.pharm": "b.pharm",
    "b pharma": "b.pharm",
    "m.pharm": "m.pharm",
    "d.pharm": "d.pharm",
    "mba": "mba",
    "bba": "bba",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill string to its canonical form."""
    s = skill.strip().lower()
    s = re.sub(r'[^a-z0-9\s.]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return SKILL_SYNONYMS.get(s, s)


def extract_skills(skills_text: str) -> list[str]:
    """Extract and normalize skills from a comma-separated skills string.

    Input: "Python, MS Excel, SQL, Communication Skills, pharma sales"
    Output: ["python", "excel", "sql", "communication", "pharma sales"]
    """
    if not skills_text or not isinstance(skills_text, str):
        return []

    raw_skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    normalized = list(dict.fromkeys(normalize_skill(s) for s in raw_skills))  # dedup, preserve order
    return [s for s in normalized if s]


def match_jd(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
    candidate_experience: float = 0,
    min_experience: int = 0,
) -> dict:
    """Score a candidate against a job description.

    Scoring formula (deterministic):
    - Required skill match: 60% weight (each matched skill = equal fraction)
    - Preferred skill match: 20% weight
    - Experience match: 20% weight (capped at 2x min requirement)

    Returns:
        {
            "fit_score": 0-100,
            "required_matched": [...],
            "required_missing": [...],
            "preferred_matched": [...],
            "experience_score": 0-100,
            "tier": "Strong" | "Moderate" | "Weak"
        }
    """
    preferred_skills = preferred_skills or []

    # Normalize everything
    cand_set = set(normalize_skill(s) for s in candidate_skills)
    req_set = set(normalize_skill(s) for s in required_skills)
    pref_set = set(normalize_skill(s) for s in preferred_skills)

    # Required skills match (60% weight)
    req_matched = cand_set & req_set
    req_missing = req_set - cand_set
    req_score = (len(req_matched) / len(req_set) * 100) if req_set else 100

    # Preferred skills match (20% weight)
    pref_matched = cand_set & pref_set
    pref_score = (len(pref_matched) / len(pref_set) * 100) if pref_set else 50

    # Experience score (20% weight)
    if min_experience > 0:
        exp_ratio = min(candidate_experience / min_experience, 2.0)  # cap at 2x
        exp_score = min(exp_ratio * 50, 100)  # 1x = 50, 2x = 100
    else:
        exp_score = 50 if candidate_experience > 0 else 25

    # Composite score
    fit_score = round(req_score * 0.60 + pref_score * 0.20 + exp_score * 0.20)
    fit_score = max(0, min(100, fit_score))

    # Tier assignment
    if fit_score >= 70:
        tier = "Strong"
    elif fit_score >= 45:
        tier = "Moderate"
    else:
        tier = "Weak"

    return {
        "fit_score": fit_score,
        "required_matched": sorted(req_matched),
        "required_missing": sorted(req_missing),
        "preferred_matched": sorted(pref_matched),
        "experience_score": round(exp_score),
        "tier": tier,
    }


def rank_candidates(candidates: list[dict]) -> list[dict]:
    """Rank candidates by fit score (descending). Assigns rank 1, 2, 3...

    Each candidate dict must have 'fit_score' key.
    Returns the same list sorted and with 'rank' added.
    """
    sorted_candidates = sorted(candidates, key=lambda c: c["fit_score"], reverse=True)
    for i, c in enumerate(sorted_candidates, 1):
        c["rank"] = i
    return sorted_candidates
