# test/test_rag_integration.py
import pandas as pd
from src.ai.rag_engine import index_dataframe_to_chroma, ask

def test_rag_with_real_data():
    # Load a cleaned table (from your 108 tables)
    df = pd.read_csv("data/processed/table_10.csv")  # Pick a numeric table
    index_dataframe_to_chroma(df, "test_10q.pdf", 10)
    
    # Ask a simple question
    result = ask("What is the latest revenue value?")
    
    # Assert: Should return a number (not error/hallucination)
    assert "answer" in result
    assert isinstance(result["answer"], (int, float))
    assert result["answer"] > 0