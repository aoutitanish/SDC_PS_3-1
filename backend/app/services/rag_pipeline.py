"""
KrishiMitra AI -- Hybrid RAG Pipeline (services/rag_pipeline.py)

Implements:
  1. TF-IDF cosine similarity retrieval (via existing vector store infrastructure)
  2. BM25 lexical retrieval (rank-bm25 or pure-python fallback)
  3. Hybrid merge and deduplication
  4. Metadata filtering (crop, region/state, season, language, topic)
  5. Source citation with full provenance: institution, publication, URL, retrieval date
  6. Retrieval quality logging (latency, top-k scores, no-result detection)

This pipeline retrieves from the ICAR/FAO/SAU agronomic knowledge base
(data/knowledge_base/rag_documents/) built by scripts/ingest_rag_knowledge.py.

It does NOT access the old ML training tables or crop_recommendation_model.pkl.
"""

import os
import json
import time
import logging
import math
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
KB_DIR = settings.KNOWLEDGE_BASE_DIR
INDEX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "data", "knowledge_base", "rag_index"
)

# ---------------------------------------------------------------------------
# BM25 fallback (pure-python, no external dependency)
# ---------------------------------------------------------------------------

class SimpleBM25:
    """
    Minimal BM25 implementation that requires only numpy.
    Used when rank-bm25 is not installed.
    Parameters match Okapi BM25 defaults (k1=1.5, b=0.75).
    """
    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.n = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / max(self.n, 1)
        self.df: Dict[str, int] = {}
        self.tf: List[Dict[str, int]] = []
        for doc in corpus:
            freq: Dict[str, int] = {}
            for tok in doc:
                freq[tok] = freq.get(tok, 0) + 1
                self.df[tok] = self.df.get(tok, 0) + (1 if freq[tok] == 1 else 0)
            self.tf.append(freq)
        self.idf: Dict[str, float] = {
            term: math.log((self.n - df_val + 0.5) / (df_val + 0.5) + 1)
            for term, df_val in self.df.items()
        }

    def get_scores(self, query_tokens: List[str]) -> np.ndarray:
        scores = np.zeros(self.n)
        for term in query_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for i, tf_doc in enumerate(self.tf):
                tf_val = tf_doc.get(term, 0)
                if tf_val == 0:
                    continue
                dl = len(self.corpus[i])
                num = tf_val * (self.k1 + 1)
                denom = tf_val + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf_val * num / denom
        return scores


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer for BM25."""
    import re
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


# ---------------------------------------------------------------------------
# RAGPipeline
# ---------------------------------------------------------------------------

class RAGPipeline:
    """
    Hybrid semantic + lexical retrieval over the ICAR/FAO agronomic knowledge base.
    Loaded lazily from the pre-built index in data/knowledge_base/rag_index/.
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.bm25: Optional[SimpleBM25] = None
        self._loaded = False
        self._load()

    def _load(self):
        """Load the pre-built index. If missing, build from knowledge base directory."""
        vec_path = os.path.join(INDEX_DIR, "tfidf_vectorizer.pkl")
        mat_path = os.path.join(INDEX_DIR, "tfidf_matrix.pkl")
        docs_path = os.path.join(INDEX_DIR, "documents.json")

        if os.path.exists(vec_path) and os.path.exists(mat_path) and os.path.exists(docs_path):
            try:
                self.tfidf_vectorizer = joblib.load(vec_path)
                self.tfidf_matrix = joblib.load(mat_path)
                with open(docs_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                # Build BM25 from loaded documents
                corpus_tokens = [_tokenize(d.get("content", "")) for d in self.documents]
                self.bm25 = SimpleBM25(corpus_tokens)
                self._loaded = True
                logger.info(f"RAG pipeline loaded: {len(self.documents)} documents from {INDEX_DIR}")
            except Exception as e:
                logger.error(f"Failed to load RAG index: {e}")
        else:
            logger.warning(
                f"RAG index not found at {INDEX_DIR}. "
                "Run: python scripts/ingest_rag_knowledge.py"
            )

    def is_available(self) -> bool:
        return self._loaded and bool(self.documents)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        crop_filter: Optional[str] = None,
        state_filter: Optional[str] = None,
        season_filter: Optional[str] = None,
        topic_filter: Optional[str] = None,
        hybrid_alpha: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents for the given query.

        Returns a dict with:
          retrieved_documents: list of dicts with content, source metadata, scores
          context_text: pre-formatted context block for LLM prompt
          sources: deduplicated citation list
          retrieval_latency_ms: int
          no_relevant_found: bool
          retrieval_log: dict of diagnostic info
        """
        t0 = time.time()

        top_k = top_k or settings.RAG_TOP_K
        hybrid_alpha = hybrid_alpha if hybrid_alpha is not None else settings.RAG_HYBRID_ALPHA

        if not self.is_available():
            return self._empty_result(query, reason="RAG index not loaded")

        # --- Step 1: Pre-filter by metadata if specified ---
        candidate_indices = list(range(len(self.documents)))
        if crop_filter or state_filter or season_filter or topic_filter:
            candidate_indices = self._metadata_filter(
                candidate_indices, crop_filter, state_filter, season_filter, topic_filter
            )

        if not candidate_indices:
            # No docs match filters; fall back to unfiltered
            logger.info("RAG: metadata filters returned 0 docs; running unfiltered retrieval.")
            candidate_indices = list(range(len(self.documents)))

        # --- Step 2: TF-IDF cosine scores ---
        q_vec = self.tfidf_vectorizer.transform([query])
        all_tfidf = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # --- Step 3: BM25 scores ---
        q_tokens = _tokenize(query)
        all_bm25 = self.bm25.get_scores(q_tokens)

        # Normalize both score arrays to [0, 1] over candidates
        cand_tfidf = np.array([all_tfidf[i] for i in candidate_indices])
        cand_bm25 = np.array([all_bm25[i] for i in candidate_indices])

        cand_tfidf_norm = self._norm(cand_tfidf)
        cand_bm25_norm = self._norm(cand_bm25)

        # --- Step 4: Hybrid score ---
        hybrid_scores = hybrid_alpha * cand_tfidf_norm + (1 - hybrid_alpha) * cand_bm25_norm

        # --- Step 5: Top-K selection ---
        ranked_local = np.argsort(hybrid_scores)[::-1][:top_k]
        selected = [(candidate_indices[li], float(hybrid_scores[li])) for li in ranked_local]

        # --- Step 6: Build result ---
        retrieved_docs = []
        seen_content_hashes = set()
        for idx, score in selected:
            doc = self.documents[idx]
            ch = hash(doc.get("content", "")[:200])
            if ch in seen_content_hashes:
                continue
            seen_content_hashes.add(ch)
            retrieved_docs.append({
                "doc_id": doc.get("doc_id", f"doc_{idx}"),
                "content": doc.get("content", ""),
                "title": doc.get("title", ""),
                "source_institution": doc.get("source_institution", ""),
                "source_url": doc.get("source_url", ""),
                "publication_year": doc.get("publication_year", ""),
                "retrieval_date": doc.get("retrieval_date", ""),
                "region": doc.get("region", ""),
                "state": doc.get("state", ""),
                "crop": doc.get("crop", ""),
                "season": doc.get("season", ""),
                "topic": doc.get("topic", ""),
                "language": doc.get("language", "en"),
                "hybrid_score": round(score, 4),
                "tfidf_score": round(float(all_tfidf[idx]), 4),
                "bm25_score": round(float(all_bm25[idx]), 4),
            })

        latency_ms = int((time.time() - t0) * 1000)
        no_relevant = len(retrieved_docs) == 0 or (retrieved_docs and retrieved_docs[0]["hybrid_score"] < 0.05)

        context_text = self._format_context(retrieved_docs)
        sources = self._deduplicate_sources(retrieved_docs)

        retrieval_log = {
            "query": query,
            "filters": {"crop": crop_filter, "state": state_filter, "season": season_filter, "topic": topic_filter},
            "candidate_pool": len(candidate_indices),
            "retrieved": len(retrieved_docs),
            "top_score": retrieved_docs[0]["hybrid_score"] if retrieved_docs else 0.0,
            "latency_ms": latency_ms,
            "no_relevant_found": no_relevant,
            "hybrid_alpha": hybrid_alpha,
        }
        logger.info(f"RAG retrieval: {retrieval_log}")

        return {
            "retrieved_documents": retrieved_docs,
            "context_text": context_text,
            "sources": sources,
            "retrieval_latency_ms": latency_ms,
            "no_relevant_found": no_relevant,
            "retrieval_log": retrieval_log,
        }

    def _metadata_filter(
        self,
        indices: List[int],
        crop_filter: Optional[str],
        state_filter: Optional[str],
        season_filter: Optional[str],
        topic_filter: Optional[str],
    ) -> List[int]:
        """Filter document indices by metadata fields. Case-insensitive partial match."""
        result = []
        for i in indices:
            doc = self.documents[i]
            if crop_filter:
                doc_crop = (doc.get("crop") or "").lower()
                if crop_filter.lower() not in doc_crop and doc_crop not in ("", "all"):
                    continue
            if state_filter:
                doc_state = (doc.get("state") or doc.get("region") or "").lower()
                if doc_state and state_filter.lower() not in doc_state:
                    continue
            if season_filter:
                doc_season = (doc.get("season") or "").lower()
                if doc_season and season_filter.lower() not in doc_season:
                    continue
            if topic_filter:
                doc_topic = (doc.get("topic") or "").lower()
                if doc_topic and topic_filter.lower() not in doc_topic:
                    continue
            result.append(i)
        return result

    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        if not docs:
            return "No relevant agricultural documents found for this query."
        blocks = []
        for doc in docs:
            institution = doc.get("source_institution") or "Unknown source"
            pub_year = doc.get("publication_year") or ""
            region = doc.get("region") or doc.get("state") or ""
            crop = doc.get("crop") or ""
            season = doc.get("season") or ""
            url = doc.get("source_url") or ""

            meta_parts = [institution]
            if pub_year:
                meta_parts.append(str(pub_year))
            if region:
                meta_parts.append(region)
            if crop:
                meta_parts.append(crop)
            if season:
                meta_parts.append(season)
            meta_str = " | ".join(meta_parts)
            if url:
                meta_str += f" | URL: {url}"

            title = doc.get("title") or ""
            block = f"[SOURCE: {meta_str}]\n"
            if title:
                block += f"Title: {title}\n"
            block += doc.get("content", "")
            blocks.append(block)
        return "\n\n---\n\n".join(blocks)

    def _deduplicate_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        sources = []
        for doc in docs:
            key = (doc.get("source_institution") or "", doc.get("title") or "")
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "name": doc.get("source_institution") or "Agricultural Knowledge Base",
                "title": doc.get("title") or "",
                "publication_year": doc.get("publication_year") or "",
                "url": doc.get("source_url") or "",
                "region": doc.get("region") or doc.get("state") or "",
                "crop": doc.get("crop") or "",
                "retrieval_date": doc.get("retrieval_date") or "",
                "score": doc.get("hybrid_score", 0.0),
                "used": True,
            })
        return sources

    @staticmethod
    def _norm(arr: np.ndarray) -> np.ndarray:
        mn, mx = arr.min(), arr.max()
        if mx - mn < 1e-9:
            return np.zeros_like(arr)
        return (arr - mn) / (mx - mn)

    def _empty_result(self, query: str, reason: str = "") -> Dict[str, Any]:
        return {
            "retrieved_documents": [],
            "context_text": f"No agricultural knowledge base available. {reason}",
            "sources": [],
            "retrieval_latency_ms": 0,
            "no_relevant_found": True,
            "retrieval_log": {"query": query, "reason": reason},
        }


# Singleton instance for the new RAG+LLM pipeline
rag_pipeline = RAGPipeline()
