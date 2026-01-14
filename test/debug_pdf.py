"""
Debug script to test segment extraction from actual PDF
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

from src.ingestion.table_extractor import extract_tables
from src.analysis.financial_reasoning import MetricReasoner

# Use the identified Apple Q2 2025 PDF
PDF_PATH = r"e:\finance-ai\data\uploads\119a8e66-0803-40db-9ff1-614d46365b5f_618374cc-0b7e-4007-8f49-da55758e5811.pdf"

def debug_segment_extraction():
    print("="*80)
    print("DEBUGGING SEGMENT EXTRACTION FROM LIVE PDF")
    print("="*80)
    
    # 1. Extract tables
    print(f"\n📄 Extracting tables from: {PDF_PATH}")
    tables = extract_tables(PDF_PATH)
    print(f"✅ Extracted {len(tables)} tables")
    
    # 2. Search for tables containing "Greater China" AND "Operating Income"
    print("\n" + "="*80)
    print("SEARCHING FOR SEGMENT TABLES...")
    print("="*80)
    
    segment_tables = []
    for i, table in enumerate(tables):
        df = table["df"]
        markdown = table.get("markdown", "")
        preceding = table.get("preceding_text", "")
        
        # Check if table contains both segment info AND operating income
        table_text = (markdown + " " + preceding + " " + df.to_string()).lower()
        
        has_greater_china = "greater china" in table_text or "china" in table_text
        has_operating_income = "operating income" in table_text or "segment operating" in table_text
        has_net_sales = "net sales" in table_text or "sales by" in table_text
        
        if has_greater_china:
            segment_tables.append({
                "index": i,
                "page": table.get("page"),
                "has_op_income": has_operating_income,
                "has_net_sales": has_net_sales,
                "preceding": preceding[:200] if preceding else "None",
                "df_preview": df.head(10).to_string()
            })
    
    print(f"\n📊 Found {len(segment_tables)} tables with 'Greater China':")
    for st in segment_tables:
        print(f"\n--- Table {st['index']} (Page {st['page']}) ---")
        print(f"  Has Operating Income: {st['has_op_income']}")
        print(f"  Has Net Sales: {st['has_net_sales']}")
        print(f"  Preceding Text: {st['preceding'][:100]}...")
        print(f"  DataFrame Preview:\n{st['df_preview']}")
    
    # 3. Test compute_matrix_metric
    print("\n" + "="*80)
    print("TESTING compute_matrix_metric")
    print("="*80)
    
    reasoner = MetricReasoner(tables, question="What is the operating income for Greater China?")
    
    # Test Operating Income
    print("\n🔍 Testing: Operating Income for Greater China")
    result = reasoner.compute_matrix_metric("operating_income", "greater china")
    print(f"  Success: {result.get('success')}")
    print(f"  Result: {result.get('result')}")
    print(f"  Reasoning: {result.get('reasoning')}")
    
    # Test Net Sales (Revenue)
    print("\n🔍 Testing: Net Sales for Greater China")
    result_sales = reasoner.compute_matrix_metric("revenue", "greater china")
    print(f"  Success: {result_sales.get('success')}")
    print(f"  Result: {result_sales.get('result')}")
    print(f"  Reasoning: {result_sales.get('reasoning')}")

if __name__ == "__main__":
    debug_segment_extraction()
