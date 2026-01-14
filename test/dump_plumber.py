
import pdfplumber
import glob
import os

def dump_plumber():
    pdf_files = glob.glob(os.path.join("e:\\finance-ai\\data\\uploads", "*.pdf"))
    target = None
    for p in pdf_files:
        if "02d9d8b2" in p:
            target = p
            break
            
    if not target:
        print("❌ Target PDF NOT FOUND")
        return

    print(f"Checking pdfplumber on: {os.path.basename(target)}")
    
    with pdfplumber.open(target) as pdf:
        # Page 14 is index 13
        page = pdf.pages[13]
        text = page.extract_text()
        
        print(f"--- pdfplumber Dump ---")
        print(text[:500] if text else "NO TEXT FOUND")
        
        if text and ("16,002" in text or "16002" in text):
             print("\n✅ Found 16,002 in pdfplumber text!")
        else:
             print("\n❌ 16,002 missing in pdfplumber text")

        if text and ("6,626" in text or "6626" in text):
             print("\n✅ Found 6,626 in pdfplumber text!")
        else:
             print("\n❌ 6,626 missing in pdfplumber text")

if __name__ == "__main__":
    dump_plumber()
