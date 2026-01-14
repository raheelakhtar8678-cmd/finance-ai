"""
Debug script to inspect RAG context for segment queries
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

from src.ai.rag_engine import retrieve_context

def debug_rag_context():
    print("="*80)
    print("DEBUGGING RAG CONTEXT FOR SEGMENT QUERIES")
    print("="*80)
    
    queries = [
        "Greater China operating income",
        "segment operating income Greater China",
        "Note 10 segment information",
        "Greater China net sales operating",
        "Greater China 6,626",
        "Americas Europe Greater China Japan operating income"
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print("="*80)
        
        contexts = retrieve_context(query, k=3)
        
        for i, ctx in enumerate(contexts):
            text = ctx.get('text', '')
            print(f"\n--- Context {i+1} ---")
            print(f"Length: {len(text)} chars")
            print(f"Content (first 500 chars):\n{text[:500]}")
            print("-"*40)

if __name__ == "__main__":
    debug_rag_context()
