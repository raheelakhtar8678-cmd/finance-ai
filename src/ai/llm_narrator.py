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

# Secondary free models to try if primary fails (Updated Jan 2025)
OPENROUTER_FALLBACK_MODELS = [
    "deepseek/deepseek-chat:free",          # Strong reasoning, free tier
    "google/gemma-3-27b-it:free",           # Google's latest free model
    "meta-llama/llama-3.3-70b-instruct:free", # Meta's latest free model
    "qwen/qwen-2.5-72b-instruct:free"       # Qwen's free model
]

def explain_with_openrouter(prompt: str, model: str = OPENROUTER_MODEL) -> str:
    """Call OpenRouter API with a specific model"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    # 🔄 Lazy Reload: If key is missing, try reloading from .env
    # This helps if the key was added after the server started
    if not openrouter_key:
        print("⚠️ OpenRouter key missing in env. Attempting to reload .env...")
        load_dotenv(override=True)
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_key:
        raise Exception("OPENROUTER_API_KEY not found in environment or .env")
    
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/raheelakhtar8678/finance-ai", 
        "X-Title": "Finance AI Analyst"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional financial analyst. Provide a structured report."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    r.raise_for_status()
    res_json = r.json()
    if "choices" not in res_json:
        raise Exception(f"OpenRouter Error: {res_json}")
        
    return res_json["choices"][0]["message"]["content"].strip()


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
You are a Senior Financial Analyst AI. Your goal is to provide elite-level, structured, and exhaustive financial insights that outperform standard AI like GPT-4 or Gemini.

STRICT REPORTING FORMAT:
1. **Key Metrics Table**: Present ALL metrics in a PROPER MARKDOWN TABLE using pipe characters (|). EVERY cell must have a value - never leave cells empty. Use "N/A" if data is unavailable. Format example:
| Metric | Value | Growth |
| --- | --- | --- |
| Revenue | 1,950,000 | +8.3% |
2. **Concise Analysis**: Use bullet points to explain trends, rank performance, or highlight outliers. NO long paragraphs.
3. **Analyst Verdict**: A one-sentence professional summary based on the actual data.

CONTEXT:
User Question: "{user_question}"

AVAILABLE DATA:
1. Verified Metrics:
{computed_result}

2. Document Context (Relevant Tables & Text):
{rag_context}

{charts_text}

ANALYST INSTRUCTIONS:

⚠️ **CRITICAL - PROFIT/LOSS VERIFICATION**:
Before EVER claiming "profit/loss data is not available":
1. SEARCH the context for "Net Income" - this is THE definitive profit metric
2. SEARCH for "Condensed Consolidated Statements of Operations" or "Income Statement"
3. If you find Net Income > 0, the company IS PROFITABLE
4. If you find Net Income < 0, the company IS MAKING A LOSS
5. ONLY claim "data not available" if you genuinely cannot find Net Income anywhere

**Exhaustive Extraction**: If a table is provided in the context, analyze ALL of its rows. Never claim data is missing if a relevant table is present.

**Precision**: Use the Verified Metrics as primary truth, but supplement with ALL details found in the Document Context.

**Period Sensitivity**: Financial tables often have multiple columns for different durations (e.g. "Three Months Ended" vs "Six Months Ended"). You MUST match the user's specific duration request to the correct column.

**Statement Types to Check**:
- For PROFIT/LOSS questions: Income Statement → Net Income line
- For REVENUE questions: Income Statement → Net Sales/Revenue line  
- For CASH questions: Cash Flow Statement → Operating Activities line
- For ASSETS/DEBT questions: Balance Sheet

**Triangulation**: If comparing metrics, look across ALL statements. Explain differences (e.g., why OCF differs from Net Income due to accruals).

**🚨 CRITICAL - NO HALLUCINATIONS 🚨**:
1. **NEVER invent numbers** - Only use values that appear EXACTLY in the provided data
2. **NEVER swap periods** - If 2025 shows $16,002M and 2024 shows $16,372M, report them in the CORRECT columns
3. **NEVER round differently** - Use the exact precision shown in the source
4. **Double-check period labels** - Ensure "Current Period" vs "Prior Period" are not swapped
5. **If unsure, say "Not found"** - Do not guess or approximate

**DATA VERIFICATION CHECKLIST**:
Before reporting any number, verify:
✓ Is this the exact value from the source (not rounded or estimated)?
✓ Is this assigned to the correct year/period column?
✓ Does the source explicitly show this metric for this period?

Your Structured Analyst Report:
"""
        
        # Try Gemini first
        try:
            print("   🔄 Trying Gemini...")
            explanation = explain_with_gemini(full_prompt)
            explanation = self._fix_table_formatting(explanation)
            print("   ✅ Gemini success")
            return explanation
            
        except Exception as e1:
            print(f"   ⚠️ Gemini failed: {e1}. Falling back to OpenRouter...")
            
            # Try OpenRouter with a chain of models
            models_to_try = [OPENROUTER_MODEL] + OPENROUTER_FALLBACK_MODELS
            
            for model_name in models_to_try:
                try:
                    print(f"   🔄 Trying OpenRouter ({model_name})...")
                    explanation = explain_with_openrouter(full_prompt, model=model_name)
                    
                    if explanation and len(explanation) > 10:
                        explanation = self._fix_table_formatting(explanation)
                        print(f"   ✅ OpenRouter success ({model_name})")
                        return explanation
                    else:
                        print(f"   ⚠️ OpenRouter ({model_name}) returned empty/short response.")
                except Exception as ex:
                    print(f"   ⚠️ OpenRouter ({model_name}) failed: {ex}")
            
            # Final fallback: Emergency Report
            print("   ℹ️ Using emergency fallback report (All models exhausted)")
            return self._build_emergency_report(user_question, computed_result)

    def _fix_table_formatting(self, text: str) -> str:
        """
        Convert tab-separated tables to proper markdown format.
        Detects consecutive lines with tabs and converts to pipe-separated tables.
        Also handles lines that are just dashes (separator artifacts from LLM).
        Also handles single-line tables where rows are separated by '| |'.
        """
        import re
        
        # PRE-PROCESSING: Fix single-line tables
        # Pattern: "| A | B | | C | D |" -> should be two rows
        # Detect this by looking for "| |" (pipe space pipe) which indicates row separator
        def fix_single_line_tables(txt):
            lines = txt.split('\n')
            fixed_lines = []
            for line in lines:
                stripped = line.strip()
                # Check if line looks like a single-line table (multiple | | patterns)
                if stripped.startswith('|') and '| |' in stripped:
                    # Split on '| |' to get rows, then rejoin with newlines
                    # But we need to be careful: "| |" between cells vs row separator
                    # Row separator is "| |" where next char is uppercase or starts a new cell
                    parts = re.split(r'\|\s+\|(?=\s*[A-Z\$\d])', stripped)
                    if len(parts) > 1:
                        # Reconstruct each part as a proper row
                        new_rows = []
                        for i, part in enumerate(parts):
                            part = part.strip()
                            if not part.startswith('|'):
                                part = '| ' + part
                            if not part.endswith('|'):
                                part = part + ' |'
                            new_rows.append(part)
                        
                        # Check if we need to add header separator after first row
                        if len(new_rows) > 1 and '---' not in new_rows[1]:
                            # Count columns from first row
                            first_row_cells = [c.strip() for c in new_rows[0].split('|') if c.strip()]
                            separator = '| ' + ' | '.join(['---'] * len(first_row_cells)) + ' |'
                            new_rows.insert(1, separator)
                        
                        fixed_lines.extend(new_rows)
                        continue
                fixed_lines.append(line)
            return '\n'.join(fixed_lines)
        
        text = fix_single_line_tables(text)
        
        lines = text.split('\n')
        result_lines = []
        table_buffer = []
        
        def is_separator_line(line):
            """Check if line is just dashes/separators (not data)."""
            stripped = line.strip()
            # Match lines that are only dashes, pipes, tabs, and spaces
            # Also match tab-separated dashes like "---\t---\t---"
            if not stripped:
                return False
            # Check if all "cells" are just dashes
            cells = re.split(r'[\t|]+', stripped)
            all_dashes = all(re.match(r'^-+$', c.strip()) or c.strip() == '' for c in cells if c)
            return all_dashes and len([c for c in cells if c.strip()]) >= 2
        
        def flush_table():
            """Convert buffered tab-separated lines to markdown table."""
            if not table_buffer:
                return
            
            # Parse all rows
            parsed_rows = []
            max_cols = 0
            for line in table_buffer:
                # Skip pure separator lines (like "---	---	---")
                if is_separator_line(line):
                    continue
                    
                # Split by tab(s) or 4+ spaces
                cells = re.split(r'\t+|\s{4,}', line.strip())
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    parsed_rows.append(cells)
                    max_cols = max(max_cols, len(cells))
            
            if not parsed_rows or max_cols < 2:
                # Not a real table, just add original lines
                result_lines.extend(table_buffer)
                return
            
            # Pad rows to max_cols
            for row in parsed_rows:
                while len(row) < max_cols:
                    row.append('')
            
            # Build markdown table
            # Header row
            header = '| ' + ' | '.join(parsed_rows[0]) + ' |'
            # Separator row
            separator = '| ' + ' | '.join(['---'] * max_cols) + ' |'
            
            result_lines.append(header)
            result_lines.append(separator)
            
            # Data rows
            for row in parsed_rows[1:]:
                data_row = '| ' + ' | '.join(row) + ' |'
                result_lines.append(data_row)
            
            result_lines.append('')  # Empty line after table
        
        for line in lines:
            # Skip pure separator lines entirely
            if is_separator_line(line):
                continue
                
            # Check if line looks like a tab-separated table row
            # Must have at least 2 tab-separated values
            if '\t' in line and line.count('\t') >= 1:
                table_buffer.append(line)
            elif re.search(r'\s{4,}', line) and len(re.split(r'\s{4,}', line)) >= 3:
                # Also detect space-separated tables (4+ spaces between columns)
                table_buffer.append(line)
            else:
                # Flush any accumulated table
                flush_table()
                table_buffer = []
                result_lines.append(line)
        
        # Final flush
        flush_table()
        
        return '\n'.join(result_lines)
    
    def _build_emergency_report(self, user_question, data):
        report = f"# ⚠️ AI Analyst Rate-Limited\n\n"
        report += f"The Senior Analyst reached a request quota limit (20/day) while processing: **{user_question}**.\n\n"
        report += "### 🔍 Verified Data & Sources\n"
        report += "The system successfully retrieved the following relevant financial data. Review the figures below:\n\n"
        report += "```\n" + data + "\n```\n\n"
        report += "---\n*Note: Detailed AI explanation unavailable due to API rate limits.*"
        return report


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