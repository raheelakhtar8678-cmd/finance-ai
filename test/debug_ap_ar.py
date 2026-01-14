
import sys
sys.path.insert(0, '.')
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

# Inspect Table 5 (Balance Sheet)
print("\n" + "="*50)
print("INSPECTING TABLE 5 (Balance Sheet)")
print("="*50)

if len(cleaned_tables) > 5:
    bs_table = cleaned_tables[5]["df"] # Table 5 is index 5? Or 4? Step 243 said Table 5 (Page 6).
    # Step 243 said "POTENTIAL MATCH: TABLE 5". So index 5.
    
    print(f"Columns: {bs_table.columns.tolist()}")
    for idx, row in bs_table.iterrows():
        # check for 'pay' or 'able'
        r_str = str(row.values).lower()
        if "pay" in r_str or "able" in r_str:
            print(f"Row {idx}:")
            print(row.to_string())
            print("-" * 20)

# Run reasoning for Accounts Payable
print("\n" + "="*50)
print("DEBUGGING ACCOUNTS PAYABLE")
print("="*50)
reasoner = MetricReasoner(cleaned_tables, "What is the accounts payable?")
result_ap = reasoner.compute_with_formula("accounts_payable")
print(f"Result: {result_ap}")

# Run reasoning for Accounts Receivable
print("\n" + "="*50)
print("DEBUGGING ACCOUNTS RECEIVABLE")
print("="*50)
result_ar = reasoner.compute_with_formula("accounts_receivable")
print(f"Result: {result_ar}")

print("\n" + "="*50)
print("INTERNAL REASONING LOGS")
print("="*50)
# Filter logs for relevant keywords
for log in reasoner.reasoning_log:
    if any(k in log.lower() for k in ["payable", "receivable", "extracted"]):
        print(log)
