# test/test_calculator_robustness.py
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocking modules that might not be fully available or needed for this unit test
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()

# Import the module under test
# We need to mock load_llm inside rag_engine before importing/using ask
from src.ai import rag_engine

class TestCalculatorRobustness(unittest.TestCase):
    
    @patch('src.ai.rag_engine.retrieve_context')
    @patch('src.ai.rag_engine._call_llm')
    def test_direct_variable_passing(self, mock_llm, mock_retrieve):
        """
        Verify that the system correctly calculates when variables are passed 
        directly in the LLM payload (no regex needed).
        """
        print("\n🧪 Testing Robust Calculation Engine...")
        
        # 1. Mock Context Retrieval (Simulate finding documents)
        mock_retrieve.return_value = [
            {"text": "Revenue for 2024 was $1,000,000. Cost of goods was $800,000.", "meta": {"source": "test.pdf"}}
        ]
        
        # 2. Mock LLM Response (The new JSON format)
        # LLM decides to calculate Margin = (Rev - Cost) / Rev
        mock_llm.return_value = '''
        {
            "tool": "calculator", 
            "expr": "(revenue - cost) / revenue", 
            "vars": {
                "revenue": 1000000, 
                "cost": 800000
            },
            "note": "Calculating gross margin."
        }
        '''
        
        # 3. Call ask()
        result = rag_engine.ask("What is the gross margin?")
        
        # 4. Verify Result
        print(f"   📝 Result Received: {result}")
        
        self.assertIn("answer", result)
        expected_margin = (1000000 - 800000) / 1000000 # 0.2
        self.assertAlmostEqual(result["answer"], 0.2)
        print("   ✅ Calculation Correct (0.2)")
        
        # Verify it used the note
        self.assertEqual(result.get("note"), "Calculating gross margin.")

if __name__ == "__main__":
    unittest.main()
