"""
Advanced Retriever — Hybrid Search, re-ranking, and broader coverage for list-style questions.
"""

import logging
import re
from collections import defaultdict

from langchain_community.retrievers import BM25Retriever

logger = logging.getLogger(__name__)

EXHAUSTIVE_PATTERNS = (
    r"\ball\b",
    r"\bevery\b",
    r"\blist\b",
    r"\benumerate\b",
    r"\bcomplete\b",
    r"\bfull\b",
    r"\bwhich\b.*\b(?:all|every)\b",
    r"\bwhat\b.*\b(?:all|every)\b",
)

STOPWORDS = {
    "about", "after", "again", "also", "among", "and", "any", "are", "been",
    "but", "can", "could", "does", "each", "from", "have", "into", "more",
    "show", "tell", "than", "that", "them", "then", "they", "this", "those",
    "what", "when", "where", "which", "with", "would", "your",
}


class AdvancedRetriever:
    """
    Implements a multi-stage retrieval pipeline:
    1. Vector search and/or BM25 keyword search
    2. Reciprocal rank fusion
    3. Optional keyword expansion for exhaustive/list queries
    4. Cross-encoder re-ranking
    """

    def __init__(self, vectorstore_manager, llm=None, all_documents=None):
        self.vs_manager = vectorstore_manager
        self.llm = llm
        self.all_documents = all_documents or []
        self.cross_encoder = None

        try:
            from sentence_transformers import CrossEncoder

            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Cross-encoder re-ranker loaded")
        except Exception as e:
            logger.warning(f"Cross-encoder not available: {e}")

    @staticmethod
    def _doc_key(doc):
        metadata = doc.metadata or {}
        return (
            metadata.get("source"),
            metadata.get("page"),
            metadata.get("chunk_index"),
            metadata.get("content_type"),
            doc.page_content[:120],
        )

    @staticmethod
    def _wants_exhaustive_coverage(query):
        normalized = query.lower().strip()
        return any(re.search(pattern, normalized) for pattern in EXHAUSTIVE_PATTERNS)

    @staticmethod
    def _extract_query_terms(query):
        terms = []
        for token in re.findall(r"[a-zA-Z0-9]+", query.lower()):
            if len(token) <= 2 or token in STOPWORDS:
                continue
            terms.append(token)
        return terms

    def _filter_documents(self, content_type_filter=None, source_file_filter=None):
        filtered_docs = self.all_documents

        if content_type_filter:
            filtered_docs = [
                doc for doc in filtered_docs
                if doc.metadata.get("content_type") == content_type_filter
            ]

        if source_file_filter:
            filtered_docs = [
                doc for doc in filtered_docs
                if doc.metadata.get("source") in source_file_filter
            ]

        return filtered_docs

    def _vector_search(self, query, content_type_filter=None, k=10,
                       source_file_filter=None, mmr_lambda=None):
        retriever = self.vs_manager.get_retriever(
            content_type_filter=content_type_filter,
            search_type="mmr",
            k=k,
            source_file_filter=source_file_filter,
            lambda_mult=mmr_lambda,
        )
        return retriever.invoke(query)

    @staticmethod
    def _bm25_search(query, documents, k=10):
        if not documents:
            return []

        bm25 = BM25Retriever.from_documents(documents)
        bm25.k = k
        return bm25.invoke(query)

    def _reciprocal_rank_fusion(self, ranked_results, limit):
        """
        Merge multiple ranked result lists without requiring EnsembleRetriever support.
        """
        scores = defaultdict(float)
        doc_map = {}

        for docs, weight in ranked_results:
            for rank, doc in enumerate(docs, start=1):
                key = self._doc_key(doc)
                doc_map[key] = doc
                scores[key] += weight / (60 + rank)

        fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [doc_map[key] for key, _score in fused[:limit]]

    def _keyword_score(self, doc, query_terms):
        if not query_terms:
            return 0

        content = doc.page_content.lower()
        unique_matches = {term for term in query_terms if term in content}
        if not unique_matches:
            return 0

        score = len(unique_matches)
        if len(query_terms) >= 2 and all(term in content for term in query_terms[:2]):
            score += 2
        if "problem statement" in content:
            score += 3
        if re.search(r"\b\d+\s+\|", content):
            score += 1
        return score

    def _augment_with_keyword_matches(self, candidates, filtered_docs, query_terms, limit):
        seen = {self._doc_key(doc) for doc in candidates}
        scored = []

        for doc in filtered_docs:
            score = self._keyword_score(doc, query_terms)
            if score <= 0:
                continue
            scored.append((score, doc))

        scored.sort(
            key=lambda item: (
                item[0],
                item[1].metadata.get("page", 0),
                -item[1].metadata.get("chunk_index", 0),
            ),
            reverse=True,
        )

        augmented = list(candidates)
        for _score, doc in scored:
            key = self._doc_key(doc)
            if key in seen:
                continue
            augmented.append(doc)
            seen.add(key)
            if len(augmented) >= limit:
                break

        return augmented

    def _limit_docs_per_page(self, docs, limit, max_docs_per_page=2):
        """
        Exhaustive list-type queries benefit from broader page coverage instead of repeated chunks.
        """
        selected = []
        page_counts = defaultdict(int)
        seen = set()

        for doc in docs:
            key = self._doc_key(doc)
            if key in seen:
                continue

            page_key = (doc.metadata.get("source"), doc.metadata.get("page"))
            if page_counts[page_key] >= max_docs_per_page:
                continue

            selected.append(doc)
            page_counts[page_key] += 1
            seen.add(key)

            if len(selected) >= limit:
                return selected

        for doc in docs:
            key = self._doc_key(doc)
            if key in seen:
                continue
            selected.append(doc)
            seen.add(key)
            if len(selected) >= limit:
                break

        return selected

    def rerank(self, query, documents, top_n):
        """Re-rank documents using a Cross-Encoder model when available."""
        if not documents:
            return []

        if not self.cross_encoder:
            return documents[:top_n]

        try:
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self.cross_encoder.predict(pairs)
            scored_docs = list(zip(documents, scores))
            scored_docs.sort(key=lambda item: item[1], reverse=True)
            return [doc for doc, _score in scored_docs[:top_n]]
        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}")
            return documents[:top_n]

    def retrieve(self, query, content_type_filter=None, top_k=5,
                 source_file_filter=None, retrieval_mode="Hybrid (Vector + BM25)",
                 mmr_lambda=None):
        """
        Full retrieval pipeline:
        1. Vector search and/or BM25 keyword search
        2. Deduplicate and expand when the question asks for exhaustive coverage
        3. Cross-Encoder re-rank
        """
        filtered_docs = self._filter_documents(content_type_filter, source_file_filter)
        exhaustive = self._wants_exhaustive_coverage(query)
        target_top_k = top_k

        if exhaustive:
            target_top_k = max(top_k, 10)

        candidate_k = max(target_top_k * 3, 18 if exhaustive else top_k * 3)
        candidates = []

        try:
            vector_results = []
            bm25_results = []

            if retrieval_mode != "BM25 Only":
                vector_results = self._vector_search(
                    query=query,
                    content_type_filter=content_type_filter,
                    k=candidate_k,
                    source_file_filter=source_file_filter,
                    mmr_lambda=mmr_lambda,
                )

            if retrieval_mode != "Vector Only (MMR)":
                bm25_results = self._bm25_search(query, filtered_docs, k=candidate_k)

            if retrieval_mode == "Vector Only (MMR)":
                candidates = vector_results
            elif retrieval_mode == "BM25 Only":
                candidates = bm25_results
            else:
                candidates = self._reciprocal_rank_fusion(
                    [
                        (vector_results, 0.7),
                        (bm25_results, 0.3),
                    ],
                    limit=candidate_k * 2,
                )
        except Exception as e:
            logger.warning(f"Hybrid retrieval failed, falling back to vector search: {e}")
            candidates = self.vs_manager.similarity_search(
                query,
                content_type=content_type_filter,
                k=target_top_k,
                source_file_filter=source_file_filter,
            )

        deduped = []
        seen = set()
        for doc in candidates:
            key = self._doc_key(doc)
            if key in seen:
                continue
            deduped.append(doc)
            seen.add(key)

        if exhaustive and filtered_docs:
            query_terms = self._extract_query_terms(query)
            deduped = self._augment_with_keyword_matches(
                deduped,
                filtered_docs,
                query_terms,
                limit=max(candidate_k * 2, target_top_k * 2),
            )

        rerank_limit = max(target_top_k, min(len(deduped), target_top_k * 2))
        reranked = self.rerank(query, deduped, top_n=rerank_limit)

        if exhaustive:
            final_docs = self._limit_docs_per_page(
                reranked,
                limit=target_top_k,
                max_docs_per_page=2,
            )
        else:
            final_docs = reranked[:target_top_k]

        logger.info(
            "Retrieved %s documents (mode=%s, exhaustive=%s, candidates=%s)",
            len(final_docs),
            retrieval_mode,
            exhaustive,
            len(deduped),
        )
        return final_docs
