"""Viva Agent — generates likely examiner questions with model answers."""
import json, re
from langchain_core.prompts import ChatPromptTemplate
from .llm_factory import get_llm

PROMPT = ChatPromptTemplate.from_template(
    """You are a viva/thesis examiner. Based on the summary and extracted concepts,
generate likely examiner questions with strong model answers.

Return STRICT JSON:
{{
  "questions": [
    {{
      "question": "...",
      "answer": "2-5 sentences, specific to the paper",
      "difficulty": "easy|medium|hard",
      "category": "motivation|method|results|limitations|theory|application"
    }}
  ]
}}

Generate exactly 12 questions: 3 easy, 6 medium, 3 hard. Cover a mix of categories.

Summary:
{summary}

Concepts:
{concepts}

Return only JSON.
"""
)


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        return json.loads(m.group(0))


def generate_viva(summary: dict, concepts: dict) -> dict:
    llm = get_llm(temperature=0.5)
    chain = PROMPT | llm
    resp = chain.invoke({
        "summary": json.dumps(summary, indent=2),
        "concepts": json.dumps(concepts, indent=2),
    })
    return _parse_json(resp.content)
