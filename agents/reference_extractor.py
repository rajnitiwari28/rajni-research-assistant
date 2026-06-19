from .llm_factory import get_llm
from .rag_store import retrieve_context
import json
import re


def extract_references(store):

    # Retrieve chunks likely containing references
    context = retrieve_context(
        store,
        "references bibliography citations",
        k=25
    )

    llm = get_llm()

    prompt = f"""
You are a reference extraction system.

Extract ONLY the bibliography/references from the text.

Rules:
- Preserve original text exactly.
- Preserve numbering.
- Do not summarize.
- Do not explain.
- Return valid JSON only.

Format:

{{
    "references": [
        "...",
        "..."
    ]
}}

Text:

{context}
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    try:
        return json.loads(content)

    except Exception:

        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except:
                pass

        return {
            "references": [content]
        }