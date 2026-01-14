
import pandas as pd
from src.ingestion.table_extractor import to_markdown_string
from src.ai.rag_engine import index_dataframe_to_chroma, retrieve_context, get_vector_store

def test_markdown_conversion():
    print("Testing Markdown Conversion...")
    df = pd.DataFrame({
        "Column 1": ["Row1", "Row2"],
        "Column 2": [100, 200]
    })
    md = to_markdown_string(df)
    print(f"Markdown Output:\n{md}")
    assert "Column 1" in md
    assert "---" in md
    print("✅ Markdown Conversion Passed")

def test_indexing_and_retrieval():
    print("\nTesting Indexing & Hybrid Retrieval...")
    # Mock DF that looks like a balance sheet
    df = pd.DataFrame({
        "Assets": ["Cash", "Inventory", "Total Assets"],
        "Sep 30, 2024": [500, 300, 800],
        "Sep 30, 2023": [400, 200, 600]
    })
    
    # 1. Index it
    # Note: This will actually write to the local vector store. 
    # We should probably use a mock or a separate collection if possible, 
    # but for this system we'll just add it and search.
    index_dataframe_to_chroma(df, "test_source", 999)
    
    # 2. Retrieve with hybrid boost
    # Query for "Cash Assets 2024"
    results = retrieve_context("Cash Assets Sep 30 2024", k=5)
    
    found = False
    for res in results:
        text = res["text"]
        print(f"Result Score: {res['score']:.4f}, Text Snippet: {text[:50]}...")
        if "Cash" in text and "500" in text:
            found = True
            break
            
    if found:
        print("✅ Retrieval Found Correct Data")
    else:
        print("❌ Retrieval Failed to find data")

if __name__ == "__main__":
    try:
        test_markdown_conversion()
        test_indexing_and_retrieval()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
