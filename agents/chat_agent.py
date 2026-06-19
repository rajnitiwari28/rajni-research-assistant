from .llm_factory import get_llm
from .rag_store import retrieve_context


def detect_question_type(q: str):
    q = q.lower()

    if any(x in q for x in ["author", "authors", "title", "year", "journal"]):
        return "metadata"

    if any(x in q for x in ["abstract", "summary"]):
        return "abstract"

    if any(x in q for x in ["method", "methodology", "approach", "model", "architecture"]):
        return "methodology"

    if any(x in q for x in ["result", "accuracy", "performance", "evaluation"]):
        return "results"

    if any(x in q for x in ["reference", "citation"]):
        return "references"

    return "general"


def ask_question(store, question):

    qtype = detect_question_type(question)

    if qtype == "metadata":
        context = retrieve_context(
            store,
            "title authors abstract",
            k=5
        )

    elif qtype == "abstract":
        context = retrieve_context(
            store,
            "abstract introduction summary",
            k=8
        )

    elif qtype == "methodology":
        context = retrieve_context(
            store,
            "methodology approach model architecture proposed method",
            k=10
        )

    elif qtype == "results":
        context = retrieve_context(
            store,
            "results evaluation experiment accuracy performance",
            k=10
        )

    elif qtype == "references":
        context = retrieve_context(
            store,
            "references bibliography citations",
            k=8
        )

    else:
        context = retrieve_context(
            store,
            question,
            k=10
        )

    # Prevent huge requests
    context = context[:10000]

    llm = get_llm()

    prompt = f"""
You are an expert research paper assistant.

Answer using ONLY the paper context.

Rules:
- Be precise and academic.
- Extract information directly from the paper.
- If information is not available, say:
  "This information is not clearly stated in the paper."
- Do not invent authors, results, or methodology.

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    return response.content