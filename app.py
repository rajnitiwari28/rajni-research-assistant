"""Streamlit UI for the Paper-to-Presentation & Viva Agent."""

import os, tempfile, json
import streamlit as st
from dotenv import load_dotenv

from agents.word_export import create_word_file, create_viva_word
from agents.reference_extractor import extract_references
from agents.chat_agent import ask_question
from agents.slide_generator import build_pptx

from agents.rag_store import build_vectorstore
from agents.summarizer import summarize
from agents.concept_extractor import extract_concepts
from agents.viva_agent import generate_viva

load_dotenv()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Paper → Presentation & Viva Agent", layout="wide")

# ---------- HEADER ----------
col1, col2 = st.columns([1, 5])

with col1:
    st.image("assets/logo.png", width=150)

with col2:
    st.title("RajniAI: AI-Powered Research Assistant")
    st.caption("Summaries • PPT • Viva • References • Chat Assistant")

# ---------- SESSION STATE INIT ----------
for key in ["store", "plan", "summary", "concepts", "viva", "references", "pptx","gamma_prompt"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Settings")

    provider = st.selectbox(
        "LLM Provider",
        ["gemini", "groq"],
        index=0 if os.getenv("LLM_PROVIDER", "gemini") == "gemini" else 1
    )

    os.environ["LLM_PROVIDER"] = provider
    key_label = "GOOGLE_API_KEY" if provider == "gemini" else "GROQ_API_KEY"

    key_val = st.text_input(
        key_label,
        value=os.getenv(key_label, ""),
        type="password"
    )

    if key_val:
        os.environ[key_label] = key_val

    st.markdown("---")

    st.markdown(
        """
    ### 🔑 Need API Keys?

    If you don’t have keys yet, create them here:

    - 🟡 Gemini API:  
    https://aistudio.google.com/apikey

    - 🟢 Groq API:  
    https://console.groq.com/keys

    ---

    💡 Tip:  
    Gemini works best for long documents  
    Groq is faster for chat & viva generation
    """
    )
# ---------- FILE UPLOAD ----------
uploaded = st.file_uploader("Upload research paper (PDF)", type=["pdf"])


# ---------- RUN PIPELINE ----------
if uploaded and st.button("🚀 Run all agents", type="primary"):

    if not os.getenv(key_label):
        st.error(f"Please provide your {key_label}")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.read())
        pdf_path = tmp.name

    try:
        # -------- RAG STORE --------
        with st.status("Indexing paper...", expanded=False):
            store = build_vectorstore(pdf_path)
        st.session_state["store"] = store

        # -------- SUMMARY --------
        with st.status("Generating Summary...", expanded=False):
            summary = summarize(store)
        st.session_state["summary"] = summary

        # -------- CONCEPTS --------
        with st.status("Extracting Concepts...", expanded=False):
            concepts = extract_concepts(store)
        st.session_state["concepts"] = concepts

        # -------- SLIDES --------
        with st.status("Generating PPT Plan...", expanded=False):
            plan = {
                "title": summary.get("title", "Research Paper"),
                "subtitle": "AI Generated Presentation",
                "slides": [
                    {
                        "title": section,
                        "bullets": [
                            sentence.strip()
                            for sentence in text.split(".")
                            if sentence.strip()
                        ]
                    }
                    for section, text in summary.items()
                ]
            }
            pptx_file = build_pptx(plan, theme="academic")

        st.session_state["plan"] = plan
        st.session_state["pptx"] = pptx_file

        # -------- VIVA --------
        with st.status("Generating Viva...", expanded=False):
            viva = generate_viva(summary, concepts)
        st.session_state["viva"] = viva

        # -------- REFERENCES --------
        with st.status("Extracting References...", expanded=False):
            refs = extract_references(store)
        st.session_state["references"] = refs
        #--------GAAMA----------------
        # -------- GAMMA PROMPT --------
        with st.status("Generating Gamma Prompt...", expanded=False):

            gamma_prompt = f"""
                Act as an expert academic presentation designer.

                Create a visually stunning IEEE-style research presentation from the following paper.

                TITLE:
                {summary.get('title', '')}

                SUMMARY:
                {json.dumps(summary, indent=2)}

                CONCEPTS:
                {json.dumps(concepts, indent=2)}

                Requirements:

                1. Generate 15 professional slides.
                2. First slide should contain title, author name, affiliation.
                3. Include:
                - Problem Statement
                - Research Gap
                - Objectives
                - Literature Review
                - Proposed Methodology
                - System Architecture
                - Workflow Diagram
                - Algorithm
                - Experimental Setup
                - Results and Analysis
                - Comparative Study
                - Advantages
                - Limitations
                - Future Work
                - Conclusion
                - References

                4. Use modern academic blue theme.
                5. Add relevant icons and illustrations.
                6. Create speaker notes for every slide.
                7. Keep slide text concise.
                8. Highlight novelty and contributions.
                9. Use diagrams wherever possible instead of paragraphs.
                10. Presentation should be suitable for:
                    - M.Tech Viva
                    - PhD Synopsis
                    - IEEE Conference Presentation
                    - Faculty Research Seminar
                """

        st.session_state["gamma_prompt"] = gamma_prompt
        st.success("All agents finished successfully!")

    except Exception as e:
        st.exception(e)


# ---------- SAFE GET ----------
def safe_get(key):
    return st.session_state.get(key, None)


# ---------- TABS ----------
if st.session_state.get("summary"):

    tabs = st.tabs([
        "📝 Summary",
        "🔑 Concepts",
        "🎞️ Slides",
        "📚 References",
        "🎓 Viva Q&A",
        "🧠 Gamma Prompt",
        "💬 Ask Anything"
    ])

    # ================= SUMMARY =================
    with tabs[0]:
        summary = safe_get("summary")
        if summary:
            for section, text in summary.items():
                st.subheader(section)
                st.write(text)

            word_buffer = create_word_file("Summary", summary)

            st.download_button(
                "⬇️ Download Summary (Word)",
                data=word_buffer,
                file_name="summary.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    # ================= CONCEPTS =================
    with tabs[1]:
        c = safe_get("concepts")
        if c:
            st.subheader(c.get("title", ""))

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Contributions")
                for x in c.get("contributions", []):
                    st.markdown(f"- {x}")

                st.markdown("### Methods")
                for x in c.get("methods", []):
                    st.markdown(f"- {x}")

            with col2:
                st.markdown("### Results")
                for x in c.get("results", []):
                    st.markdown(f"- {x}")

                st.markdown("### Keywords")
                st.write(", ".join(c.get("keywords", [])))

            word_buffer = create_word_file("Concepts", c)

            st.download_button(
                "⬇️ Download Concepts (Word)",
                data=word_buffer,
                file_name="concepts.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    # ================= SLIDES =================
    with tabs[2]:
        plan = safe_get("plan")

        if plan:
            st.subheader(plan.get("title", ""))
            st.caption(plan.get("subtitle", ""))

            for i, sl in enumerate(plan.get("slides", []), 1):
                with st.expander(f"Slide {i}: {sl['title']}"):
                    for b in sl.get("bullets", []):
                        st.markdown(f"- {b}")

            pptx_file = safe_get("pptx")

            st.download_button(
                "⬇️ Download PPT Presentation",
                data=pptx_file,
                file_name="presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

    # ================= REFERENCES =================
    with tabs[3]:
        refs = safe_get("references")

        if refs:
            st.subheader("📚 References")

            for ref in refs.get("references", []):
                st.markdown(ref)
                st.divider()

            word_buffer = create_word_file(
                "References",
                refs.get("references", [])
            )

            st.download_button(
                "⬇️ Download References (Word)",
                data=word_buffer,
                file_name="references.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    # ================= VIVA =================
    with tabs[4]:
        viva = safe_get("viva")

        if viva:
            for i, q in enumerate(viva.get("questions", []), 1):
                with st.expander(f"Q{i} [{q.get('difficulty','?')}]"):
                    st.markdown(q["question"])
                    st.markdown("**Answer:** " + q["answer"])

            word_buffer = create_viva_word(viva)

            st.download_button(
                "⬇️ Download Viva (Word)",
                data=word_buffer,
                file_name="viva_questions.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    # ================= GAMMA PROMPT =================
    with tabs[5]:

        st.subheader("🧠 Gamma Presentation Prompt")

        gamma_prompt = safe_get("gamma_prompt")

        if gamma_prompt:

            st.text_area(
                "Generated Gamma Prompt",
                value=gamma_prompt,
                height=500
            )

            st.download_button(
                "⬇️ Download Gamma Prompt",
                data=gamma_prompt,
                file_name="gamma_prompt.txt",
                mime="text/plain"
            )

            st.info(
                "Copy this prompt and paste it into Gamma.app → Create with AI."
            )

    # ================= CHAT =================
    with tabs[6]:
        st.subheader("💬 Ask Anything About This Paper")

        question = st.text_input("Enter your question")

        if st.button("🔍 Search"):
            store = safe_get("store")

            if store:
                answer = ask_question(store, question)

                st.markdown("### Answer")
                st.write(answer)

                st.download_button(
                    "⬇️ Download Answer",
                    data=answer,
                    file_name="answer.txt",
                    mime="text/plain"
                )
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    text-align: center;
    font-size: 13px;
    padding: 8px;
    background-color: rgba(20, 20, 20, 0.95);
    color: white;
    z-index: 9999;
    border-top: 1px solid #444;
}
</style>

<div class="footer">
    © 2026 RajniAI | Developed by Rajni Tiwari, CSE, CMRIT
</div>
""", unsafe_allow_html=True)