"""
Google Lens API wrapper — Uses SearchAPI.io's Google Lens endpoint.
Docs: https://www.searchapi.io/docs/google-lens
"""

import requests
import logging
import os
import base64

logger = logging.getLogger(__name__)

SEARCHAPI_BASE = "https://www.searchapi.io/api/v1/search"


class GoogleLensAPI:
    """Extract text and visual information from images using Google Lens via SearchAPI."""

    def __init__(self, api_key):
        self.api_key = api_key

    def extract_from_image(self, image_path):
        """
        Send image to Google Lens API via SearchAPI and extract:
        - Text detected in the image (OCR)
        - Visual descriptions and matched content

        For local images, this uses pytesseract as fallback since
        Google Lens requires a publicly accessible URL.

        Args:
            image_path: local path to the image file

        Returns:
            Combined text description from the image
        """
        # Google Lens API requires a publicly accessible URL
        # For local files, we'll use pytesseract OCR instead
        # If you have images hosted online, you can pass the URL directly

        try:
            # Attempt OCR with pytesseract first (local, no API needed)
            text = self.fallback_ocr(image_path)
            if text and text.strip() and text != "No text detected in image.":
                return text
        except Exception:
            pass

        # If we have a URL instead of a local path, use the API
        if image_path.startswith(("http://", "https://")):
            return self._call_lens_api(image_path)

        return self.fallback_ocr(image_path)

    def _call_lens_api(self, image_url):
        """Call SearchAPI Google Lens endpoint with an image URL."""
        try:
            params = {
                "engine": "google_lens",
                "api_key": self.api_key,
                "url": image_url,
                "search_type": "all",
            }

            response = requests.get(SEARCHAPI_BASE, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            text_parts = []

            # Extract text results (OCR text from image)
            if "text_results" in result:
                for item in result["text_results"]:
                    txt = item.get("text", "")
                    if txt:
                        text_parts.append(txt)

            # Extract visual match titles/descriptions
            if "visual_matches" in result:
                for match in result["visual_matches"][:5]:
                    title = match.get("title", "")
                    if title:
                        text_parts.append(f"Visual match: {title}")

            # Extract knowledge graph info
            if "knowledge_graph" in result:
                kg = result["knowledge_graph"]
                if kg.get("title"):
                    text_parts.append(f"Identified as: {kg['title']}")
                if kg.get("description"):
                    text_parts.append(kg["description"])

            combined = "\n".join(filter(None, text_parts))
            return combined if combined else "No information extracted from image."

        except requests.exceptions.RequestException as e:
            logger.warning(f"Google Lens API request failed: {e}")
            return f"Image processing failed: {str(e)}"
        except Exception as e:
            logger.warning(f"Google Lens API error: {e}")
            return f"Image processing failed: {str(e)}"

    def fallback_ocr(self, image_path):
        """Fallback using pytesseract for local OCR."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip() if text.strip() else "No text detected in image."
        except ImportError:
            return "OCR not available (pytesseract not installed)."
        except Exception as e:
            return f"OCR failed: {str(e)}"
