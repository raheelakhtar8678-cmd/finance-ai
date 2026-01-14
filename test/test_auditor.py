# test/test_auditor.py
import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai.auditor import FinancialAuditor, AuditResult

class TestFinancialAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = FinancialAuditor()
    
    def test_valid_response(self):
        """Standard valid response should pass."""
        rag_response = {
            "answer": "For Q2 2025, Apple reported Total Net Sales of $90,753 million and Operating Income of $27,900 million."
        }
        result = self.auditor.verify(rag_response)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.issues), 0)
        
    def test_hierarchy_violation_income(self):
        """Revenue < Operating Income should fail."""
        # Scenario: Revenue = 10k, Op Income = 20k (Impossible)
        rag_response = {
            "answer": "We found Net Sales of $10,000 million but Operating Income was surprisingly higher at $20,000 million."
        }
        result = self.auditor.verify(rag_response)
        self.assertFalse(result.passed)
        self.assertTrue(any("Logic Error" in i for i in result.issues))
        print(f"\n[Test] Caught Violation: {result.issues}")

    def test_hierarchy_violation_net_income(self):
        """Revenue < Net Income should fail."""
        rag_response = {
            "answer": "Revenue was $50B, but Net Income was $60B due to a tax benefit." 
            # Technically possible with huge tax benefit? 
            # Our strict rule might flagging it is good for an 'Auditor' to at least warn.
        }
        result = self.auditor.verify(rag_response)
        # Depending on logic strictness. In our current code:
        # rev=50e9, net=60e9 -> fail
        self.assertFalse(result.passed)

    def test_insufficient_data(self):
        """Insufficient data should skip audit."""
        rag_response = {
            "answer": "Insufficient data to determine the profit margin."
        }
        result = self.auditor.verify(rag_response)
        self.assertTrue(result.passed)

if __name__ == "__main__":
    unittest.main()
