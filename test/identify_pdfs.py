import pymupdf4llm
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdf_identifier")

files = [
    Path(r"E:\finance-ai\data\raw\4f867b9d-a765-495e-8d72-cadd4f12036f.pdf"),
    Path(r"E:\finance-ai\data\raw\618374cc-0b7e-4007-8f49-da55758e5811.pdf")
]

for pdf_path in files:
    if not pdf_path.exists():
        logger.warning(f"File not found: {pdf_path}")
        continue
    
    # Just read first page or 2000 chars to identify
    try:
        # pymupdf4llm reads whole file, so we'll just read it and slice raw text
        # for speed, maybe just standard pymupdf is better, but let's consistency use the tool we chose
        md_text = pymupdf4llm.to_markdown(str(pdf_path))
        header = md_text[:2000]
        
        logger.info(f"=== File: {pdf_path.name} ===")
        # Look for date
        if "2025" in header:
            logger.info("FOUND 2025 MARKER")
        if "Quarterly Report" in header:
             logger.info("Found 'Quarterly Report' type")
        
        logger.info(f"Header Snippet:\n{header[:300]}")
        
    except Exception as e:
        logger.error(f"Failed to read {pdf_path.name}: {e}")
