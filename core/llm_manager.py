"""
LLM Manager — Load and manage LLM (Using HuggingFace Llama 3.1 8B via OpenAI API struct).
"""

import os
import logging
from config.settings import LLM_TEMPERATURE

logger = logging.getLogger(__name__)


class LLMManager:
    """Loads and provides the LLM model via HuggingFace Inference API."""

    def __init__(self, model_path=None, provider="HuggingFace (Llama-3.1)", ollama_model="qwen2.5:3b"):
        self.provider = provider
        
        if "Ollama" in provider:
            logger.info(f"Initializing Local Ollama ({ollama_model})")
            try:
                # Try new langchain-ollama package first
                try:
                    from langchain_ollama import ChatOllama
                except ImportError:
                    from langchain_community.chat_models import ChatOllama
                    
                self.llm = ChatOllama(
                    model=ollama_model,
                    temperature=LLM_TEMPERATURE,
                    num_ctx=16384,
                )
                logger.info("LLM initialized successfully via Local Ollama")
            except Exception as e:
                logger.error(f"Local Ollama initialization failed: {e}")
                raise Exception(f"Failed to connect to local Ollama. Ensure Ollama is running and {ollama_model} is pulled. Error: {e}")
        else:
            logger.info("Initializing HuggingFace Llama 3.1 8B API")
            hf_token = os.environ.get("HF_TOKEN")
            if not hf_token:
                logger.error("HF_TOKEN environment variable not found.")
                raise ValueError("HF_TOKEN environment variable is required to use the HuggingFace API.")
                
            try:
                from langchain_openai import ChatOpenAI
                
                self.llm = ChatOpenAI(
                    model="meta-llama/Llama-3.1-8B-Instruct:novita",
                    api_key=hf_token,
                    base_url="https://router.huggingface.co/v1",
                    temperature=LLM_TEMPERATURE,
                )
                logger.info("LLM initialized successfully via HuggingFace API")
            except ImportError:
                logger.error("langchain-openai package is missing.")
                raise ImportError("Please install langchain-openai to use the ChatGPT-compatible API.")

    def get_llm(self):
        """Return the LangChain-compatible LLM instance."""
        return self.llm
