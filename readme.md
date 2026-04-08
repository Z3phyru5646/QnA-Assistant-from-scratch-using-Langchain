# 🧠 Local RAG Knowledge Assistant

A privacy-first, 100% local, multi-modal Retrieval-Augmented Generation (RAG) assistant built using LangChain, Streamlit, and ChromaDB. This project allows users to chat with their documents (PDF, DOCX, TXT), images, and tables securely using local Language Models (via Ollama) or hosted APIs (HuggingFace Llama 3).

## ✨ Key Features
- **Multi-Modal Document Processing:** Extracts not just text, but images and tables from PDFs.
- **Advanced Image Understanding:** Automatically routes complex charts and diagrams through **Google AI Mode** (SearchApi) to describe logic flow and relationships, enabling the system to "read" images.
- **Adaptive Text Chunking:** Intelligently chunks text by page and structure to prevent context tearing (e.g., separating titles from bullet points).
- **Notebook Isolation:** Create multiple distinct workspaces (notebooks). Changing your notebook changes the vector database context, keeping your projects separate.
- **Guardrails & Autocorrect:** Domain-aware query autocorrection and semantic guardrails to reject off-topic questions.
- **Source Citations:** Generates exact source references and metadata for where information was dynamically retrieved.
- **Responsive Streamlit Dashboard:** Dual-panel UI with live metrics and interactive chat.

## 🛠️ Tech Stack
- **Framework:** [LangChain](https://python.langchain.com/)
- **UI:** [Streamlit](https://streamlit.io/)
- **Vector Store:** [ChromaDB](https://www.trychroma.com/)
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **LLM Engine:** Local **Ollama** (e.g. `qwen2.5:3b`, `llama3`) or HuggingFace API.
- **Document Parsing:** PyMuPDF, pdfplumber, python-docx
- **OCR/Vision:** SearchApi (Google AI Mode), pytesseract, easyocr.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally.
- *Optional:* Tesseract OCR installed on your system.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/Z3phyru5646/QnA-Assistant-from-scratch-using-Langchain.git
cd QnA-Assistant-from-scratch-using-Langchain
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
# Optional: for HuggingFace models
HF_TOKEN=your_huggingface_token

# Optional: for Google AI Image parsing of complex flowcharts
SEARCHAPI_KEY=your_searchapi_key
```

### 4. Running the App
```bash
streamlit run app.py
```

### 5. Managing Models
To use local models, ensure you have pulled them using Ollama in your terminal:
```bash
ollama pull qwen2.5:3b
```
Select the corresponding model in the sidebar dropdown in the UI.

## 📂 Project Structure
```text
📦 GenAI_Project
 ┣ 📂 core               # Core backend modules (Pipelines, LLM, Memory, VectorDB)
 ┣ 📂 config             # Settings and internationalization (i18n)
 ┣ 📂 data               # Persistent vector database and extracted files
 ┣ 📂 ui                 # Streamlit UI components (Chat, Sidebar, Dashboards)
 ┣ 📂 utils              # Helper functions, formatters, sanitizers
 ┣ 📜 app.py             # Main entry point for the Streamlit dashboard
 ┗ 📜 requirements.txt   # Python dependencies
```

## 📝 License
This project is open-source and available under the MIT License.
