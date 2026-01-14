
import fitz
import re
import os

PDF_PATH = r"e:/finance-ai/data/uploads/119a8e66-0803-40db-9ff1-614d46365b5f_618374cc-0b7e-4007-8f49-da55758e5811.pdf"

print(f"Checking {PDF_PATH}...")
if not os.path.exists(PDF_PATH):
    print("❌ File not found!")
    exit(1)

doc = fitz.open(PDF_PATH)
print(f"Opened PDF with {len(doc)} pages.")

# Note 10 is usually around page 14-16
start_page = 13 # 0-indexed, so page 14
end_page = 16

found = False
for i in range(start_page, end_page + 1):
    page = doc[i]
    text = page.get_text()
    
    if "Greater China" in text or "Note 10" in text:
        print(f"\n--- Page {i+1} ---")
        # Print context around Greater China
        if "Greater China" in text:
            print("✅ Found 'Greater China'!")
            found = True
            
            # Show the raw text around it to verify numbers are intact
            idx = text.find("Greater China")
            start = max(0, idx - 100)
            end = min(len(text), idx + 200)
            snippet = text[start:end]
            print(f"CONTEXT SNIPPET:\n{snippet}")
            
            # Test the regex pattern from our code
            print("\nTESTING REGEX:")
            segment_name = "Greater China"
            segment_pattern = rf"{re.escape(segment_name)}[:\s]*\$?\s*([\d,]+)[.\s]*\$?\s*([\d,]+)?"
            match = re.search(segment_pattern, text, re.IGNORECASE)
            if match:
                print(f"MATCH: {match.groups()}")
            else:
                print("❌ Regex did not match!")
        else:
            print("Found 'Note 10' but not 'Greater China'")

doc.close()
