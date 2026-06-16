"""Summarizer Agent — produces a sectioned summary via RAG."""
from langchain_core.prompts import ChatPromptTemplate
from .llm_factory import get_llm
from .rag_store import retrieve_context

SECTIONS = [
    ("Background & Motivation", "What problem does this paper address and why is it important?"),
    ("Related Work", "What prior work does this paper build on or compare against?"),
    ("Methodology", "What methods, models, or approaches does the paper propose?"),
    ("Experiments & Datasets", "What datasets, experimental setup, and evaluation metrics are used?"),
    ("Key Results", "What are the main results and findings?"),
    ("Limitations & Future Work", "What limitations are mentioned and what future directions are suggested?"),
]

PROMPT = ChatPromptTemplate.from_template(
    """You are an academic summarizer. Using ONLY the context below from a research paper, write a clear, concise summary for the section: "{section}".

Guidance for this section: {guidance}

Context:
{context}

Write 3-6 sentences. Be specific and factual. If the context does not cover this section, say "Not clearly stated in the paper." """
)


def summarize(store) -> dict:
    llm = get_llm(temperature=0.2)
    chain = PROMPT | llm
    out = {}
    for section, guidance in SECTIONS:
        ctx = retrieve_context(store, f"{section}: {guidance}", k=6)
        resp = chain.invoke({"section": section, "guidance": guidance, "context": ctx})
        out[section] = resp.content.strip()
    return out
