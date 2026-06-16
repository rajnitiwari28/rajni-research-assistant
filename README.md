# 📄 Paper-to-Presentation & Viva Agent

An academic assistant that turns any research paper (PDF) into:
1. **Structured summary** (sectioned: Motivation, Methods, Results, …)
2. **Auto-generated slide deck** (downloadable `.pptx`)
3. **Likely viva / examiner questions** with model answers

Built with the exact stack from the project spec:
- **Frontend:** Streamlit
- **Backend:** Python
- **LLM:** Gemini (default) or Groq — both have generous free tiers
- **Vector DB:** ChromaDB (in-memory)
- **Orchestration:** LangChain
- **Multi-agent design:** Summarizer · Concept-Extractor · Slide-Generator · Viva

---

## 🚀 Step-by-step: how to run

### 1. Install Python 3.10+
Check with: `python --version`

### 2. Extract this folder, then open a terminal in it
```bash
cd paper_viva_agent
```

### 3. Create a virtual environment (recommended)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```
> First install takes ~3-5 min (downloads sentence-transformer model on first run).

### 5. Get a FREE API key
- **Gemini (recommended):** https://aistudio.google.com/apikey
- Or **Groq:** https://console.groq.com/keys

### 6. Configure your key (two options)
**Option A — `.env` file:** copy `.env.example` to `.env` and paste your key.
```bash
cp .env.example .env   # then edit .env
```
**Option B — type it into the Streamlit sidebar** when the app opens.

### 7. Launch the app
```bash
streamlit run app.py
```
Your browser opens at `http://localhost:8501`.

### 8. Use it
1. Upload a research paper PDF.
2. Click **🚀 Run all agents**.
3. Browse the **Summary / Concepts / Slides / Viva Q&A** tabs.
4. Download the `.pptx` and viva JSON.

---

## 🧠 Architecture

```
PDF ──► PyPDF Loader ──► Text Splitter ──► Embeddings (MiniLM)
                                                │
                                                ▼
                                         ChromaDB (RAG)
                                                │
        ┌───────────────────────┬───────────────┴────────────────┐
        ▼                       ▼                                ▼
 Summarizer Agent      Concept-Extractor Agent           (shared context)
        │                       │
        └───────────┬───────────┘
                    ▼
         Slide-Generator Agent ──► python-pptx ──► .pptx download
                    │
                    ▼
              Viva Agent ──► JSON Q&A
```

Each agent is a LangChain prompt-chain in `agents/`. They all share the same
`get_llm()` factory, so switching providers (Gemini ↔ Groq) is one env var.

---

## 📁 Project layout

```
paper_viva_agent/
├── app.py                       # Streamlit UI
├── requirements.txt
├── .env.example
├── README.md
└── agents/
    ├── llm_factory.py           # Gemini / Groq switch
    ├── rag_store.py             # PDF → ChromaDB
    ├── summarizer.py            # Agent 1
    ├── concept_extractor.py     # Agent 2
    ├── slide_generator.py       # Agent 3 (+ PPTX export)
    └── viva_agent.py            # Agent 4
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt` inside the venv |
| Slow first run | Sentence-transformer model (~80 MB) downloads once |
| `API key not valid` | Re-check the key in the sidebar / `.env` |
| `Rate limit` on Gemini | Switch provider to `groq` in the sidebar |
| PPTX looks plain | It uses default python-pptx template — open in PowerPoint to restyle |

---

## ➡️ What to do next

- Try it on your own paper.
- Tweak agent prompts in `agents/*.py` (e.g. ask for more slides, harder viva questions).
- Add a 5th agent (e.g. a Critic agent that reviews the summary) — same pattern.
- Persist Chroma to disk by passing `persist_directory="./chroma_db"` in `rag_store.py`.
- Deploy free on **Streamlit Community Cloud**: push to GitHub → connect → add your API key as a secret.
