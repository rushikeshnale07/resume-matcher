"""
Ontology engine: loads the skill taxonomy and provides matching utilities
- exact match, synonym match, and related/adjacent-skill (partial) match.
"""
import json
import os
import re
from typing import Dict, List, Set, Tuple


class SkillOntology:
    def __init__(self, ontology_path: str = None):
        if ontology_path is None:
            ontology_path = os.path.join(os.path.dirname(__file__), "skills_ontology.json")
        with open(ontology_path, "r") as f:
            raw = json.load(f)

        # Flatten into: skill_name -> {synonyms, related, category}
        self.skills: Dict[str, Dict] = {}
        # lookup: any surface form (lowercased) -> canonical skill name
        self.surface_to_canonical: Dict[str, str] = {}

        for category, payload in raw["categories"].items():
            for skill_name, meta in payload["skills"].items():
                self.skills[skill_name] = {
                    "synonyms": meta.get("synonyms", []),
                    "related": meta.get("related", []),
                    "category": category,
                }
                self.surface_to_canonical[skill_name.lower()] = skill_name
                for syn in meta.get("synonyms", []):
                    self.surface_to_canonical[syn.lower()] = skill_name

        # Sort surface forms by length desc so multi-word skills match before substrings
        self._surface_forms_sorted = sorted(
            self.surface_to_canonical.keys(), key=len, reverse=True
        )

    def all_canonical_skills(self) -> List[str]:
        return list(self.skills.keys())

    def extract_skills(self, text: str) -> Set[str]:
        """Extract canonical skill names present in a block of text via phrase matching."""
        text_lower = " " + re.sub(r"[^a-z0-9+.# ]", " ", text.lower()) + " "
        found = set()
        for surface in self._surface_forms_sorted:
            # word-boundary-ish match, tolerant of +, #, . in skill names (C++, C#, Node.js)
            pattern = r"(?<![a-z0-9])" + re.escape(surface) + r"(?![a-z0-9])"
            if re.search(pattern, text_lower):
                found.add(self.surface_to_canonical[surface])
        return found

    def related_skills(self, skill: str) -> Set[str]:
        return set(self.skills.get(skill, {}).get("related", []))

    def compare_skill_sets(
        self, resume_skills: Set[str], jd_skills: Set[str]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Returns (matched, partial_match, missing) skills from the JD's perspective.
        - matched: JD skill directly present in resume
        - partial_match: JD skill not present, but a related/adjacent skill is
        - missing: JD skill not present and no related skill present either
        """
        matched, partial, missing = [], [], []
        for skill in jd_skills:
            if skill in resume_skills:
                matched.append(skill)
                continue
            related = self.related_skills(skill)
            # also check reverse: does resume have a skill that lists this JD skill as related?
            reverse_related = {
                s for s in resume_skills if skill in self.related_skills(s)
            }
            if related & resume_skills or reverse_related:
                partial.append(skill)
            else:
                missing.append(skill)
        return matched, partial, missing
