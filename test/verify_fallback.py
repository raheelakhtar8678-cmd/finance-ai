
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.getcwd())

from src.ai.llm_narrator import LLMNarrator

def test_fallback():
    print("🧪 Starting OpenRouter Fallback Verification...")
    
    narrator = LLMNarrator()
    
    # We want to simulate Gemini failure and see if OpenRouter is called.
    # We will patch explain_with_gemini to fail.
    # We will also patch explain_with_openrouter to just print "Called OpenRouter" and return "Success" 
    # so we don't actually need a real API key for this logic test.
    # OR, if the user WANTS to test the actual key, we should let it run. 
    # But usually, we first check the logic. 
    # Let's try to let it run real requests if possible, but fallback to mocking if keys aren't there.
    
    print("\n[Case 1] Simulating Gemini Crash -> Checking if it tries OpenRouter")
    
    with patch('src.ai.llm_narrator.explain_with_gemini') as mock_gemini:
        mock_gemini.side_effect = Exception("💥 Simulated Gemini API Outage 💥")
        
        # We wrap explain_with_openrouter to track if it was called, but let it execute (or fail if no key)
        # Actually, to confirm "working", capturing the log output is best.
        
        try:
            result = narrator.explain(
                user_question="What is 2+2?", 
                rag_context="Math context", 
                computed_result="4"
            )
            print(f"\n✅ Final Result: {result[:50]}...")
        except Exception as e:
            print(f"\n❌ Final execution failed: {e}")

if __name__ == "__main__":
    test_fallback()
