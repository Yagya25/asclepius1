"""Resume Screening Agent: parse resumes, extract skills, match JD, score, rank.

Same pattern as IngestionAgent + InsightAgent:
- All computation is deterministic (no LLM)
- All recommendations are created with status='pending'
- Pipeline stops for HR manager approval
"""
import pandas as pd

from ...agents.base_agent import BaseAgent
from ...models import Dataset, JobDescription, Recommendation, ResumeScreening
from .analysis import extract_skills, match_jd, rank_candidates


class ResumeScreeningAgent(BaseAgent):
    """Agent 5: Upload Resumes → Extract Skills → Match JD → Score → Rank → Recommend."""

    def __init__(self, db):
        super().__init__("HR_RESUME_SCREENING", db)

    def run(self, dataset_id: int, file_path: str, jd_id: int) -> list[Recommendation]:
        """Run resume screening pipeline.

        Args:
            dataset_id: Dataset record for this upload.
            file_path: Path to the uploaded CSV of resumes.
            jd_id: Job Description to screen against.

        Returns:
            List of Recommendation records (all pending).
        """
        # Step 1: Load resumes
        df = pd.read_csv(file_path)
        original_count = len(df)

        self.log_action(
            dataset_id=dataset_id,
            action="RESUMES_LOADED",
            input_summary=f"File: {file_path}",
            output_summary=f"Loaded {original_count} resumes, columns: {list(df.columns)}",
        )

        # Step 2: Load JD
        jd = self.db.query(JobDescription).filter(JobDescription.id == jd_id).first()
        if not jd:
            raise ValueError(f"Job Description {jd_id} not found")

        required_skills = jd.required_skills or []
        preferred_skills = jd.preferred_skills or []
        min_exp = jd.min_experience_years or 0

        # Step 3: Detect columns
        col_map = self._detect_resume_columns(df.columns.tolist())
        name_col = col_map.get("name")
        email_col = col_map.get("email")
        skills_col = col_map.get("skills")
        exp_col = col_map.get("experience")
        edu_col = col_map.get("education")

        if not name_col or not skills_col:
            raise ValueError("Resume CSV must have at least Name and Skills columns")

        # Step 4: Extract skills and score each candidate
        candidates = []
        for _, row in df.iterrows():
            candidate_name = str(row.get(name_col, "")).strip()
            if not candidate_name or candidate_name.lower() in ("nan", "none", ""):
                continue

            raw_skills = str(row.get(skills_col, ""))
            extracted = extract_skills(raw_skills)
            experience = self._parse_experience(row.get(exp_col, 0) if exp_col else 0)
            education = str(row.get(edu_col, "")) if edu_col else ""
            email = str(row.get(email_col, "")) if email_col else ""

            match_result = match_jd(
                candidate_skills=extracted,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                candidate_experience=experience,
                min_experience=min_exp,
            )

            candidates.append({
                "name": candidate_name,
                "email": email if email.lower() not in ("nan", "none") else "",
                "skills": extracted,
                "experience": experience,
                "education": education if education.lower() not in ("nan", "none") else "",
                "fit_score": match_result["fit_score"],
                "tier": match_result["tier"],
                "required_matched": match_result["required_matched"],
                "required_missing": match_result["required_missing"],
                "preferred_matched": match_result["preferred_matched"],
            })

        self.log_action(
            dataset_id=dataset_id,
            action="SKILLS_EXTRACTED",
            input_summary=f"{len(candidates)} valid resumes processed",
            output_summary=f"Skills extracted from {len(candidates)} candidates",
        )

        # Step 5: Rank candidates
        ranked = rank_candidates(candidates)

        self.log_action(
            dataset_id=dataset_id,
            action="CANDIDATES_SCORED",
            input_summary=f"JD: {jd.title}, Required: {required_skills}, Min exp: {min_exp}y",
            output_summary=(
                f"Strong: {sum(1 for c in ranked if c['tier'] == 'Strong')}, "
                f"Moderate: {sum(1 for c in ranked if c['tier'] == 'Moderate')}, "
                f"Weak: {sum(1 for c in ranked if c['tier'] == 'Weak')}"
            ),
        )

        # Step 6: Save screening records to DB
        # Ensure idempotency by clearing any existing records for this dataset
        self.db.query(ResumeScreening).filter(ResumeScreening.dataset_id == dataset_id).delete()
        
        for c in ranked:
            screening = ResumeScreening(
                dataset_id=dataset_id,
                jd_id=jd_id,
                candidate_name=c["name"],
                email=c["email"],
                extracted_skills=c["skills"],
                experience_years=c["experience"],
                education=c["education"],
                fit_score=c["fit_score"],
                tier=c["tier"],
                rank=c["rank"],
            )
            self.db.add(screening)

        # Step 7: Generate recommendations (all pending)
        recs: list[Recommendation] = []

        # Recommend shortlisting strong candidates
        strong = [c for c in ranked if c["tier"] == "Strong"]
        if strong:
            names = ", ".join(c["name"] for c in strong[:5])
            recs.append(self._create_rec(
                dataset_id,
                f"Shortlist {len(strong)} strong candidates for {jd.title}",
                f"Top candidates: {names}. "
                f"These candidates match {len(required_skills)} required skills with fit scores above 70.",
                "shortlist", "info",
                f"{len(strong)} candidates ready for interview",
            ))

        # Warn about weak candidate pool
        weak = [c for c in ranked if c["tier"] == "Weak"]
        if len(weak) > len(ranked) * 0.5:
            recs.append(self._create_rec(
                dataset_id,
                f"Weak candidate pool: {len(weak)}/{len(ranked)} candidates scored below 45",
                f"Over half of applicants lack critical skills. Consider broadening job posting or "
                f"reducing requirements. Missing skills in most resumes: "
                f"{', '.join(ranked[0]['required_missing'][:3]) if ranked else 'N/A'}.",
                "review", "warning",
                f"{len(weak)} weak candidates out of {len(ranked)} total",
            ))

        # Highlight top candidate
        if ranked:
            top = ranked[0]
            recs.append(self._create_rec(
                dataset_id,
                f"Top candidate: {top['name']} (Fit Score: {top['fit_score']}/100)",
                f"Matched skills: {', '.join(top['required_matched'])}. "
                f"Experience: {top['experience']}y. Education: {top['education']}. "
                f"Missing: {', '.join(top['required_missing']) or 'None'}.",
                "shortlist", "info",
                f"Rank #1 candidate with {top['fit_score']}% fit",
            ))

        # Flag candidates missing critical skills
        critical_missing = [c for c in ranked if len(c["required_missing"]) > len(required_skills) * 0.6]
        if critical_missing and len(critical_missing) < len(ranked):
            recs.append(self._create_rec(
                dataset_id,
                f"{len(critical_missing)} candidates missing >60% of required skills",
                "Consider auto-rejecting these candidates to save interview time.",
                "reject", "info",
                f"{len(critical_missing)} candidates below skill threshold",
            ))

        # Update dataset
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        dataset.status = "analyzed"
        dataset.row_count = len(ranked)
        dataset.analysis_summary = {
            "total_candidates": len(ranked),
            "strong": len(strong),
            "moderate": sum(1 for c in ranked if c["tier"] == "Moderate"),
            "weak": len(weak),
            "top_candidate": ranked[0]["name"] if ranked else None,
            "avg_fit_score": round(sum(c["fit_score"] for c in ranked) / len(ranked), 1) if ranked else 0,
        }

        self.db.commit()

        self.log_action(
            dataset_id=dataset_id,
            action="SHORTLIST_GENERATED",
            input_summary=f"{len(ranked)} candidates scored",
            output_summary=f"Generated {len(recs)} recommendations. ALL pending HR manager approval.",
            human_checkpoint=True,
        )

        return recs

    def _create_rec(self, dataset_id: int, title: str, description: str,
                    action_type: str, severity: str, impact: str) -> Recommendation:
        """Create a recommendation record with status=pending."""
        rec = Recommendation(
            dataset_id=dataset_id,
            module="hr",
            agent_name="HR_RESUME_SCREENING",
            title=title,
            description=description,
            action_type=action_type,
            severity=severity,
            estimated_impact=impact,
            status="pending",
        )
        self.db.add(rec)
        return rec

    def _detect_resume_columns(self, col_names: list[str]) -> dict[str, str]:
        """Detect resume column semantics from names."""
        patterns = {
            "name": ["name", "candidate_name", "full_name", "applicant", "candidate"],
            "email": ["email", "email_address", "mail", "e_mail"],
            "skills": ["skills", "skill", "technical_skills", "key_skills", "competencies"],
            "experience": ["experience", "exp", "years", "experience_years", "work_experience", "years_of_experience"],
            "education": ["education", "degree", "qualification", "edu", "highest_education"],
        }
        mapping: dict[str, str] = {}
        for col in col_names:
            col_lower = col.lower().replace("_", "").replace(" ", "")
            for sem_type, keywords in patterns.items():
                for kw in keywords:
                    kw_clean = kw.lower().replace("_", "").replace(" ", "")
                    if kw_clean in col_lower or col_lower in kw_clean:
                        if sem_type not in mapping:
                            mapping[sem_type] = col
                        break
        return mapping

    def _parse_experience(self, val) -> float:
        """Parse experience value from various formats."""
        if pd.isna(val) or val is None:
            return 0
        try:
            return float(val)
        except (ValueError, TypeError):
            import re
            match = re.search(r'(\d+\.?\d*)', str(val))
            return float(match.group(1)) if match else 0
