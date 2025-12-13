import pdfplumber
import pandas as pd
from pathlib import Path

def extract_tables(pdf_path: str):
    """
    Extract all tables from a PDF file.
    Returns a list of Pandas DataFrames.
    """
    tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            
            for table in page_tables:
                if not table:  # Skip empty tables
                    continue
                    
                # Create DataFrame from table (list of rows)
                df = pd.DataFrame(table)
                
                # Remove completely empty rows and columns
                df = df.dropna(how="all", axis=1)  # remove empty columns
                df = df.dropna(how="all", axis=0)  # remove empty rows
                
                # Only add non-empty DataFrames
                if not df.empty:
                    tables.append(df)
    
    return tables
