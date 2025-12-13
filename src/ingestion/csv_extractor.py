import pandas as pd

def extract_tables_from_csv(file_path: str) -> list[pd.DataFrame]:
    df = pd.read_csv(file_path)
    if df.empty:
        return []
    return [df]