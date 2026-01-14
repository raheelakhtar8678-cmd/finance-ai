
import sys
sys.path.insert(0, '.')
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables
from src.analysis.financial_reasoning import MetricReasoner

pdf_path = "data/uploads/fc8b6662-f6bc-4b6d-a25e-b4cf96218de6_4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf"

print("Loading...")
tables = ingest_any_file(pdf_path)
cleaned = clean_all_tables(tables)
reasoner = MetricReasoner(cleaned, question="Q2 2024 results")

metrics = ["revenue", "operating_income", "eps"]
for m in metrics:
    print(f"\nCOMPUTING {m.upper()}...")
    try:
        res = reasoner.compute_with_formula(m)
        val = res.get("result")
        print(f"FINAL {m.upper()}: {val}")
        print(f"RAW DICT: {res}")
    except Exception as e:
        print(f"ERROR: {e}")
