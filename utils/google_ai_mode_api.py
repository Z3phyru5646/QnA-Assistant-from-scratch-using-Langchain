"""
Google AI Mode API wrapper — Uses SearchAPI.io's Google AI Mode endpoint.
Docs: https://www.searchapi.io/docs/google-ai-mode-api
"""

import requests
import logging

logger = logging.getLogger(__name__)

SEARCHAPI_BASE = "https://www.searchapi.io/api/v1/search"


class GoogleAIModeAPI:
    """Interpret tables and content using Google AI Mode via SearchAPI."""

    def __init__(self, api_key):
        self.api_key = api_key

    def interpret_table(self, table_markdown, context=""):
        """
        Send table data to Google AI Mode API for intelligent interpretation.

        Args:
            table_markdown: table content in markdown format
            context: optional additional context about the table

        Returns:
            AI-generated summary and key insights about the table
        """
        try:
            query = (
                f"Analyze this table and provide a brief summary, "
                f"key insights, and important data points:\n\n{table_markdown[:1500]}"
            )

            params = {
                "engine": "google_ai_mode",
                "api_key": self.api_key,
                "q": query,
            }

            response = requests.get(SEARCHAPI_BASE, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Extract the AI-generated text
            text_parts = []

            # Get text blocks from the response
            if "text_blocks" in result:
                for block in result["text_blocks"]:
                    if block.get("type") == "paragraph":
                        answer = block.get("answer", "")
                        if answer:
                            text_parts.append(answer)
                    elif block.get("type") == "unordered_list":
                        for item in block.get("items", []):
                            if item.get("answer"):
                                text_parts.append(f"• {item['answer']}")

            # Alternatively, use the markdown field if available
            if not text_parts and "markdown" in result:
                return result["markdown"][:2000]

            combined = "\n".join(text_parts)
            return combined if combined else self.fallback_interpretation(table_markdown)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Google AI Mode API request failed: {e}")
            return self.fallback_interpretation(table_markdown)
        except Exception as e:
            logger.warning(f"Google AI Mode API error: {e}")
            return self.fallback_interpretation(table_markdown)

    def fallback_interpretation(self, table_markdown):
        """Simple fallback — return descriptive text about the table."""
        lines = table_markdown.strip().split("\n")
        return f"Table with {len(lines)} rows of data."
