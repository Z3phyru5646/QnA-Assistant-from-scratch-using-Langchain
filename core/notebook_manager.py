"""
Notebook Manager — CRUD operations for notebook isolation (like NotebookLM).
Each notebook has its own ChromaDB collection and PDF list.
"""

import json
import uuid
import shutil
import logging
from pathlib import Path
from datetime import datetime
from config.settings import NOTEBOOKS_DIR, DATA_DIR, VECTORSTORE_DIR, DEFAULT_NOTEBOOK_NAME

logger = logging.getLogger(__name__)


class NotebookManager:
    """Manages notebook lifecycle: create, delete, list, and PDF tracking."""

    def __init__(self):
        NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_notebook_path(self, notebook_id: str) -> Path:
        return NOTEBOOKS_DIR / f"{notebook_id}.json"

    def _get_notebook_pdf_dir(self, notebook_id: str) -> Path:
        return DATA_DIR / "uploaded_pdfs" / notebook_id

    def create_notebook(self, name: str = None) -> dict:
        """Create a new notebook with a unique ID and empty PDF list."""
        notebook_id = uuid.uuid4().hex[:12]
        name = name or DEFAULT_NOTEBOOK_NAME

        notebook = {
            "id": notebook_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "collection_name": f"rag_nb_{notebook_id}",
            "pdf_files": [],
            "stats": {
                "total_chunks": 0,
                "text_chunks": 0,
                "image_chunks": 0,
                "table_chunks": 0,
            },
        }

        # Save metadata
        with open(self._get_notebook_path(notebook_id), "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)

        # Create notebook's PDF directory
        self._get_notebook_pdf_dir(notebook_id).mkdir(parents=True, exist_ok=True)

        logger.info(f"Created notebook '{name}' (ID: {notebook_id})")
        return notebook

    def get_notebook(self, notebook_id: str) -> dict | None:
        """Load notebook metadata from disk."""
        path = self._get_notebook_path(notebook_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load notebook {notebook_id}: {e}")
            return None

    def save_notebook(self, notebook: dict):
        """Persist notebook metadata to disk."""
        notebook_id = notebook["id"]
        with open(self._get_notebook_path(notebook_id), "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)

    def list_notebooks(self) -> list[dict]:
        """List all notebooks sorted by creation date (newest first)."""
        notebooks = []
        for path in NOTEBOOKS_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    notebooks.append(json.load(f))
            except Exception as e:
                logger.warning(f"Skipping corrupt notebook file {path}: {e}")
        notebooks.sort(key=lambda nb: nb.get("created_at", ""), reverse=True)
        return notebooks

    def delete_notebook(self, notebook_id: str):
        """Delete notebook: remove JSON, PDFs, and ChromaDB collection."""
        # Remove JSON metadata
        json_path = self._get_notebook_path(notebook_id)
        if json_path.exists():
            json_path.unlink()

        # Remove uploaded PDFs for this notebook
        pdf_dir = self._get_notebook_pdf_dir(notebook_id)
        if pdf_dir.exists():
            shutil.rmtree(pdf_dir, ignore_errors=True)

        logger.info(f"Deleted notebook {notebook_id}")

    def add_pdf_to_notebook(self, notebook_id: str, filename: str, chunk_stats: dict):
        """Register a processed PDF in the notebook's metadata."""
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return

        # Avoid duplicates
        existing_names = [p["filename"] for p in notebook["pdf_files"]]
        if filename in existing_names:
            return

        notebook["pdf_files"].append({
            "filename": filename,
            "added_at": datetime.now().isoformat(),
            "text_chunks": chunk_stats.get("text_chunks", 0),
            "image_chunks": chunk_stats.get("image_chunks", 0),
            "table_chunks": chunk_stats.get("table_chunks", 0),
        })

        # Update aggregate stats
        notebook["stats"]["total_chunks"] += chunk_stats.get("total_chunks", 0)
        notebook["stats"]["text_chunks"] += chunk_stats.get("text_chunks", 0)
        notebook["stats"]["image_chunks"] += chunk_stats.get("image_chunks", 0)
        notebook["stats"]["table_chunks"] += chunk_stats.get("table_chunks", 0)

        self.save_notebook(notebook)
        logger.info(f"Added '{filename}' to notebook {notebook_id}")

    def remove_pdf_from_notebook(self, notebook_id: str, filename: str):
        """Unregister a PDF from the notebook and delete the file."""
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return

        # Find and remove the PDF entry
        pdf_entry = None
        for p in notebook["pdf_files"]:
            if p["filename"] == filename:
                pdf_entry = p
                break

        if pdf_entry:
            notebook["pdf_files"].remove(pdf_entry)

            # Update stats
            notebook["stats"]["total_chunks"] -= (
                pdf_entry.get("text_chunks", 0) +
                pdf_entry.get("image_chunks", 0) +
                pdf_entry.get("table_chunks", 0)
            )
            notebook["stats"]["text_chunks"] -= pdf_entry.get("text_chunks", 0)
            notebook["stats"]["image_chunks"] -= pdf_entry.get("image_chunks", 0)
            notebook["stats"]["table_chunks"] -= pdf_entry.get("table_chunks", 0)

            # Ensure stats don't go negative
            for k in notebook["stats"]:
                notebook["stats"][k] = max(0, notebook["stats"][k])

            self.save_notebook(notebook)

        # Delete the actual PDF file
        pdf_path = self._get_notebook_pdf_dir(notebook_id) / filename
        if pdf_path.exists():
            pdf_path.unlink()

        logger.info(f"Removed '{filename}' from notebook {notebook_id}")

    def get_notebook_pdf_names(self, notebook_id: str) -> list[str]:
        """Get list of PDF filenames in a notebook."""
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return []
        return [p["filename"] for p in notebook.get("pdf_files", [])]
