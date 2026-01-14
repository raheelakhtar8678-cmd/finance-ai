
import fitz
import glob
import os

def dump_page_14():
    pdf_files = glob.glob(os.path.join("e:\\finance-ai\\data\\uploads", "*.pdf"))
    if not pdf_files:
        print("❌ No PDF found")
        return

    pdf_path = pdf_files[0]
    print(f"Dumping Page 14 from: {os.path.basename(pdf_path)}")
    
    doc = fitz.open(pdf_path)
    
    # Page 14 (Index 13)
    page = doc[13]
    text = page.get_text()
    
    with open("e:\\finance-ai\\test\\page_14_dump.txt", "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"✅ Dumped {len(text)} chars to page_14_dump.txt")
    
    # Check if 16,002 exists
    if "16,002" in text or "16002" in text:
        print("✅ Found '16,002' in text!")
    else:
        print("❌ '16,002' NOT FOUND in text.")

    # Check if 6,626 exists
    if "6,626" in text or "6626" in text:
        print("✅ Found '6,626' in text!")
    else:
        print("❌ '6,626' NOT FOUND in text.")

if __name__ == "__main__":
    dump_page_14()
