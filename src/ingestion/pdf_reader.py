import pdfplumber
from pathlib import Path

def load_pdf(path: str):
    """Load PDF and return pdfplumber object."""
    pdf_path = Path(path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    
    return pdfplumber.open(pdf_path)
