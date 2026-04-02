"""
RAG Chain — Assembles retrieval + generation pipeline using LangChain LCEL.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful knowledge assistant. Answer the user's question based ONLY on the provided context from uploaded documents. If the context doesn't contain enough information, say "I don't have enough information in the uploaded documents to answer this question."

Be concise, accurate, and always cite which source/page the information came from.

Context from documents:
{context}"""


class RAGChain:
    """Assembles the RAG pipeline: context formatting + prompt + LLM."""

    def __init__(self, llm, memory=None):
        self.llm = llm
        self.memory = memory

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "{question}"),
        ])

    def format_docs(self, docs):
        """Format retrieved documents into a context string with source citations."""
        if not docs:
            return "No relevant documents found."

        formatted = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            content_type = doc.metadata.get("content_type", "text")
            formatted.append(
                f"[Source {i+1}: {source}, Page {page}, Type: {content_type}]\n"
                f"{doc.page_content}"
            )
        return "\n\n---\n\n".join(formatted)

    def ask(self, question, retrieved_docs):
        """
        Generate an answer given a question and pre-retrieved documents.

        Args:
            question: user's question string
            retrieved_docs: list of LangChain Documents

        Returns:
            answer string
        """
        context = self.format_docs(retrieved_docs)

        try:
            chain = self.prompt | self.llm | StrOutputParser()
            answer = chain.invoke({
                "context": context,
                "question": question,
            })
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = f"Error generating answer: {str(e)}"

        # Save to memory if available
        if self.memory:
            try:
                self.memory.save_context(
                    {"input": question},
                    {"output": answer},
                )
            except Exception as e:
                logger.warning(f"Memory save failed: {e}")

        return answer
