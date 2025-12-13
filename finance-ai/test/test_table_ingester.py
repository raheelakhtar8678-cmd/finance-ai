from pathlib import Path
from .pdf_extractor import extract_tables_from_pdf
from .excel_extractor import extract_tables_from_excel
from .csv_extractor import extract_tables_from_csv

def ingest_any_file(file_path: str) -> list:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_tables_from_pdf(file_path)
    elif ext in (".xlsx", ".xls"):
        return extract_tables_from_excel(file_path)
    elif ext == ".csv":
        return extract_tables_from_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")