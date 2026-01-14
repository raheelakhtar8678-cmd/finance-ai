# test/verify_context_fusion.py
import sys
import os
import pandas as pd
import shutil

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai.rag_engine import index_dataframe_to_chroma, retrieve_context, get_vector_store

def verify_context_indexing():
    print("🧪 Verifying Context Fusion Indexing...")
    
    # 1. Setup Mock Data
    df = pd.DataFrame({
        "Region": ["North", "South", "East", "West"],
        "Revenue": [100, 200, 150, 120]
    })
    
    # Context that is NOT in the table, but crucial for understanding
    preceding_text = "Note 10. Geographic Performance. The North region faced supply chain constraints."
    following_text = "Revenues are in millions of USD."
    
    # 2. Index with Context
    source_name = "test_context_fusion.pdf"
    
    # Clear existing test entries if possible (or just use unique source)
    # Chroma doesn't support easy delete by metadata in all versions, using distinct source
    
    print(f"📥 Indexing mock table from {source_name}...")
    index_dataframe_to_chroma(
        df=df,
        source_name=source_name,
        table_id=1,
        preceding_text=preceding_text,
        following_text=following_text
    )
    
    # 3. Validation Query: "constraints" or "Note 10"
    # These terms appear ONLY in the context, not the table itself.
    queries = [
        "What happened in the North region?", # Should match "Note 10... constraints"
        "Note 10 performance"               # Should match "Note 10"
    ]
    
    all_passed = True
    
    for q in queries:
        print(f"\n🔍 Querying: '{q}'")
        results = retrieve_context(q, k=10) # Increase k to see if it's buried
        
        found = False
        print(f"   Found {len(results)} results.")
        for i, doc in enumerate(results):
            text = doc["text"]
            meta = doc["meta"]
            score = doc["score"]
            src = meta.get("source", "unknown")
            
            print(f"   [{i}] Source: {src} | Score: {score:.4f} | Text: {text[:50]}...")
            
            if src == source_name:
                print(f"      Matched Target Source!")
                # Verify Context Presence
                if "Note 10" in text and "supply chain constraints" in text:
                    print("      ✅ Context Successfully Embedded and Retrieved!")
                    found = True
                    break
                else:
                    print(f"      ❌ matched source but Context MISSING in text! Text was: {text[:100]}")
        
        if not found:
            print(f"   ❌ FAILED: Could not retrieve table using context-only terms.")
            all_passed = False
            
    if all_passed:
        print("\n🎉 SUCCESS: Context Fusion is working! text-based queries can find tables.")
    else:
        print("\n❌ FAILURE: Context Fusion test failed.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        verify_context_indexing()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
