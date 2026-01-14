
import sys
sys.path.insert(0, '.')
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables
# Removed invalid import
from src.analysis.financial_reasoning import MetricReasoner
from src.analysis.query_controller import QueryController

# Setup
print("Initializing Verification Environment...")
pdf_path = "data/uploads/fc8b6662-f6bc-4b6d-a25e-b4cf96218de6_4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf"
tables = ingest_any_file(pdf_path)
cleaned = clean_all_tables(tables)

# Create Controller (Mocking session behavior if needed, or using Reader directly)
reasoner = MetricReasoner(cleaned, question="")

def test_query(q):
    print(f"\n❓ QUERY: {q}")
    reasoner.question = q.lower()
    # Simple keyword routing simulation or direct formula check
    if "compare" in q.lower() or "growth" in q.lower():
        # For comparison, we usually check valid metrics
        if "revenue" in q.lower():
            res = reasoner.compute_with_formula("revenue")
            print(f"   👉 RESULT: {res.get('result')}")
            print(f"   👉 PRIOR: {res.get('prior')}")
            if res.get('prior'):
                growth = ((res['result'] - res['prior']) / res['prior']) * 100
                print(f"   👉 GROWTH CALC: {growth:.2f}%")
        elif "operating income" in q.lower():
            res = reasoner.compute_with_formula("operating_income")
            print(f"   👉 RESULT: {res.get('result')}")
            print(f"   👉 PRIOR: {res.get('prior')}")
            if res.get('prior'):
                growth = ((res['result'] - res['prior']) / res['prior']) * 100
                print(f"   👉 GROWTH CALC: {growth:.2f}%")
        elif "net income" in q.lower():
            res = reasoner.compute_with_formula("net_income")
            print(f"   👉 RESULT: {res.get('result')}")
            print(f"   👉 PRIOR: {res.get('prior')}")

print("\n=== USER POV TESTING ===")
test_query("What is the total net sales for the current quarter?")
test_query("Compare revenue relative to the same period last year")
test_query("Did operating income grow compared to the prior year?")
test_query("What is the EPS?")
