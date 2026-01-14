# Debug script to check what tables contain the Income Statement data
import sys
sys.path.insert(0, '.')

from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables
import os

# Find the most recently uploaded PDF
upload_dir = "data/uploads"
if os.path.exists(upload_dir):
    files = sorted([f for f in os.listdir(upload_dir) if f.endswith('.pdf')], 
                   key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), 
                   reverse=True)
    
    if files:
        pdf_path = os.path.join(upload_dir, files[0])
        print(f"Analyzing: {pdf_path}\n")
        
        # Extract tables
        tables = ingest_any_file(pdf_path)
        cleaned = clean_all_tables(tables)
        
        print(f"Total tables extracted: {len(cleaned)}\n")
        print("=" * 80)
        
        # Search for Income Statement indicators
        income_statement_keywords = [
            "net income", "net sales", "operating income", 
            "research and development", "r&d", 
            "cost of sales", "gross margin",
            "earnings per share", "diluted",
            "statement of operations"
        ]
        
        for i, table in enumerate(cleaned):
            df = table["df"]
            page = table.get("page", "?")
            
            # Get full text of table
            table_text = ""
            for col in df.columns:
                table_text += str(col).lower() + " "
            for _, row in df.iterrows():
                for val in row:
                    table_text += str(val).lower() + " "
            
            # Check for Income Statement keywords
            found_keywords = []
            for kw in income_statement_keywords:
                if kw in table_text:
                    found_keywords.append(kw)
            
            if found_keywords:
                print(f"\n📊 TABLE {i} (Page {page}) - MATCHES: {found_keywords}")
                print("-" * 40)
                print(f"Columns: {list(df.columns)}")
                print(f"First column values:")
                if len(df.columns) > 0:
                    for j, val in enumerate(df.iloc[:, 0].head(15)):
                        print(f"  Row {j}: {val}")
                print("-" * 40)
        
        print("\n" + "=" * 80)
        print("DONE - If 'net income' or 'research and development' is not found above,")
        print("the Income Statement table may not be extracted correctly from the PDF.")
    else:
        print("No PDF files found in uploads directory")
else:
    print(f"Upload directory not found: {upload_dir}")
