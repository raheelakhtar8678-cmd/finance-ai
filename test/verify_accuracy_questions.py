import pymupdf4llm
from pathlib import Path
import logging
import sys
sys.path.append(r"e:\finance-ai\src")
from processing.clean_tables import TableCleaner

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("accuracy_verifier")

cleaner = TableCleaner()

pdf_2024 = Path(r"E:\finance-ai\data\raw\4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf")
pdf_2025 = Path(r"E:\finance-ai\data\raw\618374cc-0b7e-4007-8f49-da55758e5811.pdf")

def process_pdf(pdf_path):
    if not pdf_path.exists():
        logger.error(f"{pdf_path} not found!")
        return None
    
    logger.info(f"Processing {pdf_path.name}...")
    # 1. Convert to Markdown
    md_text = pymupdf4llm.to_markdown(str(pdf_path))
    
    # 2. Clean Tables
    cleaned_text = cleaner.clean_text(md_text)
    
    # Save
    out_path = pdf_path.with_suffix(".md")
    out_path.write_text(cleaned_text, encoding="utf-8")
    logger.info(f"Saved to {out_path.name}")
    return cleaned_text

logger.info("--- Converting PDFs ---")
md_2024 = process_pdf(pdf_2024)
md_2025 = process_pdf(pdf_2025)

if not md_2024 or not md_2025:
    logger.error("Missing PDF data, cannot verify.")
    exit(1)

logger.info("\n--- Verifying Question 1: Greater China Operating Income ---")
# Look for 'Greater China' in segment info (Note 10 usually)
# Context: "Greater China", "Operating income"
# We'll just regex search specifically for the values mentioned in fact check to see if they exist in the text
# Fact: 2024=$6,700 (Wait, user said 2024 in the question, but the PDF is Q2 2024. 
# The user fact check says: "It was $6,700 million in 2024 and dropped to $6,626 million in 2025."
# We should verification if "Greater China" row contains these numbers.

def check_greater_china(text, year_label):
    if "Greater China" in text:
        idx = text.find("Greater China")
        # Grab snippet
        snippet = text[idx:idx+500] 
        logger.info(f"[{year_label}] 'Greater China' Snippet:\n{snippet}...")
    else:
        logger.warning(f"[{year_label}] 'Greater China' not found in text.")

check_greater_china(md_2024, "2024 Report")
check_greater_china(md_2025, "2025 Report")


logger.info("\n--- Verifying Question 2: Repurchases (Cash Flow) ---")
# Fact: 2025 = 49,504; 2024 = 43,344 (for six months)
# Search for these keywords and values
def check_repurchases(text, year_label):
    term = "Repurchases of common stock"
    if term in text:
        idx = text.find(term)
        snippet = text[idx:idx+300]
        logger.info(f"[{year_label}] '{term}' Snippet:\n{snippet}...")
    else:
        logger.warning(f"[{year_label}] '{term}' not found.")

check_repurchases(md_2024, "2024 Report")
check_repurchases(md_2025, "2025 Report")


logger.info("\n--- Verifying Question 3: RSU Unrecognized Cost ---")
# Fact: 26.3 billion, 2.7 years. In 2025 report.
def check_rsu(text, year_label):
    term = "unrecognized compensation cost"
    if term in text:
        idx = text.find(term)
        snippet = text[idx:idx+400]
        logger.info(f"[{year_label}] '{term}' Snippet:\n{snippet}...")
    else:
         logger.warning(f"[{year_label}] '{term}' not found.")

check_rsu(md_2025, "2025 Report")

logger.info("\n--- Verifying Question 4: Risk Factors (MD&A) ---")
# Fact: Mention of "Section 232 investigation" in 2025
def check_risk(text, year_label):
    term = "Section 232"
    if term in text:
         idx = text.find(term)
         snippet = text[max(0, idx-100):idx+300]
         logger.info(f"[{year_label}] Found '{term}':\n{snippet}...")
    else:
         logger.info(f"[{year_label}] '{term}' NOT found (as expected if this is the generic guide or if it's new).")

check_risk(md_2024, "2024 Report")
check_risk(md_2025, "2025 Report")
