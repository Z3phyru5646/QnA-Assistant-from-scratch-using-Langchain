# 🧠 Local RAG Knowledge Assistant

> **100% local, privacy-first document Q&A with multimodal intelligence.**

A powerful Retrieval-Augmented Generation (RAG) system that processes PDF documents containing text, images, and tables — and lets you ask questions in a beautiful Streamlit dashboard.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Multimodal PDF Processing** | Extracts text, images, and tables separately |
| 🔍 **Hybrid Search** | Combines vector similarity (MMR) + BM25 keyword search |
| 🔄 **Re-ranking** | Cross-encoder model re-scores results for precision |
| 🧠 **Local LLM** | TinyLlama-1.1B in GGUF Q4 format (~800MB RAM) |
| 🖼️ **Image Processing** | Google Lens API + pytesseract OCR fallback |
| 📊 **Table Intelligence** | Google AI Mode API + markdown conversion |
| 🎯 **Content Filtering** | Query text-only, image-only, or table-only content |
| 💬 **Conversation Memory** | Multi-turn chat with context awareness |
| 🎨 **Premium Dark UI** | Gradient cards, animations, glassmorphism styling |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Download TinyLlama Model

Download the GGUF model file and place it in the `models/` folder:

```
models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

**Download:** [TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)

### 3. Create Directories

```bash
mkdir -p data/uploaded_pdfs data/extracted_images data/extracted_tables data/processed_texts
mkdir -p vectorstore/chroma_db models
```

### 4. Run the App

```bash
streamlit run app.py
```

---

## 🏗️ Architecture

```
USER UPLOADS PDF
       │
       ▼
┌─────────────────────────┐
│    PDF PROCESSOR         │
│  (PyMuPDF + pdfplumber) │
└─────┬───────┬───────┬───┘
      │       │       │
      ▼       ▼       ▼
   TEXT    IMAGES   TABLES
      │       │       │
      ▼       ▼       ▼
  Recursive  Google   Google
  + Semantic  Lens    AI Mode
  Chunking    API      API
      │       │       │
      └───────┼───────┘
              │
              ▼
    ┌─────────────────┐
    │  all-MiniLM-L6-v2│  ← Embedding (384d)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │    ChromaDB      │  ← Vector Store (HNSW + cosine)
    └────────┬────────┘
             │
    USER ASKS QUESTION
             │
             ▼
    ┌─────────────────────┐
    │ ADVANCED RETRIEVER   │
    │ • Hybrid: Vec + BM25│
    │ • MMR diversity     │
    │ • Cross-Encoder     │
    │ • Content filter    │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────┐
    │ TinyLlama-1.1B  │  ← Local LLM (Q4, CPU)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ ANSWER + SOURCES│  → Streamlit UI
    └─────────────────┘
```

---

## 📁 Project Structure

```
offline-rag-assistant/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env                       # API keys (SearchAPI)
├── .streamlit/config.toml     # Streamlit theme config
│
├── config/
│   └── settings.py            # All configurable parameters
│
├── core/
│   ├── pdf_processor.py       # PDF → text, images, tables
│   ├── text_pipeline.py       # Text chunking (recursive + semantic)
│   ├── image_pipeline.py      # Image → text via OCR/Lens API
│   ├── table_pipeline.py      # Table → text via markdown/AI Mode
│   ├── embedding_manager.py   # HuggingFace embedding model
│   ├── vectorstore_manager.py # ChromaDB operations
│   ├── retriever.py           # Hybrid search + re-ranking
│   ├── llm_manager.py         # TinyLlama GGUF loading
│   ├── rag_chain.py           # LangChain LCEL RAG pipeline
│   └── memory_manager.py      # Conversation buffer memory
│
├── ui/
│   ├── styles.py              # Custom CSS (dark theme)
│   ├── sidebar.py             # File upload + settings
│   ├── chat_interface.py      # Chat messages + input
│   ├── dashboard_metrics.py   # Metric cards
│   └── filter_buttons.py      # Content type filter
│
├── utils/
│   ├── google_lens_api.py     # SearchAPI Google Lens wrapper
│   ├── google_ai_mode_api.py  # SearchAPI AI Mode wrapper
│   └── helpers.py             # Utility functions
│
├── models/                    # GGUF model file
├── data/                      # Extracted content
└── vectorstore/               # ChromaDB persistent storage
```

---

## 🔑 API Keys

The `.env` file contains the SearchAPI key for Google Lens and AI Mode:

```
SEARCHAPI_KEY=your_key_here
```

These APIs are **optional** — the system works fully offline with pytesseract OCR and direct table conversion.

---

## ⚙️ Configuration

All parameters are in `config/settings.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CHUNK_SIZE` | 500 | Characters per text chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |
| `TOP_K_RESULTS` | 5 | Documents to retrieve |
| `LLM_TEMPERATURE` | 0.3 | Generation temperature |
| `MMR_DIVERSITY_SCORE` | 0.3 | Diversity vs relevance balance |
| `BM25_WEIGHT` | 0.3 | Keyword search weight |
| `VECTOR_WEIGHT` | 0.7 | Semantic search weight |

---

## 📝 License

MIT License — Free for personal and commercial use.
