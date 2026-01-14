
import sys
import traceback
from src.analysis.query_controller import route_query
from src.analysis.cfo_insights import CFOInsights

# Mock tables to simulate data
mock_tables = [
    {
        "source": "2025_report.pdf",
        "df": None,
        "markdown": "| Greater China | 16002 | 6626 |\n| Japan | 7000 | 2000 |",
        "page": 1,
        "preceding_text": "Three Months Ended March 29, 2025",
        "following_text": ""
    },
    {
        "source": "2024_report.pdf",
        "df": None,
        "markdown": "| Greater China | 17812 | 7531 |\n| Japan | 6000 | 1000 |",
        # Use a clearly different date to trigger comparison
        "page": 1,
        "preceding_text": "Three Months Ended March 30, 2024",
        "following_text": ""
    }
]

def test_query():
    print("🚀 Starting reproduction test...")
    try:
        # Mocking chart_gen as None to avoid filesystem operations
        answer, chart = route_query(
            question="How did Greater China perform in 2025 vs 2024?",
            tables=mock_tables,
            chart_gen=None,
            session_id="test_session"
        )
        print("✅ Query Successful!")
        print("Answer Preview:", answer[:200])
    except Exception:
        print("❌ CRASH DETECTED!")
        traceback.print_exc()

if __name__ == "__main__":
    test_query()
