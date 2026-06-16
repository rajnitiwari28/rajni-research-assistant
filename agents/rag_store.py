"""Loads a PDF, chunks it, embeds with a local sentence-transformer,
and stores it in an in-memory Chroma collection for retrieval."""
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings


def build_vectorstore(pdf_path: str) -> Chroma:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=150
    )
    chunks = splitter.split_documents(docs)

    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    # In-memory Chroma (no persistence) -> easier to ship
    store = Chroma.from_documents(chunks, embedding=embeddings)
    return store


def retrieve_context(store: Chroma, query: str, k: int = 6) -> str:
    results = store.similarity_search(query, k=k)
    return "\n\n---\n\n".join(d.page_content for d in results)


def full_text(store: Chroma, max_chars: int = 18000) -> str:
    """Return concatenated text of all chunks (truncated)."""
    all_docs = store.get()["documents"]
    text = "\n\n".join(all_docs)
    return text[:max_chars]
