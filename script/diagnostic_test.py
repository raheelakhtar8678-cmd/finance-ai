# diagnostic_test.py
"""
Complete diagnostic test for API issues
"""

import os
import sys
sys.path.append(os.getcwd())

print("="*70)
print("🔍 DIAGNOSTIC TEST - API Components")
print("="*70)

# ==========================================
# 1. CHECK ENVIRONMENT
# ==========================================
print("\n1️⃣ CHECKING ENVIRONMENT VARIABLES")
from dotenv import load_dotenv
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    print(f"   ✅ GEMINI_API_KEY found (length: {len(gemini_key)})")
else:
    print("   ❌ GEMINI_API_KEY not found!")
    print("      Create .env file with: GEMINI_API_KEY=your-key")

# ==========================================
# 2. CHECK IMPORTS
# ==========================================
print("\n2️⃣ CHECKING IMPORTS")

try:
    from src.analysis.query_controller import route_query
    print("   ✅ query_controller imported")
except Exception as e:
    print(f"   ❌ query_controller failed: {e}")

try:
    from src.analysis.financial_reasoning import compute_metric_with_reasoning
    print("   ✅ financial_reasoning imported")
except Exception as e:
    print(f"   ❌ financial_reasoning failed: {e}")

try:
    from src.ai.llm_narrator import LLMNarrator
    print("   ✅ llm_narrator imported")
except Exception as e:
    print(f"   ❌ llm_narrator failed: {e}")

try:
    from src.analysis.question_router import resolve_intent
    print("   ✅ question_router imported")
except Exception as e:
    print(f"   ❌ question_router failed: {e}")

try:
    from src.analysis.metric_registry import METRIC_METADATA
    print("   ✅ metric_registry imported")
except Exception as e:
    print(f"   ❌ metric_registry failed: {e}")

# ==========================================
# 3. TEST GEMINI CONNECTION
# ==========================================
print("\n3️⃣ TESTING GEMINI CONNECTION")

try:
    from google import genai
    client = genai.Client(api_key=gemini_key)
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'working'"
    )
    
    print(f"   ✅ Gemini response: {response.text}")
except Exception as e:
    print(f"   ❌ Gemini failed: {e}")

# ==========================================
# 4. TEST QUESTION ROUTER
# ==========================================
print("\n4️⃣ TESTING QUESTION ROUTER")

try:
    from src.analysis.question_router import resolve_intent
    
    test_questions = [
        "What is the growth?",
        "Calculate burn rate",
        "Show me revenue",
        "Random question"
    ]
    
    for q in test_questions:
        metric, config = resolve_intent(q)
        if metric:
            print(f"   ✅ '{q}' → detected: {metric}")
        else:
            print(f"   ⚠️  '{q}' → no metric detected")
    
except Exception as e:
    print(f"   ❌ Question router test failed: {e}")

# ==========================================
# 5. TEST METRIC KEYWORDS
# ==========================================
print("\n5️⃣ CHECKING METRIC KEYWORDS")

try:
    from src.analysis.metric_registry import METRIC_METADATA
    
    print("\n   Registered metrics:")
    for metric, config in METRIC_METADATA.items():
        keywords = config.get("keywords", [])
        print(f"   • {metric}: {keywords}")
    
except Exception as e:
    print(f"   ❌ Metric registry check failed: {e}")

# ==========================================
# 6. TEST FINANCIAL REASONING
# ==========================================
print("\n6️⃣ TESTING FINANCIAL REASONING")

try:
    import pandas as pd
    from src.analysis.financial_reasoning import compute_metric_with_reasoning
    
    # Create dummy table
    test_df = pd.DataFrame({
        "revenue": [1000000, 1200000, 1500000],
        "year": [2022, 2023, 2024]
    })
    
    test_tables = [{"df": test_df, "source": "test.csv"}]
    
    result = compute_metric_with_reasoning("revenue_growth", test_tables)
    
    if result.get("success"):
        print(f"   ✅ Revenue growth calculated: {result.get('result')}%")
    else:
        print(f"   ⚠️  Calculation failed: {result.get('reasoning')}")
    
except Exception as e:
    print(f"   ❌ Financial reasoning test failed: {e}")

# ==========================================
# 7. TEST LLM NARRATOR
# ==========================================
print("\n7️⃣ TESTING LLM NARRATOR")

try:
    from src.ai.llm_narrator import LLMNarrator
    
    narrator = LLMNarrator()
    
    explanation = narrator.explain(
        user_question="Test question",
        rag_context="Test context",
        computed_result="Revenue: $1.2M",
        charts=None
    )
    
    print(f"   ✅ LLM explanation generated")
    print(f"   Response: {explanation[:100]}...")
    
except Exception as e:
    print(f"   ❌ LLM narrator test failed: {e}")

# ==========================================
# 8. SUMMARY
# ==========================================
print("\n" + "="*70)
print("📊 DIAGNOSTIC SUMMARY")
print("="*70)
print("""
If you see ❌ errors above:
1. Check .env file has GEMINI_API_KEY
2. Run: pip install google-genai python-dotenv
3. Check imports in query_controller.py
4. Verify metric_registry.py has "growth" keyword

If all ✅ but API still fails:
- Check uvicorn terminal for actual error messages
- The issue might be in how route_query() is being called
""")
