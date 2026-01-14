# src/ai/vector_store.py

import chromadb
from chromadb.config import Settings
import numpy as np
import uuid
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
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]

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
    def query(self, query_vector: np.ndarray, k: int = 5, where_filter: dict = None):
        """
        Query top-k most similar items.
        
        Args:
            query_vector: Embedding vector for similarity search
            k: Number of results to return
            where_filter: Optional ChromaDB where clause for metadata filtering.
                          Applied BEFORE similarity search (pre-filtering).
                          Example: {"stmt_type": {"$eq": "Income Statement"}}
        """
        query_params = {
            "query_embeddings": [query_vector.tolist()],
            "n_results": k
        }
        
        # Apply metadata pre-filter if provided
        if where_filter:
            query_params["where"] = where_filter
            print(f"🔍 [VectorStore] Pre-filtering with: {where_filter}")
        
        try:
            results = self.collection.query(**query_params)
        except Exception as e:
            # Fallback: If where filter fails (invalid field, etc.), retry without it
            print(f"⚠️ [VectorStore] Where filter failed ({e}), falling back to unfiltered search")
            results = self.collection.query(
                query_embeddings=[query_vector.tolist()],
                n_results=k
            )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }


# Singleton shortcut
_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance