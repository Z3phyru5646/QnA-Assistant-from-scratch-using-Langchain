"""
Autocorrect Engine — Spell-check queries using offline autocorrect library.
Learns domain vocabulary from uploaded documents.
"""

import re
import logging

logger = logging.getLogger(__name__)


class AutocorrectEngine:
    """Spell-checks user queries with domain-aware vocabulary."""

    def __init__(self):
        self._speller = None
        self._domain_words = set()
        self._init_speller()

    def _init_speller(self):
        try:
            from autocorrect import Speller
            self._speller = Speller(lang='en')
            logger.info("Autocorrect speller initialized")
        except ImportError:
            logger.warning("autocorrect library not installed, spell-check disabled")
            self._speller = None

    def learn_from_documents(self, documents):
        """Extract unique words from documents to build domain vocabulary."""
        for doc in documents:
            text = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
            self._domain_words.update(w.lower() for w in words)
        logger.info(f"Learned {len(self._domain_words)} domain words")

    def correct(self, query: str) -> tuple:
        """
        Correct spelling in query.
        Returns: (corrected_query, was_changed)
        """
        if not self._speller or not query.strip():
            return query, False

        words = query.split()
        corrected_words = []
        changed = False

        for word in words:
            clean = re.sub(r'[^\w]', '', word.lower())

            # Skip domain words, short words, numbers
            if clean in self._domain_words or len(clean) <= 2 or clean.isdigit():
                corrected_words.append(word)
                continue

            corrected = self._speller(word)
            if corrected.lower() != word.lower():
                corrected_words.append(corrected)
                changed = True
            else:
                corrected_words.append(word)

        return ' '.join(corrected_words), changed
