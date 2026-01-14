# test/repro_live_failure.py
import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock things we don't want to actually load (like UI)
sys.modules["gradio"] = MagicMock()
sys.modules["gradio.components"] = MagicMock()

# Import the actual controller
from src.analysis import query_controller

# We need to mock the RAG engine to return "Not Found" so we can test if the deterministic logic kicks in.
# OR, if we want to test the full stack, we need to ingest the data first or mock the data sources.
# Since ingestion is slow/complex, we'll try to rely on the fact that query_controller.route_query 
# SHOULD call compute_metric_with_reasoning first.

class TestLiveFailure(unittest.TestCase):
    
    def test_routing_priority(self):
        """
        Verify that a query for 'Greater China Operating Income' routes to the deterministic extractor 
        AND returns the correct value, rather than falling back to RAG/Hallucination.
        """
        print("\n🧪 Testing Live Routing for 'Greater China Operating Income'...")
        
        # 1. Mock the Dataframes (Simulation of loaded state)
        # We need to inject the mock dataframe into the processing context used by financial_reasoning
        # financial_reasoning.MetricReasoner(dfs)
        
        import pandas as pd
        
        # This table represents the "Segment Information"
        df_segment = pd.DataFrame({
            "Segment": ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific", "Total Operating Income"],
            "March 29, 2025": ["12,000", "7,000", "6,626", "2,500", "1,500", "29,000"],
            "March 30, 2024": ["11,500", "6,500", "6,700", "2,400", "1,400", "28,000"]
        })
        # Tag it so our logic knows it's a table
        # We might need to mock how `query_controller` accesses data.
        # It typically gets 'dfs' passed or loads them.
        
        # The Route Query signature expects 'dfs' to be a list of dicts like [{"df": df, "page": 1}] 
        # OR just a list of dfs depending on implementation. 
        # Based on crash logs: self._heal_df(table["df"]) -> it expects dicts.
        
        mock_tables = [{"df": df_segment, "page": 28}]
        
        question = "What was the operating income for Greater China in 2025?"
        
        # Run Route Query
        result = query_controller.route_query(question, mock_tables)
        
        print(f"   📝 Router Result: {result}")
        
        # Assertions
        # 1. Should be successful
        self.assertTrue(result.get("success"), "Query routing failed")
        
        # 2. Should have the correct number 6,626
        answer_text = str(result.get("answer", ""))
        self.assertIn("6,626", answer_text, "Failed to extract 6,626")
        
        # 3. Should mention "Operating Income" not "Net Sales"
        self.assertIn("Operating Income", answer_text, "Answer incorrectly labeled")

if __name__ == "__main__":
    unittest.main()
