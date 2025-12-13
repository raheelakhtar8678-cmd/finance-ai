# src/ai/rag_engine.py
"""
RAG engine WITHOUT LLM.
Supports:
- Indexing cleaned DataFrames into ChromaDB (row-level)
- Retrieving relevant financial data by query
- Extracting numeric variables from retrieved text
- Calling calculator with expressions like "revenue_2024 - revenue_2023"
- Returning auditable, sourced answers
Dependencies:
  - src.ai.embeddings
  - src.ai.vector_store
  - src.analysis.calculator
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional
from src.ai.embeddings import get_embedding_model
from src.ai.vector_store import get_vector_store
from src.analysis.calculator import safe_eval_expr


# ========================
# INDEXING
# ========================
def index_dataframe_to_chroma(
    df: pd.DataFrame,
    source_name: str,
    table_id: int,
    chunk_size: int = 1
) -> None:
    """
    Index a cleaned DataFrame into Chroma at row granularity.
    Args:
        df: cleaned pandas DataFrame
        source_name: e.g., "company_10q_2024.pdf"
        table_id: integer ID for the table inside the source
        chunk_size: number of rows to combine per document (default: 1)
    """
    emb = get_embedding_model()
    store = get_vector_store()
    texts = []
    vectors = []
    metadata = []
    n = len(df)

    for start in range(0, n, chunk_size):
        block = df.iloc[start:start + chunk_size]
        rows_txt = []
        for _, row in block.iterrows():
            row_text = " | ".join(f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col]))
            rows_txt.append(row_text)
        doc_text = "\n".join(rows_txt)
        if not doc_text.strip():
            continue
        texts.append(doc_text)
        vec = emb.embed_text(doc_text)
        vectors.append(vec)
        metadata.append({
            "source": source_name,
            "table_id": table_id,
            "start_row": int(start),
            "end_row": int(min(start + chunk_size - 1, n - 1))
        })

    if texts:
        store.add_embeddings(texts=texts, vectors=vectors, metadata_list=metadata)


# ========================
# RETRIEVAL
# ========================
def retrieve_context(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant chunks for the query.
    Returns list of dicts: {"text": str, "meta": dict, "score": float}
    """
    emb = get_embedding_model()
    store = get_vector_store()
    query_vec = emb.embed_text(query)
    results = store.query(query_vec, k=k)
    docs = []
    for text, meta, dist in zip(results["documents"], results["metadatas"], results["distances"]):
        docs.append({"text": text, "meta": meta, "score": float(dist)})
    return docs


# ========================
# VARIABLE EXTRACTION
# ========================
def extract_variables_from_retrieved(retrieved_docs: List[Dict]) -> Dict[str, float]:
    """
    Extract numeric variables from retrieved text.
    Example: "revenue: 1,234,000" → {"revenue": 1234000.0}
    Handles commas and parentheses: (1,200) → -1200
    """
    variables = {}
    for doc in retrieved_docs:
        text = doc.get("text", "")
        # Match patterns like "key: value" or "key = value"
        matches = re.findall(r"(\w+)\s*[:=]\s*([+-]?\d[\d,.]*)", text)
        for key, val_str in matches:
            try:
                # Clean and convert
                clean_val = val_str.replace(",", "").replace("$", "").strip()
                # Handle parentheses as negative
                if clean_val.startswith("(") and clean_val.endswith(")"):
                    clean_val = "-" + clean_val[1:-1]
                variables[key] = float(clean_val)
            except (ValueError, TypeError):
                continue
    return variables


# ========================
# HIGH-LEVEL QUERY API
# ========================
def ask(query: str, k: int = 5, expr: Optional[str] = None) -> Dict[str, Any]:
    """
    Main API function.
    If `expr` is provided, execute it using variables from retrieved context.
    If `expr` is None, return retrieved context only.
    Parameters:
        query (str): Natural language query (e.g., "What is the cash balance?")
        k (int): Number of chunks to retrieve
        expr (str, optional): Expression to evaluate (e.g., "cash / monthly_expenses")
    Returns:
        dict with keys:
            - "retrieved": list of relevant chunks
            - "variables": extracted numeric values
            - "answer": result of expression (if expr provided)
            - "expr_used": the expression evaluated (if applicable)
    """
    # 1. Retrieve relevant context
    retrieved = retrieve_context(query, k=k)
    
    # 2. Extract variables
    variables = extract_variables_from_retrieved(retrieved)
    
    result = {
        "retrieved": retrieved,
        "variables": variables,
        "answer": None,
        "expr_used": expr
    }
    
    # 3. If expression is given, calculate
    if expr:
        try:
            answer = safe_eval_expr(expr, variables)
            result["answer"] = answer
        except Exception as e:
            result["error"] = f"Calculation failed: {e}"
    
    return result