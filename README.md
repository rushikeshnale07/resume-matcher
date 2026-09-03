# AI-Powered Resume Matcher

NLP-based app that compares a resume against a job description, producing a
match score and an explainable skill-gap report using embeddings + a
skill ontology.

## How it works

1. **Text extraction** — PDF/DOCX/TXT resume parsed via `pdfplumber` / `python-docx`.
2. **Section detection** — resume split into Skills / Experience / Projects / Education / etc.
3. **Skill extraction** — phrase-matched against `ontology/skills_ontology.json`
   (handles synonyms like "ML" = "Machine Learning").
4. **Embedding similarity** — Sentence-Transformers (MiniLM) computes semantic
   similarity per resume section vs. the JD, then combines them with
   section weights (Skills/Experience weighted highest).
5. **Ontology skill-gap analysis** — for each JD skill: exact match, partial
   match (a related/adjacent skill is present), or missing.
6. **Blended score** — `0.6 * semantic_similarity + 0.4 * skill_coverage`.

## Local setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

First run downloads the MiniLM embedding model (~90MB), then it's cached locally.

## Deploying to Streamlit Community Cloud

1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io → New app → point it at your repo,
   branch, and `streamlit_app.py` as the entry point.
3. Streamlit Cloud installs `requirements.txt` automatically. No GPU needed —
   MiniLM runs fine on CPU.

## Extending the ontology

Edit `ontology/skills_ontology.json` — add a skill under the right category with:
```json
"SkillName": {"synonyms": ["alt name"], "related": ["AdjacentSkill1", "AdjacentSkill2"]}
```
No retraining needed — it's picked up on next run.

## Project structure

```
resume-matcher/
├── streamlit_app.py          # UI entry point
├── app/
│   └── scoring_engine.py     # combines embeddings + ontology into final report
├── ontology/
│   ├── skills_ontology.json  # curated skill taxonomy
│   └── ontology_engine.py    # skill extraction + matching logic
├── utils/
│   ├── text_extraction.py    # PDF/DOCX/TXT parsing
│   ├── section_parser.py     # resume section detection
│   └── embedding_matcher.py  # Sentence-Transformers similarity
└── requirements.txt
```

## Possible next steps

- Swap MiniLM for a stronger model (e.g. `BAAI/bge-small-en-v1.5`) if you want
  better semantic quality at a similar speed.
- Add a "resume improvement suggestions" step using an LLM call, seeded with
  the missing-skills list.
- Expand the ontology using a standard taxonomy (ESCO / O*NET) for broader
  domain coverage beyond tech roles.
- Add multi-JD comparison (one resume vs. several JDs, ranked).
