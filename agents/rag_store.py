"""
RAG Store
Loads PDF, creates ChromaDB vector store,
and provides smart retrieval for paper QA.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# --------------------------------------------------
# SECTION DETECTION
# --------------------------------------------------
SECTION_KEYWORDS = {
    "abstract": [
        "abstract"
    ],

    "methodology": [
        "method",
        "methodology",
        "approach",
        "model",
        "architecture",
        "framework",
        "algorithm"
    ],

    "results": [
        "result",
        "results",
        "evaluation",
        "accuracy",
        "experiment",
        "performance"
    ],

    "references": [
        "reference",
        "references",
        "bibliography"
    ]
}


# --------------------------------------------------
# BUILD VECTOR STORE
# --------------------------------------------------
def build_vectorstore(pdf_path: str):

    loader = PyPDFLoader(pdf_path)

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=80
    )

    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Tag chunks with section metadata
    for chunk in chunks:

        text = chunk.page_content.lower()

        chunk.metadata["section"] = "general"

        for section, keywords in SECTION_KEYWORDS.items():

            if any(keyword in text for keyword in keywords):

                chunk.metadata["section"] = section
                break

    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    return store


# --------------------------------------------------
# SMART RETRIEVAL
# --------------------------------------------------
def retrieve_context(
    store,
    query: str,
    k: int = 8,
    section: str = None
):

    try:

        # Section-aware retrieval
        if section:

            results = store.similarity_search(
                query,
                k=k,
                filter={"section": section}
            )

            # fallback if nothing found
            if not results:

                results = store.similarity_search(
                    query,
                    k=k
                )

        else:

            results = store.similarity_search(
                query,
                k=k
            )

        context = "\n\n".join(
            doc.page_content[:700]
            for doc in results
        )

        # Prevent Groq/Gemini token overflow
        return context[:10000]

    except Exception as e:

        print("Retrieval Error:", e)

        return ""


# --------------------------------------------------
# FULL PAPER TEXT
# --------------------------------------------------
def full_text(
    store,
    max_chars: int = 10000
):

    try:

        docs = store.get()["documents"]

        text = "\n\n".join(docs)

        return text[:max_chars]

    except Exception:

        return ""


# --------------------------------------------------
# SECTION RETRIEVAL HELPER
# --------------------------------------------------
def retrieve_section(
    store,
    section_name: str,
    k: int = 10
):

    return retrieve_context(
        store=store,
        query=section_name,
        k=k,
        section=section_name
    )