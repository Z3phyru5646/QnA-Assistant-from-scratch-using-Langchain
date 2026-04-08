"""
Summarizer — Generates summaries for individual content types.
Fixed with retry logic, better truncation, and extractive fallback.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPTS = {
    "text": """You are a document summarization expert. Summarize the following TEXT content extracted from uploaded documents. Provide a clear, comprehensive summary covering all key points, main arguments, and important details.

TEXT CONTENT:
{content}

Provide a well-structured summary with bullet points for key findings:""",

    "image": """You are a document analysis expert. Below are descriptions of IMAGES extracted from uploaded documents. Summarize what these images depict, their significance, and any key visual information they convey.

IMAGE DESCRIPTIONS:
{content}

Provide a summary of all visual content found in the documents:""",

    "table": """You are a data analysis expert. Below is TABLE data extracted from uploaded documents. Summarize the key data points, trends, patterns, and important information found in these tables.

TABLE DATA:
{content}

Provide a comprehensive summary of the tabular data:""",
}


class Summarizer:
    """Generates summaries for specific content types from the knowledge base."""

    def __init__(self, llm):
        self.llm = llm

    def summarize_by_type(self, content_type: str, documents: list) -> str:
        """
        Summarize all documents of a given content_type.
        """
        if not documents:
            type_label = {"text": "Text", "image": "Image", "table": "Table"}.get(content_type, content_type)
            return f"📭 No **{type_label}** content found in this notebook. Upload documents containing {type_label.lower()} data first."

        if not self.llm:
            # Fallback to extractive summary
            return self._extractive_summary(documents, content_type)

        # Combine all content
        combined = []
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            combined.append(f"[Source: {source}, Page {page}]\n{doc.page_content}")

        content_text = "\n\n---\n\n".join(combined)

        # Smart truncation — preserve complete sentences
        max_chars = 4000
        if len(content_text) > max_chars:
            truncated = content_text[:max_chars]
            # Find last sentence boundary
            last_period = truncated.rfind('. ')
            if last_period > max_chars * 0.8:
                truncated = truncated[:last_period + 1]
            content_text = truncated + "\n\n[... additional content truncated ...]"

        # Get the right prompt
        prompt_template = SUMMARIZE_PROMPTS.get(content_type, SUMMARIZE_PROMPTS["text"])

        # Try with retry
        for attempt in range(2):
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("human", prompt_template),
                ])
                chain = prompt | self.llm | StrOutputParser()
                summary = chain.invoke({"content": content_text})
                return summary
            except Exception as e:
                logger.warning(f"Summarization attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    # Retry with less content
                    content_text = content_text[:2000]
                else:
                    logger.error(f"Summarization failed for {content_type}: {e}")
                    return self._extractive_summary(documents, content_type)

        return "❌ Summary generation failed after retries."

    def _extractive_summary(self, documents, content_type):
        """Fallback extractive summary when LLM is unavailable."""
        type_label = {"text": "Text", "image": "Image", "table": "Table"}.get(content_type, content_type)

        summary_parts = [f"### 📋 {type_label} Summary (Extractive)\n"]
        summary_parts.append(f"*Found {len(documents)} {type_label.lower()} chunk(s) across your documents.*\n")

        # Show top content snippets
        for i, doc in enumerate(documents[:5]):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            preview = doc.page_content[:200].strip()
            summary_parts.append(f"**Source {i+1}:** {source} (Page {page})")
            summary_parts.append(f"> {preview}...\n")

        if len(documents) > 5:
            summary_parts.append(f"*... and {len(documents) - 5} more chunk(s).*")

        summary_parts.append("\n*⚠️ This is an extractive preview. Load the LLM for AI-generated summaries.*")

        return "\n".join(summary_parts)
