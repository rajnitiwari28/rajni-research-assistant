"""Streamlit UI for the Paper-to-Presentation & Viva Agent."""
import os, tempfile, json
import streamlit as st
from dotenv import load_dotenv

from agents.rag_store import build_vectorstore
from agents.summarizer import summarize
from agents.concept_extractor import extract_concepts
from agents.slide_generator import generate_slide_plan, build_pptx
from agents.viva_agent import generate_viva

load_dotenv()

st.set_page_config(page_title="Paper → Presentation & Viva Agent", layout="wide")
st.title("📄 Paper-to-Presentation & Viva Agent")
st.caption("Upload a research paper (PDF). Get a summary, slide deck, and viva Q&A.")

with st.sidebar:
    st.header("⚙️ Settings")
    provider = st.selectbox("LLM Provider", ["gemini", "groq"],
                            index=0 if os.getenv("LLM_PROVIDER", "gemini") == "gemini" else 1)
    os.environ["LLM_PROVIDER"] = provider
    key_label = "GOOGLE_API_KEY" if provider == "gemini" else "GROQ_API_KEY"
    key_val = st.text_input(key_label, value=os.getenv(key_label, ""), type="password")
    if key_val:
        os.environ[key_label] = key_val
    st.markdown("---")
    st.markdown(
        "**Free API keys:**\n"
        "- Gemini: https://aistudio.google.com/apikey\n"
        "- Groq: https://console.groq.com/keys"
    )

uploaded = st.file_uploader("Upload research paper (PDF)", type=["pdf"])

if uploaded and st.button("🚀 Run all agents", type="primary"):
    if not os.getenv(key_label):
        st.error(f"Please provide your {key_label} in the sidebar.")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.read())
        pdf_path = tmp.name

    try:
        with st.status("Indexing paper with ChromaDB (RAG)...", expanded=False):
            store = build_vectorstore(pdf_path)
        st.session_state["store"] = store

        with st.status("🧠 Summarizer Agent...", expanded=False):
            summary = summarize(store)
        st.session_state["summary"] = summary

        with st.status("🔍 Concept-Extractor Agent...", expanded=False):
            concepts = extract_concepts(store)
        st.session_state["concepts"] = concepts

        with st.status("🎞️ Slide-Generator Agent...", expanded=False):
            plan = generate_slide_plan(summary, concepts)
            pptx_bytes = build_pptx(plan)
        st.session_state["plan"] = plan
        st.session_state["pptx"] = pptx_bytes

        with st.status("🎓 Viva Agent...", expanded=False):
            viva = generate_viva(summary, concepts)
        st.session_state["viva"] = viva

        st.success("All agents finished!")
    except Exception as e:
        st.exception(e)

# ---------- Display ----------
if "summary" in st.session_state:
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "🔑 Concepts", "🎞️ Slides", "🎓 Viva Q&A"])

    with tab1:
        for section, text in st.session_state["summary"].items():
            st.subheader(section)
            st.write(text)

    with tab2:
        c = st.session_state["concepts"]
        st.subheader(c.get("title", ""))
        st.caption(c.get("authors", ""))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Contributions")
            for x in c.get("contributions", []): st.markdown(f"- {x}")
            st.markdown("### Methods")
            for x in c.get("methods", []): st.markdown(f"- {x}")
        with col2:
            st.markdown("### Results")
            for x in c.get("results", []): st.markdown(f"- {x}")
            st.markdown("### Keywords")
            st.write(", ".join(c.get("keywords", [])))

    with tab3:
        plan = st.session_state["plan"]
        st.subheader(plan.get("title", ""))
        st.caption(plan.get("subtitle", ""))
        for i, sl in enumerate(plan.get("slides", []), 1):
            with st.expander(f"Slide {i}: {sl['title']}"):
                for b in sl.get("bullets", []):
                    st.markdown(f"- {b}")
        st.download_button(
            "⬇️ Download PPTX",
            data=st.session_state["pptx"],
            file_name="presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    with tab4:
        for i, q in enumerate(st.session_state["viva"].get("questions", []), 1):
            with st.expander(f"Q{i} [{q.get('difficulty','?')}] {q['question']}"):
                st.markdown(f"**Category:** {q.get('category','')}")
                st.markdown(f"**Model answer:** {q['answer']}")
        st.download_button(
            "⬇️ Download Viva JSON",
            data=json.dumps(st.session_state["viva"], indent=2),
            file_name="viva_questions.json",
            mime="application/json",
        )
