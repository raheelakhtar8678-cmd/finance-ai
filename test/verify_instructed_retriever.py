# test/verify_instructed_retriever.py
"""
Verify Instructed Retriever integrates correctly with RAG pipeline.
This is a standalone test that only tests the integration points.
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

def test_integration():
    print("=" * 60)
    print("INSTRUCTED RETRIEVER - Integration Verification")
    print("=" * 60)
    
    # Test 1: Import all required modules
    print("\n📦 Test 1: Module imports...")
    try:
        from src.analysis.instruction_parser import parse_instructions, build_chroma_where_filter
        from src.analysis.query_rewriter import rewrite_query_with_instructions
        from src.ai.rag_engine import retrieve_context, expand_query
        from src.ai.vector_store import VectorStore
        print("   ✅ All modules import successfully")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Instruction parser integration
    print("\n🔍 Test 2: Instruction parser...")
    query = "What was Greater China operating income for Q2 2025?"
    instructions = parse_instructions(query)
    
    checks = [
        ("Period extracted", instructions.get("period_filter") == "Q2 2025"),
        ("Statement inferred", instructions.get("stmt_type_filter") == "Income Statement"),
        ("Segment detected", instructions.get("segment_filter") == "Greater China"),
    ]
    
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    # Test 3: Query rewriter integration
    print("\n🔄 Test 3: Query rewriter...")
    enhanced = rewrite_query_with_instructions(query, instructions)
    has_expansion = len(enhanced) > len(query)
    status = "✅" if has_expansion else "❌"
    print(f"   {status} Query expanded from {len(query)} to {len(enhanced)} chars")
    
    # Test 4: Where filter build
    print("\n🏗️ Test 4: ChromaDB filter building...")
    where_filter = build_chroma_where_filter(instructions, source_filter=["test.pdf"])
    has_filter = where_filter is not None and "$and" in where_filter
    status = "✅" if has_filter else "❌"
    print(f"   {status} Filter: {where_filter}")
    
    # Test 5: VectorStore accepts where_filter parameter
    print("\n📊 Test 5: VectorStore query signature...")
    import inspect
    sig = inspect.signature(VectorStore.query)
    has_where_param = "where_filter" in sig.parameters
    status = "✅" if has_where_param else "❌"
    print(f"   {status} VectorStore.query has where_filter parameter")
    
    # Test 6: retrieve_context accepts instructions parameter
    print("\n📊 Test 6: retrieve_context signature...")
    sig = inspect.signature(retrieve_context)
    has_instructions_param = "instructions" in sig.parameters
    status = "✅" if has_instructions_param else "❌"  
    print(f"   {status} retrieve_context has instructions parameter")
    
    # Summary
    all_passed = all([
        checks[0][1], checks[1][1], checks[2][1],
        has_expansion, has_filter, has_where_param, has_instructions_param
    ])
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL INTEGRATION CHECKS PASSED")
        print("Instructed Retriever is properly integrated with RAG pipeline")
    else:
        print("❌ SOME CHECKS FAILED - Review above")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_integration()
    exit(0 if success else 1)
