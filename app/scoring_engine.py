"""
Core scoring engine — combines:
  1. Embedding-based semantic similarity (section-weighted)
  2. Ontology-based skill gap analysis (matched / partial / missing)
into a single blended, explainable match report.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ontology.ontology_engine import SkillOntology
from utils.embedding_matcher import section_weighted_similarity
from utils.section_parser import split_into_sections

ontology = SkillOntology()


def build_match_report(resume_text: str, jd_text: str) -> dict:
    # 1. Section-aware embedding similarity
    resume_sections = split_into_sections(resume_text)
    if not resume_sections:
        resume_sections = {"other": resume_text}
    sim_report = section_weighted_similarity(resume_sections, jd_text)
    semantic_score = sim_report.pop("overall")

    # 2. Ontology-based skill extraction & gap analysis
    resume_skills = ontology.extract_skills(resume_text)
    jd_skills = ontology.extract_skills(jd_text)
    matched, partial, missing = ontology.compare_skill_sets(resume_skills, jd_skills)

    # 3. Skill coverage score: matched=1.0, partial=0.5, missing=0
    total_jd_skills = len(jd_skills) or 1
    skill_coverage = (len(matched) * 1.0 + len(partial) * 0.5) / total_jd_skills

    # 4. Blended final score (60% semantic, 40% skill-coverage — semantic captures
    #    context/experience framing, skill-coverage captures hard requirements)
    final_score = 0.6 * semantic_score + 0.4 * skill_coverage
    final_score_pct = round(max(0.0, min(1.0, final_score)) * 100, 1)

    return {
        "final_score": final_score_pct,
        "semantic_score": round(semantic_score * 100, 1),
        "skill_coverage_score": round(skill_coverage * 100, 1),
        "section_similarity": {k: round(v * 100, 1) for k, v in sim_report.items()},
        "matched_skills": sorted(matched),
        "partial_skills": sorted(partial),
        "missing_skills": sorted(missing),
        "resume_skills_found": sorted(resume_skills),
        "jd_skills_found": sorted(jd_skills),
    }


def score_label(score: float) -> str:
    if score >= 80:
        return "Excellent Match"
    elif score >= 65:
        return "Strong Match"
    elif score >= 50:
        return "Moderate Match"
    elif score >= 35:
        return "Weak Match"
    else:
        return "Poor Match"
