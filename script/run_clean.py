import pandas as pd
from pathlib import Path
from src.processing.clean_tables import clean_all_tables

RAW_DIR = Path("data/processed")
CLEAN_DIR = Path("data/clean")

CLEAN_DIR.mkdir(parents=True, exist_ok=True)

def main():
    files = list(RAW_DIR.glob("*.csv"))

    if not files:
        print("No processed tables found.")
        return

    for i, file_path in enumerate(files):
        df = pd.read_csv(file_path)
        cleaned = clean_all_tables([df])[0]  # extract single cleaned table
        
        clean_path = CLEAN_DIR / f"clean_{file_path.name}"
        cleaned.to_csv(clean_path, index=False)
        print(f"Cleaned and saved: {clean_path}")

if __name__ == "__main__":
    main()