"""
Debug script to examine actual RAG context content for Greater China
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

print("="*80)
print("EXAMINING RAG CONTEXT FOR GREATER CHINA")
print("="*80)

from src.ai.rag_engine import retrieve_context

queries = [
    "greater china operating income",
    "greater china net sales segment",
    "Note 10 segment information greater china"
]

for query in queries:
    print(f"\n--- Query: {query} ---")
    contexts = retrieve_context(query, k=5)
    
    for i, ctx in enumerate(contexts[:3]):
        text = ctx.get('text', '')
        meta = ctx.get('meta', {})
        
        # Check if this mentions greater china
        if 'china' in text.lower():
            print(f"\n📄 Context {i+1} (Score: {ctx.get('score', 'N/A')}):")
            print(f"   Type: {meta.get('stmt_type', 'Unknown')}")
            print(f"   Source: {meta.get('source', 'Unknown')}")
            print(f"\n   TEXT CONTENT (first 1500 chars):")
            print("-"*60)
            print(text[:1500])
            print("-"*60)
