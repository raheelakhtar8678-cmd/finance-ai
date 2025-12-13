# src/ai/rag_engine.py
"""
RAG engine for Financial AI.
Integrates:
- BGE-small embeddings
- ChromaDB vector store
- Phi-3-mini-4k-instruct (local or Colab)
- Deterministic calculator
- Variable extraction from context
"""

import os
import json
import re
import textwrap
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import torch
from src.ai.embeddings import get_embedding_model
from src.ai.vector_store import get_vector_store
from src.analysis.calculator import safe_eval_expr
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# 🔑 CONFIG
MODEL_NAME = os.getenv("FIN_MODEL", "microsoft/Phi-3-mini-4k-instruct")  # ✅ Real HF model ID
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CHUNK_SIZE = 3  # Multi-row context for financial tables

# 🧠 LLM Loader (lazy, safe)
_llm_pipe = None
_tokenizer = None

def load_llm(model_name: str = MODEL_NAME):
    global _llm_pipe, _tokenizer
    if _llm_pipe is not None:
        return _llm_pipe, _tokenizer
    try:
        _tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            device_map="auto" if DEVICE == "cuda" else None,
            trust_remote_code=True,
        )
        _llm_pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=_tokenizer,
            device_map="auto" if DEVICE == "cuda" else None,
        )
        return _llm_pipe, _tokenizer
    except Exception as e:
        raise RuntimeError(f"Failed to load LLM '{model_name}': {e}")

# 📥 INDEXING (multi-row chunks)
def index_dataframe_to_chroma(
    df: pd.DataFrame,
    source_name: str,
    table_id: int,
    chunk_size: int = CHUNK_SIZE
) -> None:
    emb = get_embedding_model()
    store = get_vector_store()
    texts = []
    vectors = []
    metadata = []
    n = len(df)
    for start in range(0, n, chunk_size):
        block = df.iloc[start:start + chunk_size]
        rows_txt = []
        for idx, row in block.iterrows():
            row_text = " | ".join(f"{c}: {row[c]}" for c in df.columns if pd.notna(row[c]))
            rows_txt.append(row_text)
        doc_text = "\n".join(rows_txt)
        texts.append(doc_text)
        vec = emb.embed_text(doc_text)
        vectors.append(vec)
        metadata.append({
            "source": source_name,
            "table_id": table_id,
            "start_row": int(start),
            "end_row": int(min(start + chunk_size - 1, n - 1))
        })
    store.add_embeddings(texts=texts, vectors=vectors, metadata_list=metadata)

# 🔍 RETRIEVAL
def retrieve_context(query: str, k: int = 5) -> List[Dict[str, Any]]:
    emb = get_embedding_model()
    store = get_vector_store()
    qvec = emb.embed_text(query)
    results = store.query(qvec, k=k)
    docs = []
    for doc_text, meta, dist in zip(results["documents"], results["metadatas"], results["distances"]):
        docs.append({"text": doc_text, "meta": meta, "score": float(dist)})
    return docs

# 🔍 VARIABLE EXTRACTION (CRITICAL FIX)
def extract_variables_from_retrieved(retrieved_docs: List[Dict]) -> Dict[str, float]:
    variables = {}
    for doc in retrieved_docs:
        text = doc.get("text", "")
        # Match patterns like "revenue_latest: 1234000" or "cash = 500000"
        matches = re.findall(r"(\w+)[\s:=]+([+-]?\d[\d,.]*)", text)
        for key, val_str in matches:
            try:
                clean_val = val_str.replace(",", "").replace("$", "")
                variables[key] = float(clean_val)
            except (ValueError, TypeError):
                continue
    return variables

# 🧾 PROMPT (financial-focused, JSON-enforced)
def build_rag_prompt(user_question: str, retrieved: List[Dict[str, Any]], max_context_chars: int = 7000) -> str:
    context = ""
    for i, doc in enumerate(retrieved):
        context += f"[DOC {i+1}] Source: {doc['meta'].get('source', 'unknown')}\n{doc['text']}\n\n"
    prompt = textwrap.dedent(f"""
    You are a CFA-certified financial analyst. Use ONLY the CONTEXT below.
    RULES:
    1. NEVER hallucinate numbers.
    2. For calculations, respond EXACTLY: {{"tool":"calculator","expr":"valid_expr","note":"reason"}}
    3. Use variable names from context (e.g., revenue_latest, cash_2023).
    4. If unsure, say: {{"answer":"Insufficient data","confidence":0.3}}

    CONTEXT:
    {context}

    QUESTION: {user_question}
    """)
    return prompt

# 🤖 LLM CALL (safe, with Phi-3 format)
def _call_llm(prompt: str, max_tokens: int = 256) -> str:
    pipe, _ = load_llm()
    # Add Phi-3 chat format
    full_prompt = f"<|system|>\nYou are a helpful financial assistant.<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
    out = pipe(
        full_prompt,
        max_new_tokens=max_tokens,
        do_sample=False,
        pad_token_id=pipe.tokenizer.eos_token_id
    )
    return out[0]["generated_text"]

# 🧩 JSON PARSING (robust)
def _parse_json_response(text: str) -> Optional[dict]:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        return json.loads(text.strip())
    except Exception:
        return None

# 🚀 MAIN ASK FUNCTION
def ask(query: str) -> Dict[str, Any]:
    try:
        # 1. Retrieve context
        retrieved = retrieve_context(query, k=5)
        
        # 2. Build prompt
        prompt = build_rag_prompt(query, retrieved)
        
        # 3. Call LLM
        raw_out = _call_llm(prompt, max_tokens=200)
        
        # 4. Parse response
        payload = _parse_json_response(raw_out)
        if not payload:
            return {"error": "invalid_json", "raw": raw_out}
        
        # 5. Handle calculator request
        if payload.get("tool") == "calculator":
            expr = payload.get("expr", "")
            variables = extract_variables_from_retrieved(retrieved)  # ✅ NOW WORKS
            try:
                result = safe_eval_expr(expr, variables)
                return {
                    "answer": result,
                    "note": payload.get("note"),
                    "source": [d["meta"] for d in retrieved]
                }
            except Exception as e:
                return {"error": "calculation_failed", "expr": expr, "message": str(e)}
        
        return payload
        
    except Exception as e:
        return {"error": "rag_failed", "message": str(e)}