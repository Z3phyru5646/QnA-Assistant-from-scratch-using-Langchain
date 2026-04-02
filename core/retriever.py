"""
Advanced Retriever — Hybrid Search, Re-ranking, MMR, Multi-Query.
"""

# Since langchain version is weird and EnsembleRetriever might be missing
try:
    from langchain.retrievers import EnsembleRetriever
except ImportError:
    try:
        from langchain.retrievers.ensemble import EnsembleRetriever
    except ImportError:
        EnsembleRetriever = None

from langchain_community.retrievers import BM25Retriever
from config.settings import BM25_WEIGHT, VECTOR_WEIGHT, RERANK_TOP_N
import logging

logger = logging.getLogger(__name__)


class AdvancedRetriever:
    """
    Implements a multi-stage retrieval pipeline:
    1. Hybrid Search (Vector MMR + BM25 keyword)
    2. Cross-Encoder Re-ranking
    """

    def __init__(self, vectorstore_manager, llm=None, all_documents=None):
        self.vs_manager = vectorstore_manager
        self.llm = llm
        self.all_documents = all_documents or []
        self.cross_encoder = None

        # Lazy-load cross-encoder
        try:
            from sentence_transformers import CrossEncoder
            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Cross-encoder re-ranker loaded")
        except Exception as e:
            logger.warning(f"Cross-encoder not available: {e}")

    def get_hybrid_retriever(self, content_type_filter=None, k=10):
        """
        Create an ensemble retriever combining vector (MMR) + BM25.
        """
        # Vector retriever with MMR
        vector_retriever = self.vs_manager.get_retriever(
            content_type_filter=content_type_filter,
            search_type="mmr",
            k=k,
        )

        # BM25 retriever (keyword-based)
        filtered_docs = self.all_documents
        if content_type_filter:
            filtered_docs = [
                d for d in self.all_documents
                if d.metadata.get("content_type") == content_type_filter
            ]

        if not filtered_docs:
            return vector_retriever

        try:
            bm25_retriever = BM25Retriever.from_documents(filtered_docs, k=k)

            ensemble = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[VECTOR_WEIGHT, BM25_WEIGHT],
            )
            return ensemble
        except Exception as e:
            logger.warning(f"BM25 retriever failed, using vector-only: {e}")
            return vector_retriever

    def rerank(self, query, documents, top_n=None):
        """Re-rank documents using Cross-Encoder model."""
        top_n = top_n or RERANK_TOP_N

        if not documents:
            return []

        if not self.cross_encoder:
            return documents[:top_n]

        try:
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self.cross_encoder.predict(pairs)
            scored_docs = list(zip(documents, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, score in scored_docs[:top_n]]
        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}")
            return documents[:top_n]

    def retrieve(self, query, content_type_filter=None, top_k=5):
        """
        Full retrieval pipeline:
        1. Hybrid Search (Vector MMR + BM25)
        2. Deduplicate
        3. Cross-Encoder Re-rank
        """
        try:
            retriever = self.get_hybrid_retriever(
                content_type_filter=content_type_filter,
                k=top_k * 3,  # Fetch more candidates for re-ranking
            )
            candidates = retriever.invoke(query)
        except Exception as e:
            logger.warning(f"Hybrid retrieval failed, falling back to vector search: {e}")
            candidates = self.vs_manager.similarity_search(
                query, content_type=content_type_filter, k=top_k
            )

        # Deduplicate by content
        seen = set()
        unique_docs = []
        for doc in candidates:
            content_hash = hash(doc.page_content[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(doc)

        # Re-rank
        final_docs = self.rerank(query, unique_docs, top_n=top_k)
        logger.info(f"Retrieved {len(final_docs)} documents (from {len(candidates)} candidates)")
        return final_docs
