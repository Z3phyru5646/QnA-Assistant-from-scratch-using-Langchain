"""
Image Pipeline — Extract meaning from images using Google Lens API + pytesseract fallback.
"""

from langchain_core.documents import Document
from config.settings import CONTENT_TYPE_IMAGE
import logging

logger = logging.getLogger(__name__)


class ImagePipeline:
    """Processes extracted images into text descriptions stored as Documents."""

    def __init__(self, api_key=""):
        self.api_key = api_key

    def process(self, image_paths, source_file="unknown"):
        """
        Process image paths into LangChain Documents.

        Uses Google Lens API (via SearchAPI) if key is provided,
        falls back to pytesseract for local OCR.

        Args:
            image_paths: list of dicts with {path, page, source}
            source_file: original PDF filename

        Returns:
            list of LangChain Documents tagged with content_type="image"
        """
        if not image_paths:
            return []

        documents = []
        lens_api = None

        if self.api_key:
            try:
                from utils.google_lens_api import GoogleLensAPI
                lens_api = GoogleLensAPI(self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Google Lens API: {e}")

        for img_info in image_paths:
            img_path = img_info["path"]
            page_num = img_info["page"]
            extracted_text = ""

            # Try Google Lens API first (requires publicly accessible URL)
            if lens_api:
                try:
                    extracted_text = lens_api.extract_from_image(img_path)
                    method = "google_lens"
                except Exception as e:
                    logger.warning(f"Google Lens failed for {img_path}: {e}")
                    extracted_text = ""

            # Fallback to pytesseract OCR
            if not extracted_text or extracted_text.startswith("Image processing failed"):
                extracted_text = self._fallback_ocr(img_path)
                method = "pytesseract"

            # Build a descriptive text from the image
            if extracted_text and extracted_text.strip():
                img_name = img_path.split("\\")[-1] if "\\" in img_path else img_path.split("/")[-1]
                full_text = (
                    f"[Image: {img_name} from page {page_num}]\n"
                    f"{extracted_text.strip()}"
                )

                doc = Document(
                    page_content=full_text,
                    metadata={
                        "source": source_file,
                        "page": page_num,
                        "content_type": CONTENT_TYPE_IMAGE,
                        "chunk_index": 0,
                        "extraction_method": method,
                        "image_path": img_path,
                    }
                )
                documents.append(doc)

        logger.info(f"Image pipeline produced {len(documents)} chunks from {len(image_paths)} images")
        return documents

    def _fallback_ocr(self, image_path):
        """Use pytesseract for local OCR fallback."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text if text.strip() else "No text detected in image."
        except ImportError:
            logger.warning("pytesseract not installed — using PIL basic info")
            return self._pil_fallback(image_path)
        except Exception as e:
            logger.warning(f"pytesseract OCR failed: {e}")
            return self._pil_fallback(image_path)

    def _pil_fallback(self, image_path):
        """Minimal fallback using PIL to describe image properties."""
        try:
            from PIL import Image
            img = Image.open(image_path)
            w, h = img.size
            mode = img.mode
            return f"Image ({w}x{h}, {mode} color mode). OCR not available."
        except Exception:
            return "Image file present but could not be processed."
