from pathlib import Path
import pandas as pd
from src.processing.clean_tables import clean_all_tables


def main():
    """
    Clean all extracted tables from data/processed/ 
    and save to data/cleaned/
    """
    input_dir = Path("data/processed")
    output_dir = Path("data/cleaned")
    output_dir.mkdir(exist_ok=True)
    
    # Find all CSV files
    csv_files = list(input_dir.glob("table_*.csv"))
    
    print(f"Found {len(csv_files)} tables to clean...")
    
    # Load all tables
    tables = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            tables.append((csv_file.name, df))
        except Exception as e:
            print(f"⚠️  Error reading {csv_file.name}: {e}")
    
    # Clean all tables
    print(f"Cleaning {len(tables)} tables...")
    cleaned_tables = clean_all_tables([df for _, df in tables])
    
    # Save cleaned tables
    for (original_name, _), cleaned_df in zip(tables, cleaned_tables):
        output_path = output_dir / original_name
        cleaned_df.to_csv(output_path, index=False)
    
    print(f"✅ Saved {len(cleaned_tables)} cleaned tables to {output_dir}")
    
    # Show sample from first 3 tables
    print("\n📊 Sample from first 3 cleaned tables:")
    for i in range(min(3, len(cleaned_tables))):
        print(f"\n--- Table {i} ---")
        print(f"Columns: {list(cleaned_tables[i].columns)}")
        print(cleaned_tables[i].head(3))


if __name__ == "__main__":
    main()