"""
PDF Processor — Multimodal PDF Splitter
Extracts text, images, and tables from PDF files into separate pipelines.
"""

import os
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from pathlib import Path
from config.settings import DATA_DIR
import logging
import io
import pandas as pd

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Splits a PDF into three streams: text blocks, images, and tables."""

    def __init__(self):
        self.images_dir = DATA_DIR / "extracted_images"
        self.tables_dir = DATA_DIR / "extracted_tables"
        self.texts_dir = DATA_DIR / "processed_texts"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create output directories if they don't exist."""
        for d in [self.images_dir, self.tables_dir, self.texts_dir,
                  DATA_DIR / "uploaded_pdfs"]:
            d.mkdir(parents=True, exist_ok=True)

    def process(self, pdf_path: Path):
        """
        Process a PDF file and return:
            text_blocks: list of dicts with {text, page, source}
            image_paths: list of dicts with {path, page, source}
            table_data:  list of dicts with {dataframe, page, source, markdown}
        """
        pdf_path = Path(pdf_path)
        source_name = pdf_path.name
        logger.info(f"Processing PDF: {source_name}")

        text_blocks = []
        image_paths = []
        table_data = []

        # --- Extract text and images with PyMuPDF ---
        try:
            doc = fitz.open(str(pdf_path))
            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text
                page_text = page.get_text("text")
                if page_text and page_text.strip():
                    text_blocks.append({
                        "text": page_text.strip(),
                        "page": page_num + 1,
                        "source": source_name,
                    })

                # Extract images
                image_list = page.get_images(full=True)
                for img_idx, img_info in enumerate(image_list):
                    try:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        if base_image:
                            image_bytes = base_image["image"]
                            img_ext = base_image.get("ext", "png")
                            img_filename = f"{pdf_path.stem}_p{page_num+1}_img{img_idx+1}.{img_ext}"
                            img_save_path = self.images_dir / img_filename

                            # Only save images larger than 5KB (skip tiny icons)
                            if len(image_bytes) > 5120:
                                with open(img_save_path, "wb") as f:
                                    f.write(image_bytes)
                                image_paths.append({
                                    "path": str(img_save_path),
                                    "page": page_num + 1,
                                    "source": source_name,
                                })
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_idx} from page {page_num+1}: {e}")

            doc.close()
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")

        # --- Extract tables with pdfplumber ---
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for tbl_idx, table in enumerate(tables):
                        if table and len(table) > 1:
                            try:
                                # Use first row as header
                                headers = [str(h) if h else f"col_{i}" for i, h in enumerate(table[0])]
                                df = pd.DataFrame(table[1:], columns=headers)

                                # Save as CSV
                                csv_filename = f"{pdf_path.stem}_p{page_num+1}_tbl{tbl_idx+1}.csv"
                                csv_path = self.tables_dir / csv_filename
                                df.to_csv(csv_path, index=False)

                                # Convert to markdown
                                try:
                                    md = df.to_markdown(index=False)
                                except Exception:
                                    md = df.to_string(index=False)

                                table_data.append({
                                    "dataframe": df,
                                    "page": page_num + 1,
                                    "source": source_name,
                                    "markdown": md,
                                    "csv_path": str(csv_path),
                                })
                            except Exception as e:
                                logger.warning(f"Failed to process table {tbl_idx} on page {page_num+1}: {e}")
        except Exception as e:
            logger.error(f"pdfplumber table extraction failed: {e}")

        logger.info(
            f"Extraction complete — Text: {len(text_blocks)} pages, "
            f"Images: {len(image_paths)}, Tables: {len(table_data)}"
        )
        return text_blocks, image_paths, table_data
