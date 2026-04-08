"""
VectorStore Manager — ChromaDB operations with metadata filtering and notebook isolation.
"""

import chromadb
from langchain_community.vectorstores import Chroma
from config.settings import CHROMA_COLLECTION_NAME, VECTORSTORE_DIR
import logging

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages ChromaDB persistent vector store with content-type filtering and notebook isolation."""

    def __init__(self, embedding_model, persist_dir=None, collection_name=None):
        self.persist_dir = str(persist_dir or VECTORSTORE_DIR)
        self.embedding_model = embedding_model
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME

        # Ensure directory exists
        import os
        os.makedirs(self.persist_dir, exist_ok=True)

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=embedding_model,
            persist_directory=self.persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB initialized at {self.persist_dir} (collection: {self.collection_name})")

    def reload_collection(self, collection_name):
        """Reload with a different collection (for notebook switching)."""
        self.collection_name = collection_name
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Reloaded ChromaDB collection: {collection_name}")

    def add_documents(self, documents):
        """Add LangChain Document objects with metadata to the vector store."""
        if documents:
            self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to ChromaDB")

    @staticmethod
    def _build_where_clause(content_type_filter=None, source_file_filter=None):
        """Build a Chroma-compatible metadata filter clause."""
        clauses = []

        if content_type_filter:
            clauses.append({"content_type": content_type_filter})

        if source_file_filter:
            if len(source_file_filter) == 1:
                clauses.append({"source": source_file_filter[0]})
            else:
                clauses.append({"source": {"$in": source_file_filter}})

        if not clauses:
            return None

        if len(clauses) == 1:
            return clauses[0]

        return {"$and": clauses}

    def get_retriever(self, content_type_filter=None, search_type="mmr", k=5,
                      source_file_filter=None, lambda_mult=None):
        """
        Get a LangChain retriever with optional content_type filter and source_file_filter.
        """
        search_kwargs = {"k": k}

        if search_type == "mmr":
            from config.settings import MMR_DIVERSITY_SCORE
            search_kwargs["lambda_mult"] = (
                MMR_DIVERSITY_SCORE if lambda_mult is None else lambda_mult
            )
            search_kwargs["fetch_k"] = max(20, k * 4)

        filter_dict = self._build_where_clause(content_type_filter, source_file_filter)
        if filter_dict:
            search_kwargs["filter"] = filter_dict

        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def similarity_search(self, query, content_type=None, k=5, source_file_filter=None):
        """Direct similarity search with optional content_type and source filters."""
        filter_dict = self._build_where_clause(content_type, source_file_filter)
        return self.vectorstore.similarity_search(query, k=k, filter=filter_dict)

    def get_documents_by_type(self, content_type: str, limit: int = 50, source_file_filter: list = None) -> list:
        """Retrieve all documents of a specific content type for summarization."""
        try:
            collection = self.vectorstore._collection
            where_clause = self._build_where_clause(content_type, source_file_filter)

            results = collection.get(
                where=where_clause,
                limit=limit,
                include=["documents", "metadatas"],
            )

            if not results or not results.get("documents"):
                return []

            from langchain_core.documents import Document
            docs = []
            for i, content in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                docs.append(Document(page_content=content, metadata=metadata))
            return docs

        except Exception as e:
            logger.warning(f"Could not get documents by type '{content_type}': {e}")
            return []

    def get_all_documents(self, content_type_filter=None, source_file_filter=None, limit=None) -> list:
        """Load persisted documents from the active collection."""
        try:
            collection = self.vectorstore._collection
            kwargs = {
                "include": ["documents", "metadatas"],
            }

            where_clause = self._build_where_clause(content_type_filter, source_file_filter)
            if where_clause:
                kwargs["where"] = where_clause

            if limit is not None:
                kwargs["limit"] = limit

            results = collection.get(**kwargs)
            if not results or not results.get("documents"):
                return []

            from langchain_core.documents import Document

            docs = []
            for i, content in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                docs.append(Document(page_content=content, metadata=metadata))

            return docs
        except Exception as e:
            logger.warning(f"Could not load all documents from collection '{self.collection_name}': {e}")
            return []

    def delete_documents_by_source(self, source_filename: str):
        """Delete all chunks from a specific source PDF."""
        try:
            collection = self.vectorstore._collection
            collection.delete(where={"source": source_filename})
            logger.info(f"Deleted all chunks from source: {source_filename}")
        except Exception as e:
            logger.warning(f"Could not delete documents for source '{source_filename}': {e}")

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
