import os
import pdfplumber

UPLOAD_DIR = r"e:\finance-ai\data\uploads"

def find_apple_pdf():
    for fname in os.listdir(UPLOAD_DIR):
        if not fname.endswith(".pdf"):
            continue
            
        path = os.path.join(UPLOAD_DIR, fname)
        try:
            with pdfplumber.open(path) as pdf:
                if not pdf.pages:
                    continue
                first_page = pdf.pages[0].extract_text()
                if "Apple Inc." in first_page and "March 29, 2025" in first_page:
                    print(f"FOUND: {fname}")
                    return path
        except Exception as e:
            print(f"Error reading {fname}: {e}")

if __name__ == "__main__":
    found = find_apple_pdf()
    if not found:
        print("Not found")
