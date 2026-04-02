"""
🧠 Local RAG Knowledge Assistant — Main Streamlit Application
100% local, privacy-first document Q&A with multimodal intelligence.
"""

import streamlit as st
import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Import UI components
from ui.styles import CUSTOM_CSS
from ui.sidebar import render_sidebar
from ui.filter_buttons import render_filter_buttons
from ui.dashboard_metrics import render_metrics
from ui.chat_interface import render_chat_interface, add_message

from config.settings import *
from utils.helpers import setup_logging, ensure_data_directories

# Setup
setup_logging()
ensure_data_directories()
logger = logging.getLogger(__name__)

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Local RAG Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============ SESSION STATE INITIALIZATION ============
def init_session_state():
    defaults = {
        "messages": [],
        "uploaded_files_list": [],
        "content_filter": None,
        "processing": False,
        "progress": 0,
        "status_text": "",
        "all_documents": [],
        "system_initialized": False,
        "system_error": None,
        "stats": {
            "total_chunks": 0,
            "text_chunks": 0,
            "image_chunks": 0,
            "table_chunks": 0,
            "total_files": 0,
            "model_loaded": False,
            "ram_usage_mb": 0,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============ INITIALIZE SYSTEM COMPONENTS ============
@st.cache_resource(show_spinner=False)
def initialize_system():
    """Load all models and create managers — runs once and is cached."""
    try:
        from core.embedding_manager import EmbeddingManager
        from core.vectorstore_manager import VectorStoreManager
        from core.llm_manager import LLMManager
        from core.memory_manager import MemoryManager
        from core.pdf_processor import PDFProcessor
        from core.text_pipeline import TextPipeline
        from core.image_pipeline import ImagePipeline
        from core.table_pipeline import TablePipeline

        api_key = os.getenv("SEARCHAPI_KEY", "")

        # 1. Load embedding model
        embedding_manager = EmbeddingManager()
        embeddings = embedding_manager.get_embeddings()

        # 2. Initialize vector store
        vs_manager = VectorStoreManager(embeddings, VECTORSTORE_DIR)

        # 3. Load LLM
        llm = None
        llm_error = None
        try:
            llm_manager = LLMManager(LLM_MODEL_PATH)
            llm = llm_manager.get_llm()
        except FileNotFoundError as e:
            llm_error = str(e)
            logger.warning(f"LLM not loaded: {e}")
        except Exception as e:
            llm_error = str(e)
            logger.warning(f"LLM loading failed: {e}")

        # 4. Initialize memory
        memory_manager = MemoryManager()

        # 5. Initialize processors
        pdf_processor = PDFProcessor()
        text_pipeline = TextPipeline(embeddings)
        image_pipeline = ImagePipeline(api_key)
        table_pipeline = TablePipeline(api_key)

        return {
            "embeddings": embeddings,
            "vs_manager": vs_manager,
            "llm": llm,
            "llm_error": llm_error,
            "memory_manager": memory_manager,
            "pdf_processor": pdf_processor,
            "text_pipeline": text_pipeline,
            "image_pipeline": image_pipeline,
            "table_pipeline": table_pipeline,
        }

    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return {"error": str(e)}


# ============ PROCESS UPLOADED FILES ============
def process_uploaded_file(uploaded_file, system, settings):
    """Process a single uploaded PDF through the multimodal pipeline."""
    all_docs = []

    try:
        # Step 1: Save uploaded file
        save_dir = DATA_DIR / "uploaded_pdfs"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Step 2: Extract text, images, tables from PDF
        text_blocks, image_paths, table_data = system["pdf_processor"].process(save_path)

        # Step 3: Process TEXT
        text_docs = system["text_pipeline"].process(
            text_blocks,
            source_file=uploaded_file.name,
            chunk_size=settings["chunk_size"],
            chunk_overlap=settings["chunk_overlap"],
        )
        all_docs.extend(text_docs)

        # Step 4: Process IMAGES
        image_docs = system["image_pipeline"].process(
            image_paths,
            source_file=uploaded_file.name,
        )
        all_docs.extend(image_docs)

        # Step 5: Process TABLES
        table_docs = system["table_pipeline"].process(
            table_data,
            source_file=uploaded_file.name,
        )
        all_docs.extend(table_docs)

        # Step 6: Store in ChromaDB
        if all_docs:
            system["vs_manager"].add_documents(all_docs)

        # Update session state
        st.session_state.all_documents.extend(all_docs)
        st.session_state.uploaded_files_list.append(uploaded_file.name)

        # Update stats
        st.session_state.stats["total_chunks"] += len(all_docs)
        st.session_state.stats["text_chunks"] += len(text_docs)
        st.session_state.stats["image_chunks"] += len(image_docs)
        st.session_state.stats["table_chunks"] += len(table_docs)
        st.session_state.stats["total_files"] += 1

        return True, (
            f"✅ **{uploaded_file.name}** processed successfully!\n\n"
            f"📄 Text chunks: **{len(text_docs)}** | "
            f"🖼️ Image chunks: **{len(image_docs)}** | "
            f"📊 Table chunks: **{len(table_docs)}**"
        )

    except Exception as e:
        logger.error(f"File processing error: {e}")
        return False, f"❌ Error processing {uploaded_file.name}: {str(e)}"


# ============ HANDLE QUERY ============
def handle_query(query, content_filter, system, settings):
    """Process user query through the RAG pipeline."""
    try:
        if not system.get("llm"):
            return (
                "⚠️ **LLM not loaded.** Please download the TinyLlama GGUF model and place it in the `models/` folder.\n\n"
                "Download from: [TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)"
            ), []

        from core.retriever import AdvancedRetriever
        from core.rag_chain import RAGChain

        # Build advanced retriever
        retriever = AdvancedRetriever(
            vectorstore_manager=system["vs_manager"],
            llm=system["llm"],
            all_documents=st.session_state.all_documents,
        )

        # Retrieve with optional content type filter
        retrieved_docs = retriever.retrieve(
            query=query,
            content_type_filter=content_filter,
            top_k=settings["top_k"],
        )

        if not retrieved_docs:
            return (
                "🔍 I couldn't find any relevant information in the uploaded documents for your query. "
                "Try rephrasing your question or uploading additional documents."
            ), []

        # Build RAG chain and generate answer
        rag_chain = RAGChain(
            llm=system["llm"],
            memory=system["memory_manager"].get_memory(),
        )

        answer = rag_chain.ask(query, retrieved_docs)

        # Prepare sources
        sources = []
        for doc in retrieved_docs:
            sources.append({
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "?"),
                "content_type": doc.metadata.get("content_type", "text"),
                "preview": doc.page_content[:200],
            })

        return answer, sources

    except Exception as e:
        logger.error(f"Query handling error: {e}")
        return f"❌ Error generating answer: {str(e)}", []


# ============ MAIN APP ============
def main():
    # ── Header ──
    st.markdown("""
    <div class="app-header">
        <h1>🧠 Local RAG Knowledge Assistant</h1>
        <p>Your 100% local, privacy-first document Q&A system with multimodal intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load System ──
    with st.spinner("🔄 Loading AI Models... This may take a minute on first run."):
        system = initialize_system()

    if "error" in system:
        st.error(f"⚠️ System initialization failed: {system['error']}")
        st.info("Please check that all dependencies are installed correctly.")
        return

    st.session_state.system_initialized = True

    # ── Status Bar ──
    llm_status = "green" if system.get("llm") else "red"
    llm_text = "Loaded" if system.get("llm") else "Not Found"
    db_status = "green"

    st.markdown(f"""
    <div class="status-bar">
        <span><span class="status-dot {llm_status}"></span>LLM: {llm_text}</span>
        <span><span class="status-dot {db_status}"></span>Vector DB: Active</span>
        <span><span class="status-dot green"></span>Embeddings: Ready</span>
        <span style="margin-left:auto; color:#64748b;">
            🕐 {datetime.now().strftime("%H:%M")}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Show LLM warning if not loaded
    if system.get("llm_error"):
        st.warning(
            f"⚠️ **LLM not loaded:** {system['llm_error']}\n\n"
            "You can still upload and process PDFs. The chat will work once the model is downloaded."
        )

    # ── Sidebar ──
    settings = render_sidebar()

    # Handle sidebar actions
    if settings["clear_chat"]:
        st.session_state.messages = []
        system["memory_manager"].clear_memory()
        st.rerun()

    if settings["clear_db"]:
        if VECTORSTORE_DIR.exists():
            shutil.rmtree(VECTORSTORE_DIR)
        st.session_state.all_documents = []
        st.session_state.uploaded_files_list = []
        st.session_state.stats = {
            "total_chunks": 0, "text_chunks": 0,
            "image_chunks": 0, "table_chunks": 0,
            "total_files": 0, "model_loaded": True, "ram_usage_mb": 0,
        }
        st.cache_resource.clear()
        st.rerun()

    # Update RAM usage
    try:
        import psutil
        process = psutil.Process(os.getpid())
        st.session_state.stats["ram_usage_mb"] = round(
            process.memory_info().rss / 1024 / 1024
        )
    except Exception:
        st.session_state.stats["ram_usage_mb"] = 0

    st.session_state.stats["model_loaded"] = system.get("llm") is not None

    # ── Dashboard Metrics ──
    render_metrics(st.session_state.stats)

    st.markdown("---")

    # ── Filter Buttons ──
    content_filter = render_filter_buttons()

    st.markdown("---")

    # ── Process Uploaded Files ──
    if settings["uploaded_files"]:
        for uploaded_file in settings["uploaded_files"]:
            if uploaded_file.name not in st.session_state.uploaded_files_list:
                with st.spinner(f"📄 Processing **{uploaded_file.name}**..."):
                    success, message = process_uploaded_file(
                        uploaded_file, system, settings
                    )
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # ── Chat Interface ──
    user_input = render_chat_interface()

    # Handle user input
    if user_input:
        if not st.session_state.uploaded_files_list:
            add_message(
                "assistant",
                "⚠️ Please upload a PDF document first before asking questions. "
                "Use the **sidebar** on the left to upload files.",
            )
            st.rerun()
        else:
            # Add user message
            add_message("user", user_input)

            # Generate answer
            with st.spinner("🤔 Thinking..."):
                answer, sources = handle_query(
                    user_input, content_filter, system, settings
                )

            # Add assistant response
            add_message("assistant", answer, sources)
            st.rerun()

    # ── Export Chat ──
    if settings["export_chat"] and st.session_state.messages:
        chat_text = "\n\n".join([
            f"{'👤 User' if m['role'] == 'user' else '🤖 Assistant'} [{m.get('timestamp', '')}]:\n{m['content']}"
            for m in st.session_state.messages
        ])
        st.download_button(
            "📥 Download Chat History",
            chat_text,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
