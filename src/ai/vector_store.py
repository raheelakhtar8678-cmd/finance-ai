# src/ai/vector_store.py

import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Any

class VectorStore:
    """
    A simple wrapper around ChromaDB for storing embeddings
    and performing vector similarity search.
    """

    def __init__(self, db_path: str = "./chroma_db"):
        print(f"[VectorStore] Initializing persistent DB at: {db_path}")

        self.client = chromadb.PersistentClient(path=db_path)

        # Create collection (or load if exists)
        self.collection = self.client.get_or_create_collection(
            name="financial_data",
            metadata={"hnsw:space": "cosine"}
        )

    # --------------------------
    # Insert vectors
    # --------------------------
    def add_embeddings(
        self,
        texts: List[str],
        vectors: List[np.ndarray],
        metadata_list: List[Dict[str, Any]]
    ):
        """
        Add text + embedding + metadata in one call.
        """
        ids = [f"id_{i}" for i in range(len(texts))]

        self.collection.add(
            ids=ids,
            embeddings=[v.tolist() for v in vectors],
            documents=texts,
            metadatas=metadata_list
        )

        print(f"[VectorStore] Added {len(texts)} entries to vector DB.")

    # --------------------------
    # Query
    # --------------------------
    def query(self, query_vector: np.ndarray, k: int = 5):
        """
        Query top-k most similar items.
        """
        results = self.collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=k
        )

        return {
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0],
        }


# Singleton shortcut
_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance