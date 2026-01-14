
import sys
from unittest.mock import MagicMock

# Mock LLM Narrator since we don't want to call actual LLM in unit test
class MockNarrator:
    def explain(self, user_question, rag_context, computed_result, charts):
        return computed_result # Return the prompt text so we can inspect it

sys.modules["src.ai.llm_narrator"] = MagicMock()
sys.modules["src.ai.llm_narrator"].LLMNarrator = MockNarrator

from src.analysis.query_controller import generate_metric_answer

def test_cfo_advisory():
    # Test Case 1: Revenue Decline (Negative)
    metric_result = {
        "result": 50000000.0, # 50M
        "prior": 60000000.0,  # 60M (Decline)
        "period_date": "Q1 2025",
        "prior_date": "Q1 2024",
        "confidence": 0.9,
        "source": "Test",
        "reasoning": "Extracted from Table for Segment 'Greater China'"
    }
    
    question = "How is Greater China revenue performing?"
    
    print("\n🧐 Testing CFO Advisory Generation (Revenue Decline)...")
    output = generate_metric_answer(question, metric_result, metric_name="revenue")
    
    print("-" * 50)
    print(output)
    print("-" * 50)
    
    if "CFO STRATEGIC ADVISORY" in output:
        print("✅ SUCCESS: CFO Advisory section present.")
    else:
        print("❌ FAILURE: CFO Advisory section missing.")
        
    if "Action Required" in output and "Top-line contraction" in output:
        print("✅ SUCCESS: Correct 'Action Required' advice generated for revenue decline.")
    else:
        print("❌ FAILURE: Incorrect advice text.")

if __name__ == "__main__":
    test_cfo_advisory()
