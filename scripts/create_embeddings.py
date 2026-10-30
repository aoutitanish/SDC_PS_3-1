"""
Vector Index & Metadata Store Builder for KrishiMitra AI.
Builds searchable semantic & lexical vector representations with metadata filtering.
"""

import os
import json
import logging
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge_base")
VECTOR_DIR = os.path.join(DATA_DIR, "vector_store")
os.makedirs(VECTOR_DIR, exist_ok=True)


def build_vector_store():
    kb_path = os.path.join(KNOWLEDGE_DIR, "agricultural_knowledge_documents.json")
    if not os.path.exists(kb_path):
        logger.error("Knowledge base documents not found. Run ingest_data.py first.")
        return

    with open(kb_path, "r", encoding="utf-8") as fp:
        documents = json.load(fp)

    logger.info(f"Loaded {len(documents)} knowledge documents for vector indexing.")

    # Create enriched corpus with title, metadata tags, and content
    corpus = []
    for doc in documents:
        text = f"{doc.get('title', '')} | {doc.get('state', '')} | {doc.get('district', '')} | {doc.get('soil_type', '')} | {doc.get('crop', '')} | {doc.get('category', '')} | {doc.get('content', '')}"
        corpus.append(text)

    # Train sublinear TF-IDF vectorizer with n-grams
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=12000,
        sublinear_tf=True,
        stop_words="english"
    )
    matrix = vectorizer.fit_transform(corpus)

    # Save artifacts
    joblib.dump(vectorizer, os.path.join(VECTOR_DIR, "tfidf_vectorizer.pkl"))
    joblib.dump(matrix, os.path.join(VECTOR_DIR, "document_matrix.pkl"))

    with open(os.path.join(VECTOR_DIR, "documents_metadata.json"), "w", encoding="utf-8") as fp:
        json.dump(documents, fp, indent=2, ensure_ascii=False)

    logger.info(f"Vector store successfully built with {matrix.shape[0]} documents and {matrix.shape[1]} features!")


if __name__ == "__main__":
    build_vector_store()
