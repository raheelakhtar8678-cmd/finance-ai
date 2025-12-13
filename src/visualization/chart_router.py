import pandas as pd

def find_chartable_tables(tables):
    candidates = []
    for t in tables:
        df = t["df"]
        numeric_cols = df.select_dtypes("number").columns
        if len(numeric_cols) >= 1:
            candidates.append({
                "source": t["source"],
                "df": df,
                "cols": numeric_cols.tolist()
            })
    return candidates