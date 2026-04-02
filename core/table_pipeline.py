"""
Table Pipeline — Convert extracted tables to text and optionally enrich with Google AI Mode.
"""

from langchain_core.documents import Document
from config.settings import CONTENT_TYPE_TABLE
import logging

logger = logging.getLogger(__name__)


class TablePipeline:
    """Processes extracted tables into LangChain Documents."""

    def __init__(self, api_key=""):
        self.api_key = api_key

    def process(self, table_data_list, source_file="unknown"):
        """
        Process table data into LangChain Documents.

        Converts tables to markdown text, optionally enriched with
        Google AI Mode API interpretation.

        Args:
            table_data_list: list of dicts with {dataframe, page, source, markdown}
            source_file: original PDF filename

        Returns:
            list of LangChain Documents tagged with content_type="table"
        """
        if not table_data_list:
            return []

        documents = []
        ai_mode_api = None

        if self.api_key:
            try:
                from utils.google_ai_mode_api import GoogleAIModeAPI
                ai_mode_api = GoogleAIModeAPI(self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Google AI Mode API: {e}")

        for tbl_info in table_data_list:
            df = tbl_info["dataframe"]
            page_num = tbl_info["page"]
            markdown = tbl_info.get("markdown", "")
            method = "pdfplumber"

            # Build base description from the table structure
            base_text = self._table_to_text(df, markdown)

            # Optionally enrich with AI interpretation
            ai_interpretation = ""
            if ai_mode_api and markdown:
                try:
                    ai_interpretation = ai_mode_api.interpret_table(markdown)
                    method = "pdfplumber+google_ai_mode"
                except Exception as e:
                    logger.warning(f"Google AI Mode table interpretation failed: {e}")

            # Combine base text with AI interpretation
            full_text = base_text
            if ai_interpretation and not ai_interpretation.startswith("Table interpretation failed"):
                full_text += f"\n\nAI Interpretation:\n{ai_interpretation}"

            if full_text.strip():
                doc = Document(
                    page_content=full_text.strip(),
                    metadata={
                        "source": source_file,
                        "page": page_num,
                        "content_type": CONTENT_TYPE_TABLE,
                        "chunk_index": 0,
                        "extraction_method": method,
                    }
                )
                documents.append(doc)

        logger.info(f"Table pipeline produced {len(documents)} chunks from {len(table_data_list)} tables")
        return documents

    def _table_to_text(self, df, markdown=""):
        """Convert DataFrame to descriptive natural language text."""
        try:
            num_rows = len(df)
            num_cols = len(df.columns)
            col_names = ", ".join(str(c) for c in df.columns)

            text = f"[Table with {num_rows} rows and {num_cols} columns]\n"
            text += f"Columns: {col_names}\n\n"

            if markdown:
                text += markdown
            else:
                text += df.to_string(index=False)

            return text
        except Exception as e:
            logger.warning(f"Table to text conversion error: {e}")
            return str(df) if df is not None else "Table data unavailable."
