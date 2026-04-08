"""
Image Pipeline — Extract meaning from images using multiple OCR strategies.
Priority: pytesseract → easyocr → enhanced PIL analysis.
"""

from langchain_core.documents import Document
from config.settings import CONTENT_TYPE_IMAGE
import logging
import os

logger = logging.getLogger(__name__)


class ImagePipeline:
    """Processes extracted images into text descriptions stored as Documents."""

    def __init__(self, api_key=""):
        self.api_key = api_key
        self._easyocr_reader = None

    def process(self, image_paths, source_file="unknown"):
        """
        Process image paths into LangChain Documents.

        Uses multiple OCR strategies with fallbacks:
        1. pytesseract (if installed with Tesseract binary)
        2. easyocr (pure Python, no external binary needed)
        3. Enhanced PIL analysis (always works)

        Args:
            image_paths: list of dicts with {path, page, source}
            source_file: original PDF filename

        Returns:
            list of LangChain Documents tagged with content_type="image"
        """
        if not image_paths:
            return []

        documents = []

        for img_info in image_paths:
            img_path = img_info["path"]
            page_num = img_info["page"]

            # Skip if file doesn't exist
            if not os.path.exists(img_path):
                logger.warning(f"Image file not found: {img_path}")
                continue

            extracted_text = ""
            method = "none"

            # Strategy 0: Google AI Mode (SearchApi)
            if self.api_key and (not extracted_text or not self._is_useful_text(extracted_text)):
                try:
                    text = self._try_google_ai_mode(img_path)
                    if self._is_useful_text(text):
                        extracted_text = text
                        method = "google_ai_mode"
                        logger.info(f"Successfully processed image with Google AI Mode: {img_path}")
                except Exception as e:
                    logger.warning(f"Google AI Mode failed: {e}")

            # Strategy 1: pytesseract
            if not extracted_text or not self._is_useful_text(extracted_text):
                try:
                    text = self._try_pytesseract(img_path)
                    if self._is_useful_text(text):
                        extracted_text = text
                        method = "pytesseract"
                except Exception as e:
                    logger.debug(f"pytesseract failed: {e}")

            # Strategy 2: easyocr
            if not extracted_text or not self._is_useful_text(extracted_text):
                try:
                    text = self._try_easyocr(img_path)
                    if self._is_useful_text(text):
                        extracted_text = text
                        method = "easyocr"
                except Exception as e:
                    logger.debug(f"easyocr failed: {e}")

            # Strategy 3: Enhanced PIL analysis (always produces output)
            if not extracted_text or not self._is_useful_text(extracted_text):
                extracted_text = self._enhanced_pil_analysis(img_path)
                method = "pil_analysis"

            # Always create a document for every image (never skip)
            img_name = os.path.basename(img_path)
            full_text = (
                f"[Image: {img_name} from {source_file}, page {page_num}]\n"
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

    def _is_useful_text(self, text):
        """Check if extracted text is actually useful (not just error msgs)."""
        if not text or not text.strip():
            return False
        useless = [
            "no text detected", "ocr not available", "ocr failed",
            "image processing failed", "could not be processed",
            "image file present but",
        ]
        lower = text.strip().lower()
        return not any(u in lower for u in useless) and len(text.strip()) > 10

    def _try_pytesseract(self, image_path):
        """Try OCR with pytesseract."""
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)

        # Preprocess: convert to grayscale for better OCR
        if img.mode != 'L':
            img = img.convert('L')

        text = pytesseract.image_to_string(img, config='--oem 3 --psm 6')
        return text.strip()

    def _try_easyocr(self, image_path):
        """Try OCR with easyocr (no external binary needed)."""
        try:
            import easyocr
        except ImportError:
            return ""

        if self._easyocr_reader is None:
            try:
                self._easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            except Exception as e:
                logger.warning(f"easyocr Reader init failed: {e}")
                return ""

        results = self._easyocr_reader.readtext(image_path)
        texts = [r[1] for r in results if r[2] > 0.3]  # confidence > 30%
        return "\n".join(texts)

    def _enhanced_pil_analysis(self, image_path):
        """Enhanced image analysis using PIL — describes size, colors, content type guess."""
        try:
            from PIL import Image
            import struct

            img = Image.open(image_path)
            w, h = img.size
            mode = img.mode
            fmt = img.format or "Unknown"

            # Determine image characteristics
            aspect = w / h if h > 0 else 1
            pixel_count = w * h

            # Analyze dominant colors
            color_info = self._analyze_colors(img)

            # Build descriptive text
            parts = [
                f"Image dimensions: {w}x{h} pixels ({fmt} format, {mode} color mode).",
            ]

            # Guess content type based on characteristics
            if aspect > 2.5 or aspect < 0.4:
                parts.append("This appears to be a banner or header/footer image.")
            elif w < 100 and h < 100:
                parts.append("This is a small icon or logo image.")
            elif abs(aspect - 1) < 0.2:
                parts.append("This is roughly square, possibly a photo, chart, or diagram.")
            else:
                parts.append("This is a standard-sized image, possibly a chart, screenshot, or illustration.")

            if color_info:
                parts.append(f"Color analysis: {color_info}")

            # Check if image has text-like properties (high contrast B&W)
            if mode in ('1', 'L'):
                parts.append("This is a grayscale/monochrome image, likely containing text or line drawings.")

            return " ".join(parts)

        except Exception as e:
            return f"Image present on this page (analysis error: {str(e)})."

    def _analyze_colors(self, img):
        """Analyze dominant colors in the image."""
        try:
            # Resize for fast analysis
            small = img.copy()
            small.thumbnail((50, 50))
            small = small.convert('RGB')

            pixels = list(small.getdata())
            if not pixels:
                return ""

            # Get average color
            avg_r = sum(p[0] for p in pixels) // len(pixels)
            avg_g = sum(p[1] for p in pixels) // len(pixels)
            avg_b = sum(p[2] for p in pixels) // len(pixels)

            # Determine if mostly white, dark, colorful
            brightness = (avg_r + avg_g + avg_b) / 3

            if brightness > 230:
                return "Predominantly white/light background (likely a document or chart with white background)."
            elif brightness < 50:
                return "Predominantly dark image."
            elif max(avg_r, avg_g, avg_b) - min(avg_r, avg_g, avg_b) > 80:
                return f"Colorful image with dominant tones (RGB avg: {avg_r},{avg_g},{avg_b})."
            else:
                return f"Neutral-toned image (RGB avg: {avg_r},{avg_g},{avg_b})."

        except Exception:
            return ""

    def _upload_to_tmpfiles(self, image_path):
        """Uploads an image to tmpfiles.org and returns a direct public URL."""
        upstream_error = None
        
        # Try tmpfiles.org
        try:
            import requests
            with open(image_path, 'rb') as f:
                response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=15)
            response.raise_for_status()
            data = response.json()
            if "data" in data and "url" in data["data"]:
                original_url = data["data"]["url"]
                return original_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        except Exception as e:
            upstream_error = e

        # Fallback to catbox.moe if tmpfiles.org fails
        try:
            import requests
            with open(image_path, 'rb') as f:
                response = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=15)
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            logger.error(f"Catbox fallback failed: {e}. Tmpfiles error was: {upstream_error}")
            return None

    def _try_google_ai_mode(self, image_path):
        """Use SearchApi Google AI Mode to extract deep meaning from image."""
        import requests
        
        # 1. Get temporary public URL
        public_url = self._upload_to_tmpfiles(image_path)
        if not public_url:
            raise Exception("Could not generate public URL for image.")
            
            # 2. Call SearchApi
        try:
            import time
            url = "https://www.searchapi.io/api/v1/search"
            params = {
                "engine": "google_ai_mode",
                "q": "Analyze this image in deep detail. If it is a diagram, chart, or flowchart, extract all text, arrows, and explain the relationships and feedback loops completely.",
                "url": public_url,
                "api_key": self.api_key
            }
            
            time.sleep(2)  # Prevent 429 Too Many Requests
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Combine text blocks or just use markdown
            if "markdown" in data and data["markdown"]:
                return data["markdown"]
                
            if "text_blocks" in data:
                blocks = data["text_blocks"]
                return "\n\n".join([b.get("answer", "") for b in blocks if "answer" in b])
                
            return ""
        except Exception as e:
            raise Exception(f"SearchApi call failed: {e}")
