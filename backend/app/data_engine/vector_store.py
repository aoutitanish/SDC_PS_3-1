"""
Vector Store Engine for KrishiMitra AI.
Provides vector similarity indexing, query embedding, and metadata-filtered retrieval.
"""
import os
import json
import logging
import joblib
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
VECTOR_DIR = os.path.join(DATA_DIR, "vector_store")
class VectorStore:
    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.documents = []
        self._load()

    def _load(self):
        vec_path = os.path.join(VECTOR_DIR, "tfidf_vectorizer.pkl")
        mat_path = os.path.join(VECTOR_DIR, "document_matrix.pkl")
        meta_path = os.path.join(VECTOR_DIR, "documents_metadata.json")

        if os.path.exists(vec_path) and os.path.exists(mat_path) and os.path.exists(meta_path):
            self.vectorizer = joblib.load(vec_path)
            self.matrix = joblib.load(mat_path)
            with open(meta_path, "r", encoding="utf-8") as fp:
                self.documents = json.load(fp)
            logger.info(f"Vector store initialized with {len(self.documents)} documents.")
        else:
            logger.warning("Vector store artifacts not found. Building now...")
            try:
                from scripts.create_embeddings import build_vector_store
                build_vector_store()
                if os.path.exists(vec_path) and os.path.exists(mat_path) and os.path.exists(meta_path):
                    self.vectorizer = joblib.load(vec_path)
                    self.matrix = joblib.load(mat_path)
                    with open(meta_path, "r", encoding="utf-8") as fp:
                        self.documents = json.load(fp)
            except Exception as e:
                logger.error(f"Failed to auto-build vector store: {e}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Searches documents using cosine similarity with optional metadata filtering."""
        if not self.vectorizer or self.matrix is None or not self.documents:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.matrix).flatten()

        # Apply metadata filters if specified
        results = []
        # Sort indices by similarity descending
        sorted_indices = np.argsort(similarities)[::-1]

        for idx in sorted_indices:
            doc = self.documents[idx]
            sim = float(similarities[idx])

            # Apply filter matching
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if v and str(v).lower() != "all" and str(v).lower() not in str(doc.get(k, "")).lower():
                        match = False
                        break
                if not match:
                    continue

            results.append({
                "doc_id": doc.get("doc_id"),
                "category": doc.get("category"),
                "title": doc.get("title"),
                "state": doc.get("state"),
                "district": doc.get("district"),
                "crop": doc.get("crop"),
                "soil_type": doc.get("soil_type"),
                "content": doc.get("content"),
                "source": doc.get("source"),
                "similarity_score": round(sim, 4)
            })

            if len(results) >= top_k:
                break

        return results


# Singleton instance
vector_store = VectorStore()
