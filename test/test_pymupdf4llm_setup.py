import time
import pymupdf4llm
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pymupdf4llm_test")

sample_pdf = Path(r"E:\finance-ai\data\raw\4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf")

if not sample_pdf.exists():
    logger.error(f"Sample PDF not found at {sample_pdf}")
    exit(1)

logger.info(f"Starting conversion of {sample_pdf.name}...")
start_time = time.time()

try:
    # PyMuPDF4LLM is synchronous and CPU based, should be fast
    md_text = pymupdf4llm.to_markdown(str(sample_pdf))
    end_time = time.time()
    
    duration = end_time - start_time
    logger.info(f"Conversion successful in {duration:.2f} seconds!")
    # Save to file for clearer inspection
    output_file = sample_pdf.with_suffix(".md")
    output_file.write_text(md_text, encoding="utf-8")
    logger.info(f"Saved markdown to {output_file}")
    
    # Check specifically for expected financial terms in table format
    if "Total net sales" in md_text:
         logger.info("Found 'Total net sales'. checking context...")
         # Find index
         idx = md_text.find("Total net sales")
         logger.info(f"Context around 'Total net sales':\n{md_text[idx:idx+200]}")
    
    # Check for table markers which ensure table extraction worked
    if "|" in md_text and "---" in md_text:
        logger.info("Table structures detected in markdown.")
    else:
        logger.warning("No table structures detected (might be expected if PDF has no tables).")

except Exception as e:
    logger.error(f"Conversion failed: {e}")
    exit(1)
