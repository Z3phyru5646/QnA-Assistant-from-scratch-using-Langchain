"""
Question Suggester — Generates follow-up questions from RAG responses.
Strategy 1: LLM-powered generation
Strategy 2: Template-based fallback (no LLM needed)
"""

import re
import logging

logger = logging.getLogger(__name__)

SUGGESTION_PROMPT = """Based on the following question and answer, suggest exactly 3 short follow-up questions the user might want to ask next. Each question should be on a new line, numbered 1-3. Keep them concise (under 15 words each).

Question: {question}
Answer: {answer}

Suggest 3 follow-up questions:"""


class QuestionSuggester:
    """Generates suggested follow-up questions."""

    def __init__(self, llm=None):
        self.llm = llm

    def suggest(self, question: str, answer: str) -> list:
        """
        Generate 3 follow-up question suggestions.
        Returns: list of 3 question strings
        """
        # Try LLM-powered suggestions first
        if self.llm:
            try:
                return self._llm_suggest(question, answer)
            except Exception as e:
                logger.warning(f"LLM suggestion failed: {e}")

        # Fallback to template-based
        return self._template_suggest(question, answer)

    def _llm_suggest(self, question: str, answer: str) -> list:
        """Use LLM to generate contextual suggestions."""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt = ChatPromptTemplate.from_messages([
            ("human", SUGGESTION_PROMPT),
        ])
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({"question": question, "answer": answer})

        # Parse numbered lines
        lines = result.strip().split('\n')
        suggestions = []
        for line in lines:
            clean = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
            if clean and len(clean) > 5:
                suggestions.append(clean)
            if len(suggestions) >= 3:
                break

        return suggestions[:3] if suggestions else self._template_suggest(question, answer)

    def _template_suggest(self, question: str, answer: str) -> list:
        """Generate template-based suggestions by extracting key terms."""
        # Extract key nouns/terms from the answer
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', answer)
        unique_terms = list(dict.fromkeys(words))[:5]

        suggestions = []

        if unique_terms:
            suggestions.append(f"Can you explain more about {unique_terms[0]}?")

        if len(unique_terms) > 1:
            suggestions.append(f"What is the relationship between {unique_terms[0]} and {unique_terms[1]}?")

        if len(unique_terms) > 2:
            suggestions.append(f"What are the key details about {unique_terms[2]}?")

        # Fallback generic suggestions
        while len(suggestions) < 3:
            fallbacks = [
                "Can you summarize the key points?",
                "What are the most important details?",
                "Are there any related topics in the documents?",
            ]
            for fb in fallbacks:
                if fb not in suggestions and len(suggestions) < 3:
                    suggestions.append(fb)

        return suggestions[:3]
