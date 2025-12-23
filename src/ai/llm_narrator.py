# src/ai/llm_narrator.py
"""
LLM Narrator with Correct google.genai API (New SDK)
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini - Using NEW google.genai package
from google import genai
from google.genai import types

# OpenRouter fallback
import requests


# =========================
# CONFIG
# =========================

GEMINI_MODEL = "gemini-2.5-flash"  # Stable free-tier model
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

# Configure Gemini with new API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"✅ Gemini client initialized")
else:
    print("⚠️ GEMINI_API_KEY not found in environment")
    client = None


# =========================
# PROMPT BUILDER
# =========================

def build_prompt(metric_result: Dict[str, Any]) -> str:
    """
    LLM must ONLY explain – not calculate or invent.
    """
    return f"""
You are a financial analyst assistant.

STRICT RULES:
- Do NOT calculate anything
- Do NOT invent numbers
- ONLY explain what is provided
- Be concise, factual, professional

Metric Result:
{metric_result}

Explain this result clearly for a business user.
"""


# =========================
# GEMINI (PRIMARY)
# =========================

def explain_with_gemini(prompt: str) -> str:
    """Call Gemini API with new google.genai SDK"""
    if not client:
        raise Exception("Gemini client not initialized")
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        raise


# =========================
# OPENROUTER (FALLBACK)
# =========================

def explain_with_openrouter(prompt: str) -> str:
    """Call OpenRouter API as fallback"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_key:
        raise Exception("OPENROUTER_API_KEY not found")
    
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# =========================
# MAIN INTERFACE
# =========================

def narrate(metric_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safe LLM wrapper with fallback.
    """
    prompt = build_prompt(metric_result)

    try:
        explanation = explain_with_gemini(prompt)
        provider = "gemini"
    except Exception as e1:
        print(f"⚠️ Gemini failed: {e1}")
        try:
            explanation = explain_with_openrouter(prompt)
            provider = "openrouter"
        except Exception as e2:
            print(f"⚠️ OpenRouter failed: {e2}")
            explanation = str(metric_result)
            provider = "fallback"

    return {
        "explanation": explanation,
        "llm_provider": provider
    }


# =========================
# CLASS WRAPPER (for compatibility)
# =========================

class LLMNarrator:
    """
    Class wrapper for LLM narration.
    Compatible with answer_generator.py and test scripts.
    """
    
    def __init__(self):
        """Initialize narrator (stateless)"""
        pass
    
    def explain(
        self,
        user_question: str,
        rag_context: str,
        computed_result: str,
        charts: list = None
    ) -> str:
        """
        Generate natural language explanation.
        
        Args:
            user_question: User's original question
            rag_context: Context from RAG retrieval
            computed_result: Deterministic result from backend
            charts: List of chart filenames (optional)
        
        Returns:
            Natural language explanation
        """
        
        # Debug logging
        print(f"\n🤖 LLM EXPLAIN CALLED:")
        print(f"   Question: {user_question}")
        print(f"   Context length: {len(rag_context)}")
        print(f"   Result preview: {computed_result[:100]}...")
        
        # Build enhanced prompt
        charts_text = ""
        if charts:
            charts_text = f"\n\nAvailable visualizations:\n" + "\n".join(f"- {c}" for c in charts)
        
        full_prompt = f"""
You are a professional financial analyst assistant.

STRICT RULES:
- Do NOT calculate anything
- Do NOT invent numbers or data
- ONLY explain what is provided
- If confidence is low, mention uncertainty
- Be concise, factual, and professional

User Question:
{user_question}

Verified Result (from deterministic backend):
{computed_result}

Supporting Context (from documents):
{rag_context}
{charts_text}

Provide a clear, professional explanation.
"""
        
        # Try Gemini first
        try:
            print("   🔄 Trying Gemini...")
            explanation = explain_with_gemini(full_prompt)
            print("   ✅ Gemini success")
            return explanation
            
        except Exception as e1:
            print(f"   ⚠️ Gemini failed: {e1}")
            
            # Try OpenRouter
            try:
                print("   🔄 Trying OpenRouter...")
                explanation = explain_with_openrouter(full_prompt)
                print("   ✅ OpenRouter success")
                return explanation
                
            except Exception as e2:
                print(f"   ⚠️ OpenRouter failed: {e2}")
                
                # Final fallback: return deterministic result only
                print("   ℹ️ Using fallback: returning deterministic result")
                return f"{computed_result}\n\n(Note: AI explanation unavailable - both Gemini and OpenRouter failed)"


# =========================
# FASTAPI COMPATIBILITY
# =========================

def explain_with_llm(question: str, pipeline_answer: str) -> tuple:
    """
    Wrapper for FastAPI router compatibility.
    
    Args:
        question: User's question
        pipeline_answer: Deterministic answer from pipeline
    
    Returns:
        (narration, confidence)
    """
    
    narrator = LLMNarrator()
    
    try:
        explanation = narrator.explain(
            user_question=question,
            rag_context="From uploaded financial documents",
            computed_result=pipeline_answer,
            charts=None
        )
        return explanation, 0.85
    except Exception:
        return pipeline_answer, 0.5