"""
Lightweight section detection for resumes.
Splits raw resume text into sections based on common resume headers.
Not perfect NLP segmentation — a fast heuristic that's good enough for
section-weighted scoring.
"""
import re
from typing import Dict

SECTION_HEADERS = {
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "projects": ["projects", "personal projects", "academic projects"],
    "education": ["education", "academic background"],
    "achievements": ["achievements", "awards", "honors", "certifications"],
    "summary": ["summary", "objective", "profile"],
}


def split_into_sections(text: str) -> Dict[str, str]:
    lines = text.split("\n")
    sections: Dict[str, list] = {"other": []}
    current = "other"

    header_lookup = {}
    for canonical, variants in SECTION_HEADERS.items():
        for v in variants:
            header_lookup[v] = canonical

    for line in lines:
        stripped = line.strip()
        normalized = re.sub(r"[^a-z ]", "", stripped.lower()).strip()
        if normalized in header_lookup:
            current = header_lookup[normalized]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}
