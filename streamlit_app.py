import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from app.scoring_engine import build_match_report, score_label
from utils.text_extraction import extract_text
from utils.llm_suggestions import generate_suggestions

st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .score-card {
        background: linear-gradient(135deg, #1a1c24 0%, #23262f 100%);
        border-radius: 16px;
        padding: 28px;
        text-align: center;
        border: 1px solid #2d3039;
    }
    .score-number {
        font-size: 56px;
        font-weight: 800;
        margin: 0;
    }
    .score-label {
        font-size: 16px;
        color: #9aa0ab;
        margin-top: 4px;
    }
    .pill {
        display: inline-block;
        padding: 5px 12px;
        margin: 4px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }
    .pill-matched { background-color: rgba(46, 204, 113, 0.15); color: #2ecc71; border: 1px solid rgba(46, 204, 113, 0.35); }
    .pill-partial { background-color: rgba(241, 196, 15, 0.15); color: #f1c40f; border: 1px solid rgba(241, 196, 15, 0.35); }
    .pill-missing { background-color: rgba(231, 76, 60, 0.15); color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.35); }
    .section-bar-label { font-size: 13px; color: #9aa0ab; margin-bottom: -6px; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    groq_api_key = st.text_input(
        "Groq API key (optional)",
        type="password",
        help="Only needed for AI-generated resume improvement suggestions. Get a free key at console.groq.com. Never stored — used only for this session.",
    )
    st.caption("Without a key, you still get the match score and skill-gap report — just not the AI suggestions.")

# ---------- Header ----------
st.title("🎯 AI-Powered Resume Matcher")
st.caption("Compare your resume against a job description — get a match score, semantic fit, and an ontology-based skill gap report.")

st.divider()

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📄 Resume")
    resume_file = st.file_uploader("Upload resume (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
    resume_text_input = st.text_area("...or paste resume text", height=220, placeholder="Paste resume text here if you'd rather not upload a file")

with col2:
    st.subheader("📋 Job Description")
    jd_text_input = st.text_area("Paste job description", height=280, placeholder="Paste the full job description here")

st.divider()
run = st.button("🔍 Analyze Match", type="primary", use_container_width=True)

if run:
    # Resolve resume text
    resume_text = ""
    if resume_file is not None:
        try:
            resume_text = extract_text(resume_file)
        except Exception as e:
            st.error(f"Couldn't read the resume file: {e}")
    elif resume_text_input.strip():
        resume_text = resume_text_input

    jd_text = jd_text_input

    if not resume_text.strip():
        st.warning("Please upload or paste a resume first.")
    elif not jd_text.strip():
        st.warning("Please paste a job description first.")
    else:
        with st.spinner("Embedding, matching against ontology, and scoring..."):
            report = build_match_report(resume_text, jd_text)

        # persist for the suggestions step below (separate button, separate rerun)
        st.session_state["report"] = report
        st.session_state["jd_text"] = jd_text

        label = score_label(report["final_score"])
        color = "#2ecc71" if report["final_score"] >= 65 else "#f1c40f" if report["final_score"] >= 50 else "#e74c3c"

        st.markdown("### Results")
        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            st.markdown(f"""
            <div class="score-card">
                <p class="score-number" style="color:{color};">{report['final_score']}%</p>
                <p class="score-label">{label}</p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.metric("Semantic Similarity", f"{report['semantic_score']}%",
                       help="Embedding-based contextual similarity between resume and JD, weighted by resume section (Skills/Experience weighted higher).")
        with c3:
            st.metric("Skill Coverage", f"{report['skill_coverage_score']}%",
                       help="Ontology-based: fraction of JD-required skills matched (exact or related) in the resume.")

        st.divider()

        # Skill gap breakdown
        st.markdown("### 🧩 Skill Gap Analysis")
        sc1, sc2, sc3 = st.columns(3)

        with sc1:
            st.markdown(f"**✅ Matched ({len(report['matched_skills'])})**")
            if report["matched_skills"]:
                st.markdown("".join(f'<span class="pill pill-matched">{s}</span>' for s in report["matched_skills"]), unsafe_allow_html=True)
            else:
                st.caption("None found")

        with sc2:
            st.markdown(f"**🟡 Partial / Adjacent ({len(report['partial_skills'])})**")
            if report["partial_skills"]:
                st.markdown("".join(f'<span class="pill pill-partial">{s}</span>' for s in report["partial_skills"]), unsafe_allow_html=True)
                st.caption("You have a related skill, but not this exact one.")
            else:
                st.caption("None")

        with sc3:
            st.markdown(f"**❌ Missing ({len(report['missing_skills'])})**")
            if report["missing_skills"]:
                st.markdown("".join(f'<span class="pill pill-missing">{s}</span>' for s in report["missing_skills"]), unsafe_allow_html=True)
                st.caption("Consider highlighting or upskilling here.")
            else:
                st.caption("No major gaps — great coverage!")

        st.divider()

        # Section-level similarity
        with st.expander("📊 Section-level semantic similarity"):
            for section, score in report["section_similarity"].items():
                st.markdown(f'<p class="section-bar-label">{section.title()}</p>', unsafe_allow_html=True)
                st.progress(min(1.0, score / 100), text=f"{score}%")

        with st.expander("🔎 Raw extracted skills (debug view)"):
            d1, d2 = st.columns(2)
            with d1:
                st.write("**Resume skills detected:**")
                st.write(report["resume_skills_found"] or "None")
            with d2:
                st.write("**JD skills detected:**")
                st.write(report["jd_skills_found"] or "None")

# ---------- AI Suggestions (persists across reruns via session_state) ----------
if "report" in st.session_state:
    st.divider()
    st.markdown("### 💡 AI-Powered Resume Suggestions")

    if not groq_api_key:
        st.info("Add a Groq API key in the sidebar to generate personalized resume improvement suggestions.")
    else:
        if st.button("✨ Generate Suggestions", use_container_width=True):
            with st.spinner("Asking the model for improvement suggestions..."):
                try:
                    suggestions = generate_suggestions(
                        st.session_state["report"], st.session_state["jd_text"], groq_api_key
                    )
                    st.session_state["suggestions"] = suggestions
                except Exception as e:
                    st.error(f"Couldn't generate suggestions: {e}")
                    st.session_state.pop("suggestions", None)

    if "suggestions" in st.session_state:
        s = st.session_state["suggestions"]

        if s.get("priority_gaps"):
            st.markdown("**🎯 Priority gaps to address**")
            st.markdown(", ".join(f"`{g}`" for g in s["priority_gaps"]))

        if s.get("reframe_suggestions"):
            st.markdown("**🔄 Reframe existing skills**")
            for item in s["reframe_suggestions"]:
                st.markdown(f"- **{item.get('existing_skill', '')}** → {item.get('how_to_position', '')}")

        if s.get("bullet_suggestions"):
            st.markdown("**✍️ Suggested resume bullet phrasing**")
            for b in s["bullet_suggestions"]:
                st.markdown(f"- {b}")

        if s.get("learning_priority"):
            st.markdown("**📚 What to learn next, and why**")
            for item in s["learning_priority"]:
                st.markdown(f"- **{item.get('skill', '')}**: {item.get('reason', '')}")

st.divider()
st.caption("Built with Sentence-Transformers embeddings + a curated skill ontology for explainable matching.")
