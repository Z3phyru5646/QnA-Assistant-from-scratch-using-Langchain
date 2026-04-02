"""
Embedding Manager — HuggingFace sentence-transformers wrapper.
"""

from langchain_community.embeddings import SentenceTransformerEmbeddings
from config.settings import EMBEDDING_MODEL_NAME
import logging

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages the embedding model for vectorization."""

    def __init__(self, model_name=None):
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformerEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully")

    def get_embeddings(self):
        """Return the LangChain-compatible embedding function."""
        return self.model
