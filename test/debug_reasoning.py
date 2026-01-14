
import sys
sys.path.insert(0, '.')
import pandas as pd
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables
from src.analysis.financial_reasoning import MetricReasoner

# Use latest uploaded Apple 10-Q
pdf_path = "data/uploads/fc8b6662-f6bc-4b6d-a25e-b4cf96218de6_4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf"

print("Loading tables...")
tables = ingest_any_file(pdf_path)
cleaned_tables = clean_all_tables(tables)

# Mark source
for t in cleaned_tables:
    t["source"] = "Apple 10-Q"

print(f"Loaded {len(cleaned_tables)} tables.")

# Run reasoning
reasoner = MetricReasoner(cleaned_tables, "What are the inventory levels?")
# 'inventory' maps to formula 'inventory' in registry
result = reasoner.compute_with_formula("inventory")

print("\n" + "="*50)
print("REASONING LOGS:")
print("="*50)
for log in reasoner.reasoning_log:
    print(log)

print(f"\nFinal Result: {result}")
