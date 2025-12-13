from src.ingestion.table_extractor import extract_tables
from src.ingestion.table_saver import save_tables_to_csv

PDF_PATH = "data/raw/test.pdf"

def main():
    tables = extract_tables(PDF_PATH)
    saved = save_tables_to_csv(tables)

    print(f"Extracted {len(tables)} tables.")
    print("Saved files:")
    for f in saved:
        print(f" - {f}")

if __name__ == "__main__":
    main()