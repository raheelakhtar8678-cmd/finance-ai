# src/ai/embeddings.py

import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """
    Wrapper for BGE-small embedding model.
    Used to embed text, tables, and financial data rows for RAG.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en"):
        print(f"[EmbeddingModel] Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string.
        """
        if not isinstance(text, str):
            text = str(text)

        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.astype(np.float32)

    def embed_list(self, items: list[str]) -> list[np.ndarray]:
        """
        Embed a list of text strings.
        """
        encoded = self.model.encode(
            items,
            normalize_embeddings=True
        )
        return [vec.astype(np.float32) for vec in encoded]

    def embed_dataframe(self, df) -> list[tuple[str, np.ndarray]]:
        """
        Convert each row of a DataFrame into a text representation + embedding.

        Returns list of tuples:
            [
                ("row text", embedding_vector),
                ...
            ]
        """
        results = []
        for _, row in df.iterrows():
            # Convert row into readable string
            row_text = ", ".join(
                f"{col}: {row[col]}" for col in df.columns
            )
            vector = self.embed_text(row_text)
            results.append((row_text, vector))

        return results


# Singleton for convenience
_embedding_instance = None

def get_embedding_model():
    """
    Ensure only one embedding model loads (saves RAM).
    """
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = EmbeddingModel()
    return _embedding_instance