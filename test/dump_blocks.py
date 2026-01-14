
import fitz
import glob
import os

def dump_blocks():
    pdf_files = glob.glob(os.path.join("e:\\finance-ai\\data\\uploads", "*.pdf"))
    target = None
    for p in pdf_files:
        if "02d9d8b2" in p:
            target = p
            break
            
    if not target:
        print("❌ Target PDF 02d9d8b2 NOT FOUND")
        return

    print(f"Checking Blocks on: {os.path.basename(target)}")
    doc = fitz.open(target)
    page = doc[13] # Page 14
    
    # Check words
    words = page.get_text("words")
    found_16002 = False
    found_6626 = False
    
    print(f"Scanning {len(words)} words...")
    for w in words:
        # w is (x0, y0, x1, y1, "string", block_no, line_no, word_no)
        text = w[4]
        if "16,002" in text or "16002" in text:
             print(f"✅ Found 16,002 in words! {w}")
             found_16002 = True
        if "6,626" in text or "6626" in text:
             print(f"✅ Found 6,626 in words! {w}")
             found_6626 = True
             
    if not found_16002:
        print("❌ 16,002 still missing in 'words' mode")
    if not found_6626:
        print("❌ 6,626 still missing in 'words' mode")

if __name__ == "__main__":
    dump_blocks()
