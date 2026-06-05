The 3 main features that make this a bit apart from the rest---


1. Adaptive text chunking-
Breaking documents into the right pieces is very important for getting accurate
search results. the system uses adaptive text chunking which looks at the
structure of the document like headers bullet points and word count on each
page to decide the best chunk size. this stops meaning from being lost when
text is split and keeps the information intact before it is stored. this feature is
not available in any known local model tools including anythingllm

2. Guardrails-
to keep the assistant helpful focused and safe a multi layer guardrail system
checks user questions before processing them
topic relevance: the system checks if the question is related to the
uploaded documents by comparing how close the question is to the stored
content
content safety: it uses pattern matching to block harmful off topic or
manipulative questions and stops prompt injection attempts
scope enforcement: the system is set up so the llm only answers based on
the given content and this stops the assistant from making up wrong
answers

3. Query autocorrect-
since users often spell complex or technical words wrong the assistant has an
offline autocorrect engine. when documents are uploaded the system learns
special words by collecting unique terms from the text. when a user types a
question it is checked for spelling mistakes using this learned vocabulary. if a
mistake is found and fixed the system runs the search and shows the user a did
you mean message


Follow these steps to get the assistant running on the PC.

1. Prerequisites
Make sure you have Python 3.8+ installed. You'll also need an API key for your LLM (e.g., OpenAI, Cohere, or HuggingFace) depending on your config setup.

2. Installation
Clone this repository and install the required dependencies:
# Clone the repo
git clone [https://github.com/Z3phyru5646/QnA-Assistant-from-scratch-using-Langchain.git](https://github.com/Z3phyru5646/QnA-Assistant-from-scratch-using-Langchain.git)

cd QnA-Assistant-from-scratch-using-Langchain

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt


3. Environment Variables
Create a .env file in the root directory and add your API keys. (Check config/ for specific variable names).
OPENAI_API_KEY="your_api_key_here"
# Add any other required keys (e.g., Pinecone, Weaviate, etc.)

4. Ingesting Documents
Before asking questions, you need to feed the system some data. Drop your documents into your designated data folder (as set in your config), and run the ingestion script:
python ingest.py

5. Run the Application
Fire up the Streamlit app 'streamlit run app.py' to start chatting...


----How it Works (The Hybrid RAG Approach)
Standard RAG relies purely on vector embeddings, which is great for understanding the "meaning" of a query but can sometimes miss exact names, acronyms, or specific IDs.

This assistant solves that by using a Hybrid approach:

Dense Retriever: Uses embedding models (like OpenAI embeddings) to find contextually similar chunks.

Sparse Retriever: Uses traditional algorithms (like BM25) to match exact keywords.

Reciprocal Rank Fusion (RRF): The results from both retrievers are merged and reranked to provide the absolute best context to the LLM.
