# test/test_ambiguity.py
import sys
import os
import unittest
import pandas as pd
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock UI modules
sys.modules["gradio"] = MagicMock()
sys.modules["gradio.components"] = MagicMock()

from src.analysis import query_controller

class TestAmbiguity(unittest.TestCase):
    
    def test_sales_vs_income_disambiguation(self):
        """
        Verify that when both 'Net Sales' and 'Operating Income' tables exist,
        querying for 'Operating Income' retrieves the correct value ($6,626)
        and NOT the Sales value ($16,002).
        """
        print("\n🧪 Testing Disambiguation: Sales vs Operating Income...")
        
        # Table 1: Net Sales by Segment
        # Does NOT contain "Total Operating Income" row.
        df_sales = pd.DataFrame({
            "Segment": ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific", "Total Net Sales"],
            "March 29, 2025": ["21,000", "14,000", "16,002", "5,500", "3,500", "60,000"],
            "March 30, 2024": ["20,000", "13,000", "16,372", "5,400", "3,400", "58,000"]
        })
        
        # Table 2: Operating Income by Segment
        # HAS "Total Operating Income" row.
        df_income = pd.DataFrame({
            "Segment": ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific", "Total Operating Income"],
            "March 29, 2025": ["7,000", "4,000", "6,626", "1,500", "1,000", "20,126"],
            "March 30, 2024": ["6,800", "3,900", "6,700", "1,400", "900", "19,700"]
        })
        
        mock_tables = [
            {"df": df_sales, "page": 27}, 
            {"df": df_income, "page": 28}
        ]
        
        question = "What was the operating income for Greater China in 2025?"
        
        # Run Route Query
        result = query_controller.route_query(question, mock_tables)
        
        print(f"   📝 Router Result (Answer): {result.get('answer')}")
        
        answer_text = str(result.get("answer", ""))
        
        # Critical Verification
        # Should be 6,626 (Income), NOT 16,002 (Sales)
        self.assertIn("6,626", answer_text, "❌ Failed: Did not extract the correct Operating Income ($6,626).")
        self.assertNotIn("16,002", answer_text, "❌ Failed: Incorrectly extracted Net Sales ($16,002) as Income.")
        
        print("   ✅ SUCCESS: Correctly disambiguated Income from Sales.")

if __name__ == "__main__":
    unittest.main()
