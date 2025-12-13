import pandas as pd


def find_relevant_tables(cleaned_tables: dict, required_cols: list):
    matches = []

    for filename, tables in cleaned_tables.items():
        for idx, df in enumerate(tables):
            cols = [c.lower() for c in df.columns]
            if any(req in " ".join(cols) for req in required_cols):
                matches.append((filename, idx, df))

    return matches