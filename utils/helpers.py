"""
Utility functions — File handling, logging setup, etc.
"""

import os
import logging
from pathlib import Path
from config.settings import DATA_DIR


def setup_logging(level=logging.INFO):
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def ensure_data_directories():
    """Create all required data directories."""
    dirs = [
        DATA_DIR / "uploaded_pdfs",
        DATA_DIR / "extracted_images",
        DATA_DIR / "extracted_tables",
        DATA_DIR / "processed_texts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_file_size_mb(file_path):
    """Get file size in megabytes."""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        return 0


def clean_text(text):
    """Clean and normalize text content."""
    if not text:
        return ""
    # Remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
