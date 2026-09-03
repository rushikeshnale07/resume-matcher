"""
LLM-based resume improvement suggestions, seeded with the ontology skill-gap
report. Uses Groq's free-tier API (Llama 3.3) — same backend used in the
Enterprise Agentic Multimodal RAG project.
"""
import os
import json


SYSTEM_PROMPT = """You are a precise, no-fluff resume coach for technical roles \
(Data Science, MLE, Applied Scientist, AI/GenAI Engineer). You are given:
- A candidate's matched skills, partially-matched (adjacent) skills, and missing skills for a specific job description.
- The job description itself.

Give concrete, actionable suggestions. Do NOT invent experience the candidate doesn't have.
Focus on: (1) how to reframe/surface existing adjacent skills to cover gaps, \
(2) which missing skills are worth prioritizing to learn given the role, \
(3) specific resume phrasing/bullet suggestions using only what the candidate already has.

Respond ONLY in valid JSON, no markdown fences, no preamble, in this exact shape:
{
  "priority_gaps": ["skill1", "skill2"],
  "reframe_suggestions": [{"existing_skill": "...", "how_to_position": "..."}],
  "bullet_suggestions": ["...", "..."],
  "learning_priority": [{"skill": "...", "reason": "..."}]
}
"""


def _build_user_prompt(report: dict, jd_text: str) -> str:
    return f"""Job description:
{jd_text[:3000]}

Matched skills: {report['matched_skills']}
Partial/adjacent skills: {report['partial_skills']}
Missing skills: {report['missing_skills']}
Overall match score: {report['final_score']}%
"""


def generate_suggestions(report: dict, jd_text: str, api_key: str, model: str = "openai/gpt-oss-120b") -> dict:
    """
    Calls Groq's chat completions endpoint (OpenAI-compatible) to generate
    resume improvement suggestions. Raises on failure — caller should catch
    and show a friendly error in the UI.
    """
    import requests

    if not api_key:
        raise ValueError("Missing Groq API key.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(report, jd_text)},
        ],
        "temperature": 0.3,
        "max_tokens": 900,
    }

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # Strip accidental markdown fences just in case
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)
