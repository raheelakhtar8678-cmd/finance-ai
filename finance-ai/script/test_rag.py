# script/test_rag.py
import sys
import os
sys.path.append(os.getcwd())

from src.ai.embeddings import get_embedding_model
from src.ai.vector_store import get_vector_store
from src.ai.rag_engine import index_dataframe_to_chroma, retrieve_context

def test_rag_pipeline():
    print("1. Loading embedding model...")
    emb = get_embedding_model()
    vec = emb.embed_text("Test embedding")
    print(f"   → Embedding shape: {vec.shape}")

    print("2. Initializing ChromaDB...")
    store = get_vector_store()
    print("   → ChromaDB ready")

    print("3. Indexing a sample table...")
    import pandas as pd
    df = pd.DataFrame({
        "revenue": [1000000, 1200000],
        "net_income": [200000, 180000],
        "cash": [500000, 450000]
    })
    index_dataframe_to_chroma(df, "test_10q.pdf", 0)
    print("   → Table indexed")

    print("4. Testing retrieval...")
    results = retrieve_context("What is the latest cash balance?")
    print(f"   → Retrieved {len(results)} chunks")
    for i, doc in enumerate(results):
        print(f"     [{i+1}] {doc['text'][:80]}...")

    print("\n✅ RAG pipeline works (without LLM)")

if __name__ == "__main__":
    test_rag_pipeline()