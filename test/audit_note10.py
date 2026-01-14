import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.pymupdf_extractor import extract_markdown_with_pymupdf
import fitz

pdf_path = r"e:\finance-ai\data\uploads\db2bb6ec-b906-4923-b718-b767cab60dd8_2025_report.pdf"

print(f"📄 Auditing PDF: {pdf_path}")

# Get Markdown content
res = extract_markdown_with_pymupdf(pdf_path)
md = res[0]["markdown"]

# Find Segment Information section
# Note 10 is usually the one
start_keywords = ["Note 10", "Segment Information", "Geographic Data"]
found_note = False
for k in start_keywords:
    idx = md.lower().find(k.lower())
    if idx != -1:
        print(f"✅ Found '{k}' at index {idx}")
        # Print a large window around it
        print("\n--- NOTE 10 CONTENT ---")
        window = md[idx:idx+4000]
        print(window)
        print("--- END ---")
        found_note = True
        break

if not found_note:
    print("❌ Could not find Note 10 in Markdown. Trying raw text search.")
    doc = fitz.open(pdf_path)
    for page in doc:
        text = page.get_text()
        if "Greater China" in text:
            print(f"✅ Found 'Greater China' on page {page.number + 1}")
            print(text)
    doc.close()
