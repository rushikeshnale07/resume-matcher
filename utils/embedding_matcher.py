"""
Embedding-based semantic similarity between resume and JD.
Uses Sentence-Transformers (MiniLM by default — fast, CPU-friendly).
"""
from functools import lru_cache
import numpy as np


@lru_cache(maxsize=1)
def _get_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-8)
    b = b / (np.linalg.norm(b) + 1e-8)
    return float(np.dot(a, b))


def semantic_similarity(text_a: str, text_b: str, model_name: str = None) -> float:
    model = _get_model(model_name) if model_name else _get_model()
    embeddings = model.encode([text_a, text_b])
    return cosine_sim(embeddings[0], embeddings[1])


def section_weighted_similarity(resume_sections: dict, jd_text: str, weights: dict = None) -> dict:
    """
    Computes similarity per resume section against the JD, plus a weighted overall score.
    Returns dict of {section: similarity} plus 'overall'.
    """
    default_weights = {
        "skills": 1.3,
        "experience": 1.3,
        "projects": 1.1,
        "summary": 0.9,
        "education": 0.7,
        "achievements": 0.8,
        "other": 0.6,
    }
    weights = weights or default_weights
    model = _get_model()

    jd_emb = model.encode([jd_text])[0]

    per_section = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for section, text in resume_sections.items():
        if not text.strip():
            continue
        emb = model.encode([text])[0]
        sim = cosine_sim(emb, jd_emb)
        per_section[section] = sim
        w = weights.get(section, 0.6)
        weighted_sum += sim * w
        weight_total += w

    overall = weighted_sum / weight_total if weight_total > 0 else 0.0
    per_section["overall"] = overall
    return per_section
