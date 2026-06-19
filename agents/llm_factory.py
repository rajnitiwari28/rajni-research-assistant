"""Single place to build an LLM. Switch providers via .env."""
import os
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.3):
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            groq_api_key=os.getenv("GROQ_API_KEY"),
        )
    # default: gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
