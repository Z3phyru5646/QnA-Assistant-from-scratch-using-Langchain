"""
Text Pipeline — Two-stage chunking: Recursive + Semantic
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config.settings import CONTENT_TYPE_TEXT
import logging

logger = logging.getLogger(__name__)


class TextPipeline:
    """Processes raw text blocks into chunked LangChain Documents."""

    def __init__(self, embeddings=None):
        self.embeddings = embeddings

    def process(self, text_blocks, source_file="unknown", chunk_size=500, chunk_overlap=200):
        """
        Take raw text blocks from PDFProcessor and return LangChain Documents.

        Args:
            text_blocks: list of dicts with {text, page, source}
            source_file: original filename
            chunk_size: characters per chunk
            chunk_overlap: overlap between chunks

        Returns:
            list of LangChain Document objects with metadata
        """
        if not text_blocks:
            return []

        all_documents = []

        # Stage 1: RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
            length_function=len,
        )

        for block in text_blocks:
            raw_text = block["text"]
            page_num = block["page"]

            chunks = splitter.split_text(raw_text)

            for idx, chunk in enumerate(chunks):
                if chunk.strip():
                    doc = Document(
                        page_content=chunk.strip(),
                        metadata={
                            "source": source_file,
                            "page": page_num,
                            "content_type": CONTENT_TYPE_TEXT,
                            "chunk_index": idx,
                            "extraction_method": "pymupdf",
                        }
                    )
                    all_documents.append(doc)

        # Stage 2: Semantic chunking (optional — uses embedding similarity)
        # Only apply if embeddings are available and we have enough chunks
        if self.embeddings and len(all_documents) > 2:
            try:
                all_documents = self._semantic_merge(all_documents)
            except Exception as e:
                logger.warning(f"Semantic chunking failed, using recursive chunks: {e}")

        logger.info(f"Text pipeline produced {len(all_documents)} chunks from {len(text_blocks)} text blocks")
        return all_documents

    def _semantic_merge(self, documents, similarity_threshold=0.85):
        """
        Merge adjacent chunks that are semantically very similar.
        This helps avoid splitting mid-concept.
        """
        if len(documents) < 2:
            return documents

        try:
            texts = [doc.page_content for doc in documents]
            embeddings = self.embeddings.embed_documents(texts)

            merged = [documents[0]]
            for i in range(1, len(documents)):
                # Compute cosine similarity between adjacent chunks
                sim = self._cosine_similarity(embeddings[i - 1], embeddings[i])

                # If very similar AND from the same page, merge
                if (sim > similarity_threshold and
                    documents[i].metadata.get("page") == merged[-1].metadata.get("page")):
                    # Merge content
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
