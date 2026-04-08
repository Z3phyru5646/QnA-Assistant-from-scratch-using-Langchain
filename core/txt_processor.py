"""
TXT Processor — Simple text file reader.
Returns text_blocks only (no images/tables).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TxtProcessor:
    """Reads .txt files and returns text blocks."""

    def process(self, txt_path: Path):
        """
        Process a TXT file.
        Returns: (text_blocks, image_paths, table_data)
        """
        txt_path = Path(txt_path)
        source_name = txt_path.name
        logger.info(f"Processing TXT: {source_name}")

        text_blocks = []
        image_paths = []
        table_data = []

        try:
            # Try UTF-8 first, fallback to latin-1
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(txt_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if not content:
                logger.error(f"Could not decode {source_name}")
                return text_blocks, image_paths, table_data

            # Split by paragraphs (double newline)
            paragraphs = content.split('\n\n')
            page_num = 1
            current_text = []

            for para in paragraphs:
                if para.strip():
                    current_text.append(para.strip())

                combined = '\n\n'.join(current_text)
                if len(combined) > 3000:
                    text_blocks.append({
                        "text": combined,
                        "page": page_num,
                        "source": source_name,
                    })
                    current_text = []
                    page_num += 1

            if current_text:
                text_blocks.append({
                    "text": '\n\n'.join(current_text),
                    "page": page_num,
                    "source": source_name,
                })

        except Exception as e:
            logger.error(f"TXT processing failed: {e}")

        logger.info(f"TXT extraction — Text: {len(text_blocks)} blocks")
        return text_blocks, image_paths, table_data
