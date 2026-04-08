"""
Text Pipeline — Recursive chunking with optional semantic merge and adaptive mode.
"""

import logging
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import CONTENT_TYPE_TEXT

logger = logging.getLogger(__name__)


class TextPipeline:
    """Processes raw text blocks into chunked LangChain Documents."""

    def __init__(self, embeddings=None):
        self.embeddings = embeddings

    def process(self, text_blocks, source_file="unknown", chunk_size=500,
                chunk_overlap=200, adaptive=False):
        """
        Take raw text blocks from processors and return LangChain Documents.
        """
        if not text_blocks:
            return []

        if adaptive:
            chunk_size, chunk_overlap = self._calculate_adaptive_params(text_blocks)
            logger.info(f"Adaptive chunking: size={chunk_size}, overlap={chunk_overlap}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n\n", "\n\n", "\n\n• ", "\n\n- ", ".\n", "\n", ". ", " "],
            length_function=len,
        )

        all_documents = []
        for block in text_blocks:
            raw_text = self._normalize_text(block["text"])
            page_num = block["page"]

            chunks = splitter.split_text(raw_text)
            for idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                all_documents.append(
                    Document(
                        page_content=chunk.strip(),
                        metadata={
                            "source": source_file,
                            "page": page_num,
                            "content_type": CONTENT_TYPE_TEXT,
                            "chunk_index": idx,
                            "extraction_method": "pymupdf",
                        },
                    )
                )

        # Keep semantic merge only for smaller non-adaptive batches.
        if (not adaptive and self.embeddings and 2 < len(all_documents) <= 30):
            try:
                all_documents = self._semantic_merge(all_documents)
            except Exception as e:
                logger.warning(f"Semantic chunking failed, using recursive chunks: {e}")

        logger.info(
            "Text pipeline produced %s chunks from %s text blocks",
            len(all_documents),
            len(text_blocks),
        )
        return all_documents

    def _calculate_adaptive_params(self, text_blocks):
        """Auto-calculate chunk size based on document characteristics."""
        total_text = "".join(block["text"] for block in text_blocks)
        total_words = len(total_text.split())
        num_pages = len(text_blocks)
        lines = [line.strip() for line in total_text.splitlines() if line.strip()]

        words_per_page = total_words / max(num_pages, 1)

        header_pattern = r"^(?:#{1,6}\s|[A-Z][A-Z\s]{5,}$|\d+\.\s+[A-Z])"
        header_lines = sum(1 for line in lines if re.search(header_pattern, line))
        bullet_lines = sum(1 for line in lines if re.match(r"^(?:[-•*]|\d+[.)])\s+", line))
        has_structure = header_lines >= max(2, num_pages // 2) or bullet_lines >= max(4, num_pages)

        if has_structure:
            return 2500, 800
        if words_per_page > 500:
            return 3000, 1000
        if words_per_page < 100:
            return 1500, 400
        return 2000, 600

    @staticmethod
    def _normalize_text(text):
        """Remove invisible PDF artifacts and normalize whitespace before chunking."""
        cleaned = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text or "")
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        return cleaned.strip()

    def _semantic_merge(self, documents, similarity_threshold=0.85):
        """Merge adjacent chunks that are semantically very similar."""
        if len(documents) < 2:
            return documents

        try:
            texts = [doc.page_content for doc in documents]
            embeddings = self.embeddings.embed_documents(texts)

            merged = [documents[0]]
            for i in range(1, len(documents)):
                sim = self._cosine_similarity(embeddings[i - 1], embeddings[i])

                if (
                    sim > similarity_threshold
                    and documents[i].metadata.get("page") == merged[-1].metadata.get("page")
                ):
                    merged[-1].page_content += "\n" + documents[i].page_content
                else:
                    merged.append(documents[i])

            return merged
        except Exception as e:
            logger.warning(f"Semantic merge error: {e}")
            return documents

    @staticmethod
    def _cosine_similarity(vec_a, vec_b):
        """Compute cosine similarity between two vectors."""
        import numpy as np

        a = np.array(vec_a)
        b = np.array(vec_b)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
