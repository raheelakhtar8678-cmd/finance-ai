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
from src.analysis.calculator import safe_eval_expr

# 🔑 CONFIG
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CHUNK_SIZE = 3  # Multi-row context for financial tables



# 📥 INDEXING (multi-row chunks)
# 📥 INDEXING (Metadata-Rich & HTML/Markdown)
# 📥 INDEXING (Metadata-Rich & HTML/Markdown)
def index_dataframe_to_chroma(
    df: pd.DataFrame,
    source_name: str,
    table_id: int,
    chunk_size: int = CHUNK_SIZE,
    preceding_text: str = "",
    following_text: str = "",
    markdown_content: str = None 
) -> None:
    emb = get_embedding_model()
    store = get_vector_store()
    texts = []
    vectors = []
    metadata = []
    
    # 1. Extract High-Level Metadata
    if df is not None:
        table_text = " ".join([str(c) for c in df.columns] + [str(x) for x in df.head(5).values.flatten()]).lower()
    else:
        table_text = (markdown_content or "").lower()

    # A. Statement Type
    stmt_type = "Generic Table"
    if "balance sheet" in table_text or "balance sheet" in preceding_text.lower(): stmt_type = "Balance Sheet"
    elif "operations" in table_text or "income" in table_text or "operations" in preceding_text.lower(): stmt_type = "Income Statement"
    elif "cash flow" in table_text or "cash flow" in preceding_text.lower(): stmt_type = "Cash Flow Statement"
    elif "segment" in table_text or "segment" in preceding_text.lower(): stmt_type = "Segment Info"
    
    # B. Period Detection (Regex)
    # Look for dates in columns
    found_periods = []
    if df is not None:
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        for col in df.columns:
            c_str = str(col).lower()
            if any(m in c_str for m in months) and re.search(r'\d{4}', c_str):
                found_periods.append(str(col))
    else:
        # Simple regex for markdown
        dates = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}', table_text, re.IGNORECASE)
        found_periods.extend(dates)

    period_str = ", ".join(found_periods) if found_periods else "Unknown Period"
    
    # Use Markdown for full context preservation
    if df is not None:
        try:
            full_doc_text = df.to_markdown(index=False)
        except:
            full_doc_text = df.to_string(index=False)
    else:
        full_doc_text = markdown_content or "No content"

    # Chunking strategy: 
    # For small financial tables/markdown, embedding the WHOLE table is often better than splitting rows
    # because context (headers) is lost in splits.
    
    if df is not None:
        n = len(df)
        # If table is small enough (< 30 rows), embed as one unit
        if n <= 30: 
            # FUSE CONTEXT
            context_block = ""
            if preceding_text: context_block += f"Note/Header: {preceding_text}\n\n"
            if following_text: context_block += f"\n\nFootnote/Context: {following_text}"
            
            rich_text = f"{context_block}Table:\n{full_doc_text}"
            
            texts.append(rich_text)
            metadata.append({
                "source": source_name,
                "table_id": table_id,
                "stmt_type": stmt_type,
                "period": period_str,
                "type": "table_full",
                "start_row": 0,
                "end_row": n,
                "has_context": bool(preceding_text or following_text)
            })
        else:
            # Chunk logic for larger tables
            for start in range(0, n, chunk_size):
                end = min(start + chunk_size, n)
                sub_df = df.iloc[start:end]
                sub_text = sub_df.to_string(index=False)
                
                rich_text = f"Table Segment ({start}-{end}):\n{sub_text}"
                texts.append(rich_text)
                metadata.append({
                    "source": source_name,
                    "table_id": table_id,
                    "stmt_type": stmt_type,
                    "period": period_str,
                    "type": "table_chunk",
                    "start_row": start,
                    "end_row": end,
                    "has_context": False 
                })
    else:
        # Markdown Content (Treat as single chunk for now, or split by double newline if too huge)
        # Improving this: if markdown is massive, we could split by token count, 
        # but PyMuPDF tables usually fit in context.
        context_block = ""
        if preceding_text: context_block += f"Note/Header: {preceding_text}\n\n"
        if following_text: context_block += f"\n\nFootnote/Context: {following_text}"
        
        rich_text = f"{context_block}Table (Markdown):\n{full_doc_text}"
        
        texts.append(rich_text)
        metadata.append({
            "source": source_name,
            "table_id": table_id,
            "stmt_type": stmt_type,
            "period": period_str,
            "type": "markdown_table",
            "start_row": 0,
            "end_row": 0,
            "has_context": bool(preceding_text or following_text)
        })

    
    # 🎯 PERFORMANCE: Batch embed all texts at once (3-5x faster than one-by-one)
    if texts:
        vectors = emb.embed_list(texts)
            
    store.add_embeddings(texts=texts, vectors=vectors, metadata_list=metadata)

def index_markdown_content(
    markdown_text: str,
    source_name: str,
    table_id_start: int = 0
) -> None:
    """
    Index raw markdown content (e.g., from PyMuPDF4LLM) into Chroma.
    Respects <!-- TABLE START --> tags to keep tables as single chunks.
    """
    emb = get_embedding_model()
    store = get_vector_store()
    texts = []
    vectors = []
    metadata = []
    
    # Split by Table markers
    # Pattern: capture segments between tags
    # This is a simple split; sophisticated parsing might be needed for nested structures
    segments = re.split(r'(<!-- TABLE START -->[\s\S]*?<!-- TABLE END -->)', markdown_text)
    
    current_id = table_id_start
    
    for segment in segments:
        if not segment.strip():
            continue
            
        segment = segment.strip()
        is_table = "<!-- TABLE START -->" in segment
        
        # Classification & Logic
        stmt_type = "Text Block"
        if is_table:
            stmt_type = "Table"
            # Try to guess type from content
            lower_seg = segment.lower()
            if "balance sheet" in lower_seg: stmt_type = "Balance Sheet"
            elif "operating income" in lower_seg: stmt_type = "Income Statement"
            elif "cash flow" in lower_seg: stmt_type = "Cash Flow Statement"
        
        # Determine Period (Simple regex for year)
        # Looking for 202x
        years = re.findall(r'202\d', segment)
        period_str = ", ".join(set(years)) if years else "Unknown"

        chunks = []
        if is_table:
            # Treat table as one big chunk usually, unless huge
            # Clean comments for embedding? Maybe keep for structure hint
            chunks.append(segment)
        else:
            # Split text paragraph by paragraph or chunks of N chars
            # Simple paragraph split
            paras = segment.split('\n\n')
            # Group paras to approx 1000 chars?
            current_chunk = ""
            for p in paras:
                if len(current_chunk) + len(p) < 1000:
                    current_chunk += "\n\n" + p
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = p
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        
        for chunk in chunks:
            texts.append(chunk)
            metadata.append({
                "source": source_name,
                "table_id": current_id,
                "stmt_type": stmt_type,
                "period": period_str,
                "type": "table_full" if is_table else "text_chunk",
                "start_row": 0,
                "end_row": 0,
                "has_context": True 
            })
            current_id += 1

    if texts:
        vectors = emb.embed_list(texts)
        store.add_embeddings(texts=texts, vectors=vectors, metadata_list=metadata)
        print(f"✅ [RAG] Indexed {len(texts)} chunks from {source_name} (Markdown Mode)")


# 🔍 RETRIEVAL
# 🔍 RETRIEVAL

FINANCIAL_SYNONYMS = {
    "loss": ["Net Income", "Net Loss", "Operating Loss", "Statement of Operations", "Consolidated Statements of Operations", "Retained Earnings"],
    "profit": ["Net Income", "Net Profit", "Operating Income", "Gross Margin", "Statement of Operations", "Consolidated Statements of Operations"],
    "profitable": ["Net Income", "Net Profit", "Operating Income", "Statement of Operations", "Consolidated"],
    "margin": ["Gross Margin", "Operating Margin", "Profit Margin"],
    "revenue": ["Net Sales", "Total Net Sales", "Turnover", "Consolidated Statements of Operations"],
    "sales": ["Net Sales", "Total Net Sales", "Revenue", "Consolidated"],
    "debt": ["Total Liabilities", "Long-Term Debt", "Short-Term Debt", "Consolidated Balance Sheets"],
    "expense": ["Cost of Sales", "Operating Expenses", "SG&A", "Research and Development", "Consolidated Statements of Operations"],
    "cash": ["Cash and Cash Equivalents", "Cash Flow", "Cash Generated by Operating Activities", "Consolidated Statements of Cash Flows"],
    "operations": ["Statement of Operations", "Consolidated Statements of Operations", "Operating Income"],
    # R&D specific synonyms
    "r&d": ["Research and Development", "R&D Expenses", "Statement of Operations", "Operating Expenses", "Consolidated Statements of Operations"],
    "research": ["Research and Development", "R&D", "Operating Expenses", "Statement of Operations"],
    "development": ["Research and Development", "R&D", "Operating Expenses"],
}

def expand_query(query: str) -> str:
    """Expand query with financial synonyms to improve retrieval recall."""
    q_lower = query.lower()
    expanded_terms = set()
    
    for key, synonyms in FINANCIAL_SYNONYMS.items():
        if key in q_lower:
            expanded_terms.update(synonyms)
    
    if expanded_terms:
        # Append synonyms to the query for embedding
        return f"{query} {' '.join(expanded_terms)}"
    return query


def retrieve_context(query: str, k: int = 15, source_filter: List[str] = None, instructions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks from vector store.
    
    🔑 INSTRUCTED RETRIEVER ENHANCEMENT:
    - Parses constraints from query (period, statement type, segment)
    - Applies ChromaDB pre-filtering before similarity search
    - Rewrites query with constraint context for better embedding alignment
    
    Args:
        query: The search query
        k: Number of results to return
        source_filter: Optional list of source filenames to filter by (for session isolation)
        instructions: Optional pre-parsed instructions (from instruction_parser)
    """
    emb = get_embedding_model()
    store = get_vector_store()
    
    # ===== INSTRUCTED RETRIEVER: STEP 1 - PARSE INSTRUCTIONS =====
    if instructions is None:
        try:
            from src.analysis.instruction_parser import parse_instructions, format_instructions_log, build_chroma_where_filter
            instructions = parse_instructions(query)
            print(format_instructions_log(instructions))
        except Exception as e:
            print(f"⚠️ [INSTRUCTED] Instruction parsing failed: {e}")
            instructions = {}
    
    # ===== INSTRUCTED RETRIEVER: STEP 2 - BUILD PRE-FILTER =====
    where_filter = None
    try:
        from src.analysis.instruction_parser import build_chroma_where_filter
        where_filter = build_chroma_where_filter(instructions, source_filter)
    except Exception as e:
        print(f"⚠️ [INSTRUCTED] Where filter build failed: {e}")
    
    # ===== INSTRUCTED RETRIEVER: STEP 3 - REWRITE QUERY =====
    try:
        from src.analysis.query_rewriter import rewrite_query_with_instructions
        enhanced_query = rewrite_query_with_instructions(query, instructions)
    except Exception as e:
        print(f"⚠️ [INSTRUCTED] Query rewrite failed: {e}")
        enhanced_query = expand_query(query)  # Fallback to synonym expansion
    
    # Also apply synonym expansion on top
    enhanced_query = expand_query(enhanced_query)
    
    # ===== RETRIEVE WITH PRE-FILTER =====
    fetch_k = k * 2  # Fetch extra for reranking
    qvec = emb.embed_text(enhanced_query)
    
    # Try with pre-filter first
    results = store.query(qvec, k=fetch_k, where_filter=where_filter)
    
    # If pre-filter returned too few results, fallback to unfiltered
    if len(results.get("documents", [])) < k // 2 and where_filter:
        print(f"⚠️ [INSTRUCTED] Pre-filter returned only {len(results.get('documents', []))} results, expanding search...")
        results = store.query(qvec, k=fetch_k, where_filter=None)
    
    candidates = []
    if results["documents"]:
        for doc_text, meta, dist in zip(results["documents"], results["metadatas"], results["distances"]):
            candidates.append({"text": doc_text, "meta": meta, "score": float(dist)})
    
    # 🔑 Source-based filtering for session isolation (if not already pre-filtered)
    if source_filter and not where_filter:
        source_filter_lower = [s.lower() for s in source_filter]
        filtered_candidates = []
        for doc in candidates:
            doc_source = doc["meta"].get("source", "").lower()
            # Check if document source matches any of the session's source files
            if any(sf in doc_source or doc_source in sf for sf in source_filter_lower):
                filtered_candidates.append(doc)
        
        if filtered_candidates:
            print(f"📂 [RAG] Filtered from {len(candidates)} to {len(filtered_candidates)} candidates (source: {source_filter})")
            candidates = filtered_candidates
        else:
            print(f"⚠️ [RAG] No candidates matched source filter {source_filter}, using all candidates")
    
    # 3. HYBRID RERANKING (Keyword Boost)
    # Give a massive boost to chunks that actually contain the metric/entity we are looking for.
    # Distance is cosine distance (lower is better), so we SUBTRACT from distance (or penalty).
    # Since Chroma returns distance, we want to minimize it.
    
    q_lower = query.lower()
    q_terms = set(q_lower.split())
    
    # Identify critical keywords
    critical_terms = []
    if "cash flow" in q_lower: critical_terms.append("cash flow")
    if "balance sheet" in q_lower: critical_terms.append("balance sheet")
    if "income" in q_lower: critical_terms.append("income")
    if "net sales" in q_lower: critical_terms.append("net sales")
    
    # 🔑 NEW: Profitability query detection - MUST include Income Statement
    is_profit_query = any(term in q_lower for term in [
        "profit", "loss", "profitable", "making money", "earnings",
        "net income", "bottom line", "profitability", "losing money"
    ])
    
    final_results = []
    income_statement_found = False
    
    for doc in candidates:
        original_dist = doc["score"]
        text_lower = doc["text"].lower()
        stmt_type = doc["meta"].get("stmt_type", "").lower()
        period = doc["meta"].get("period", "").lower()
        
        # Boost 1: Critical Statement Types
        # If user asks for "Cash Flow" and chunk is "Cash Flow Statement", HUGE boost.
        boost = 0.0
        if "cash flow" in q_lower and "cash flow" in stmt_type: boost += 0.3
        if "balance sheet" in q_lower and "balance sheet" in stmt_type: boost += 0.3
        if "income" in q_lower and "income" in stmt_type: boost += 0.3
        
        # 🔑 NEW: CRITICAL BOOST for profitability queries
        # If asking about profit/loss, ALWAYS prioritize Income Statement
        if is_profit_query:
            if "income statement" in stmt_type or "statement of operations" in stmt_type:
                boost += 0.5  # HUGE boost
                income_statement_found = True
            # Also boost chunks containing net income figures
            if "net income" in text_lower:
                boost += 0.4
            if "operating income" in text_lower:
                boost += 0.3
        
        # Boost 2: Exact Keyword matches in text
        for term in critical_terms:
            if term in text_lower:
                boost += 0.1
                
        # Boost 3: Period Match (e.g. "three months")
        if "three months" in q_lower and "three months" in text_lower: boost += 0.1
        if "six months" in q_lower and "six months" in text_lower: boost += 0.1
        
        # Apply Boost (Reduce distance)
        # Note: Cosine distance is usually 0 to 2.
        new_dist = max(0.0, original_dist - boost)
        doc["score"] = new_dist
        final_results.append(doc)
    
    # 4. Sort by new score (ASCENDING distance) and slice top k
    final_results.sort(key=lambda x: x["score"])
    
    # 🔑 NEW: CRITICAL - Ensure Income Statement is included for profit queries
    # If user asked about profit/loss but we don't have Income Statement in top k,
    # force-add by doing a secondary search
    if is_profit_query and not income_statement_found:
        # Do a specific search for "Net Income Statement of Operations"
        income_query = "Net Income Statement of Operations Consolidated"
        income_vec = emb.embed_text(income_query)
        income_results = store.query(income_vec, k=5)
        
        if income_results["documents"]:
            for doc_text, meta, dist in zip(
                income_results["documents"], 
                income_results["metadatas"], 
                income_results["distances"]
            ):
                # Check if this is actually an income statement
                if "income" in meta.get("stmt_type", "").lower() or "net income" in doc_text.lower():
                    # Add to results with high priority
                    final_results.insert(0, {
                        "text": doc_text, 
                        "meta": meta, 
                        "score": 0.0  # Highest priority
                    })
                    break
    
    return final_results[:k]

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

