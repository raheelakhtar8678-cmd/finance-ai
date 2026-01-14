# src/ai/rag_indexer.py

from typing import List
import pandas as pd


def table_to_text_chunks(df: pd.DataFrame) -> List[str]:
    """
    Convert table rows into searchable text chunks.
    """
    chunks = []

    headers = [str(c) for c in df.columns]

    for _, row in df.iterrows():
        parts = []
        for h, v in zip(headers, row):
            if pd.isna(v):
                continue
            parts.append(f"{h}: {v}")
        if parts:
            chunks.append(" | ".join(parts))

    return chunks
