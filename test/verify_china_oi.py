
from src.ingestion.pymupdf_extractor import extract_segment_values_direct
import glob
import os

def test_extraction():
    # Find the PDF
    pdf_files = glob.glob(os.path.join("e:\\finance-ai\\data\\uploads", "*.pdf"))
    if not pdf_files:
        print("❌ No PDF found")
        return

    print(f"Found {len(pdf_files)} PDFs. Testing all...")
    
    for pdf_path in pdf_files:
        print(f"\n==================================================")
        print(f"Testing PyMuPDF on: {os.path.basename(pdf_path)}")
        
        # Run extraction for "Greater China"
        result = extract_segment_values_direct(pdf_path, "Greater China")
        
        # Print raw results
        print(f"--- RESULTS for {os.path.basename(pdf_path)} ---")
        print(f"Success: {result['success']}")
        print(f"Net Sales: {result['net_sales']}")
        print(f"Operating Income: {result['operating_income']}")
        
        # Check against 2025 Truth
        expected_oi_2025 = 6626000000.0
        expected_ns_2025 = 16002000000.0
        
        if result['operating_income'] == expected_oi_2025:
             print("✅ MATCHES 2025 TRUTH (Operating Income = 6,626 M)")
        elif result['net_sales'] == expected_ns_2025:
             print("✅ MATCHES 2025 TRUTH (Net Sales = 16,002 M)")
        
        # Check against 2024 Truth
        expected_oi_2024 = 6700000000.0
        if result['operating_income'] == expected_oi_2024:
             print("ℹ️ Matches 2024 Truth (Operating Income = 6,700 M) - Old Report?")

if __name__ == "__main__":
    test_extraction()
