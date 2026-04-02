"""
VectorStore Manager — ChromaDB operations with metadata filtering.
"""

import chromadb
from langchain_community.vectorstores import Chroma
from config.settings import CHROMA_COLLECTION_NAME, VECTORSTORE_DIR
import logging

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages ChromaDB persistent vector store with content-type filtering."""

    def __init__(self, embedding_model, persist_dir=None):
        self.persist_dir = str(persist_dir or VECTORSTORE_DIR)
        self.embedding_model = embedding_model

        # Ensure directory exists
        import os
        os.makedirs(self.persist_dir, exist_ok=True)

        self.vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_model,
            persist_directory=self.persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB initialized at {self.persist_dir}")

    def add_documents(self, documents):
        """Add LangChain Document objects with metadata to the vector store."""
        if documents:
            self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to ChromaDB")

    def get_retriever(self, content_type_filter=None, search_type="mmr", k=5):
        """
        Get a LangChain retriever with optional content_type filter.

        Args:
            content_type_filter: "text", "image", "table", or None (all)
            search_type: "mmr" or "similarity"
            k: number of results to return
        """
        search_kwargs = {"k": k}

        if search_type == "mmr":
            search_kwargs["lambda_mult"] = 0.3
            search_kwargs["fetch_k"] = 20

        if content_type_filter:
            search_kwargs["filter"] = {"content_type": content_type_filter}

        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def similarity_search(self, query, content_type=None, k=5):
        """Direct similarity search with optional content_type filter."""
        filter_dict = {"content_type": content_type} if content_type else None
        return self.vectorstore.similarity_search(query, k=k, filter=filter_dict)

    def get_collection_stats(self):
        """Return count of documents in the collection."""
        try:
            collection = self.vectorstore._collection
            total = collection.count()
            return {"total_chunks": total}
        except Exception as e:
            logger.warning(f"Could not get collection stats: {e}")
            return {"total_chunks": 0}

    def delete_collection(self):
        """Delete all data from the vector store."""
        try:
            self.vectorstore.delete_collection()
            logger.info("ChromaDB collection deleted")
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")
