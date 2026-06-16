"""Concept Extractor — pulls contributions, methods, results as JSON."""
import json, re
from langchain_core.prompts import ChatPromptTemplate
from .llm_factory import get_llm
from .rag_store import full_text

PROMPT = ChatPromptTemplate.from_template(
    """Extract the key academic concepts from this research paper.

Return STRICT JSON with these keys:
{{
  "title": "string",
  "authors": "string (best guess; empty if unknown)",
  "contributions": ["short bullet", ...],
  "methods": ["short bullet", ...],
  "results": ["short bullet", ...],
  "keywords": ["term", ...]
}}

Paper text:
{text}

Return only JSON. No prose, no markdown fences.
"""
)


def _parse_json(text: str) -> dict:
    text = text.strip()
    # strip code fences if any
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        # find first { ... last }
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def extract_concepts(store) -> dict:
    llm = get_llm(temperature=0.1)
    chain = PROMPT | llm
    resp = chain.invoke({"text": full_text(store)})
    return _parse_json(resp.content)
