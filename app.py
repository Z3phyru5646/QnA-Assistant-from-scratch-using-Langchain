"""
🧠 Local RAG Knowledge Assistant — Main Streamlit Application
100% local, privacy-first document Q&A with multimodal intelligence.
Features: Notebook isolation, multi-format upload (PDF/DOCX/TXT),
          autocorrect, guardrails, dual-panel UI, suggested questions,
          multi-user auth, group/local query visibility, live translation,
          adaptive chunking, system monitoring, summarization.
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
from ui.citation_panel import render_citation_panel
from ui.login_page import render_login_page

from config.settings import *
from config.translations import t
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
        "active_notebook_id": None,
        "notebook_documents": {},
        "notebook_messages": {},
        "notebook_files": {},
        "suggested_questions": [],
        "suggestion_clicked": None,
        "authenticated": False,
        "user_data": None,
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


# ============ NOTEBOOK MANAGER (cached) ============
@st.cache_resource
def get_notebook_manager():
    from core.notebook_manager import NotebookManager
    return NotebookManager()


# ============ AUTOCORRECT ENGINE (cached) ============
@st.cache_resource
def get_autocorrect_engine():
    from core.autocorrect_engine import AutocorrectEngine
    return AutocorrectEngine()


# ============ INITIALIZE SYSTEM COMPONENTS ============
@st.cache_resource(show_spinner=False)
def initialize_system(llm_provider="HuggingFace (Llama-3.1)", ollama_model="qwen2.5:3b"):
    """Load all models and create managers — runs once and is cached per provider."""
    try:
        from core.embedding_manager import EmbeddingManager
        from core.vectorstore_manager import VectorStoreManager
        from core.llm_manager import LLMManager
        from core.memory_manager import MemoryManager
        from core.pdf_processor import PDFProcessor
        from core.docx_processor import DocxProcessor
        from core.txt_processor import TxtProcessor
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
            llm_manager = LLMManager(provider=llm_provider, ollama_model=ollama_model)
            llm = llm_manager.get_llm()
        except FileNotFoundError as e:
            llm_error = str(e)
            logger.warning(f"LLM not loaded: {e}")
        except Exception as e:
            llm_error = str(e)
            logger.warning(f"LLM loading failed: {e}")

        # 4. Initialize memory
        memory_manager = MemoryManager()

        # 5. Initialize processors (all formats)
        pdf_processor = PDFProcessor()
        docx_processor = DocxProcessor()
        txt_processor = TxtProcessor()
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
            "docx_processor": docx_processor,
            "txt_processor": txt_processor,
            "text_pipeline": text_pipeline,
            "image_pipeline": image_pipeline,
            "table_pipeline": table_pipeline,
        }

    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return {"error": str(e)}


# ============ SWITCH NOTEBOOK COLLECTION ============
def switch_notebook_collection(system, notebook, force=False):
    nb_id = notebook["id"]
    last_nb = st.session_state.get("_last_loaded_notebook_id")

    if not force and last_nb == nb_id:
        return

    if last_nb and last_nb != nb_id:
        save_notebook_state()

    collection_name = notebook.get("collection_name", CHROMA_COLLECTION_NAME)
    system["vs_manager"].reload_collection(collection_name)

    cached_docs = st.session_state.notebook_documents.get(nb_id)
    if cached_docs:
        st.session_state.all_documents = list(cached_docs)
    else:
        persisted_docs = system["vs_manager"].get_all_documents()
        st.session_state.all_documents = list(persisted_docs)
        st.session_state.notebook_documents[nb_id] = list(persisted_docs)

    if nb_id in st.session_state.notebook_messages:
        st.session_state.messages = list(st.session_state.notebook_messages[nb_id])
    else:
        st.session_state.messages = []
        st.session_state.notebook_messages[nb_id] = []

    if nb_id in st.session_state.notebook_files:
        st.session_state.uploaded_files_list = list(st.session_state.notebook_files[nb_id])
    else:
        pdf_files = notebook.get("pdf_files", [])
        file_names = [p["filename"] if isinstance(p, dict) else p for p in pdf_files]
        st.session_state.uploaded_files_list = file_names
        st.session_state.notebook_files[nb_id] = file_names

    st.session_state.stats.update({
        "total_chunks": notebook["stats"]["total_chunks"],
        "text_chunks": notebook["stats"]["text_chunks"],
        "image_chunks": notebook["stats"]["image_chunks"],
        "table_chunks": notebook["stats"]["table_chunks"],
        "total_files": len(notebook.get("pdf_files", [])),
    })
    selection_store = st.session_state.get("selected_docs_by_notebook", {})
    st.session_state.selected_docs = dict(selection_store.get(nb_id, {}))

    st.session_state._last_loaded_notebook_id = nb_id


# ============ SAVE CURRENT NOTEBOOK STATE ============
def save_notebook_state():
    nb_id = st.session_state.get("active_notebook_id")
    if nb_id:
        st.session_state.notebook_documents[nb_id] = st.session_state.all_documents
        st.session_state.notebook_messages[nb_id] = st.session_state.messages
        st.session_state.notebook_files[nb_id] = st.session_state.uploaded_files_list


def get_selected_sources_for_active_notebook(notebook_manager):
    """Return only the checked files that belong to the active notebook."""
    nb_id = st.session_state.get("active_notebook_id")
    if not nb_id:
        return []

    active_sources = notebook_manager.get_notebook_pdf_names(nb_id)
    if not active_sources:
        return []

    by_notebook = st.session_state.get("selected_docs_by_notebook", {})
    notebook_selection = by_notebook.get(nb_id, {})
    legacy_selection = st.session_state.get("selected_docs", {})

    selected = []
    for source in active_sources:
        is_selected = notebook_selection.get(source, legacy_selection.get(source, True))
        if is_selected:
            selected.append(source)

    return selected


# ============ GET FILE PROCESSOR ============
def get_processor_for_file(uploaded_file, system):
    """Return the appropriate processor based on file extension."""
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):
        return system["pdf_processor"]
    elif name.endswith('.docx'):
        return system["docx_processor"]
    elif name.endswith('.txt'):
        return system["txt_processor"]
    else:
        return None


# ============ PROCESS UPLOADED FILES ============
def process_uploaded_file(uploaded_file, system, settings, notebook_manager):
    """Process a single uploaded file through the multimodal pipeline."""
    all_docs = []
    nb_id = st.session_state.active_notebook_id

    try:
        # Step 1: Save uploaded file
        save_dir = DATA_DIR / "uploaded_pdfs" / nb_id
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Step 2: Get appropriate processor
        processor = get_processor_for_file(uploaded_file, system)
        if not processor:
            return False, f"❌ Unsupported file type: {uploaded_file.name}"

        # Step 3: Extract text, images, tables
        text_blocks, image_paths, table_data = processor.process(save_path)

        # Step 4: Process TEXT (with adaptive chunking support)
        text_docs = system["text_pipeline"].process(
            text_blocks,
            source_file=uploaded_file.name,
            chunk_size=settings["chunk_size"],
            chunk_overlap=settings["chunk_overlap"],
            adaptive=settings.get("adaptive_chunking", False),
        )
        all_docs.extend(text_docs)

        # Step 5: Process IMAGES
        image_docs = system["image_pipeline"].process(
            image_paths,
            source_file=uploaded_file.name,
        )
        all_docs.extend(image_docs)

        # Step 6: Process TABLES
        table_docs = system["table_pipeline"].process(
            table_data,
            source_file=uploaded_file.name,
        )
        all_docs.extend(table_docs)

        # Step 7: Store in ChromaDB
        if all_docs:
            system["vs_manager"].add_documents(all_docs)

        # Update session state
        st.session_state.all_documents.extend(all_docs)
        st.session_state.uploaded_files_list.append(uploaded_file.name)

        # Update stats
        chunk_stats = {
            "total_chunks": len(all_docs),
            "text_chunks": len(text_docs),
            "image_chunks": len(image_docs),
            "table_chunks": len(table_docs),
        }

        st.session_state.stats["total_chunks"] += len(all_docs)
        st.session_state.stats["text_chunks"] += len(text_docs)
        st.session_state.stats["image_chunks"] += len(image_docs)
        st.session_state.stats["table_chunks"] += len(table_docs)
        st.session_state.stats["total_files"] += 1

        # Register in notebook manager
        notebook_manager.add_pdf_to_notebook(nb_id, uploaded_file.name, chunk_stats)
        selection_store = st.session_state.setdefault("selected_docs_by_notebook", {})
        selection_store.setdefault(nb_id, {})[uploaded_file.name] = True
        st.session_state.selected_docs = dict(selection_store.get(nb_id, {}))

        # Learn domain vocabulary for autocorrect
        try:
            autocorrect = get_autocorrect_engine()
            autocorrect.learn_from_documents(text_docs)
        except Exception:
            pass

        save_notebook_state()

        return True, (
            f"✅ **{uploaded_file.name}** processed successfully!\n\n"
            f"📄 Text chunks: **{len(text_docs)}** | "
            f"🖼️ Image chunks: **{len(image_docs)}** | "
            f"📊 Table chunks: **{len(table_docs)}**"
        )

    except Exception as e:
        logger.error(f"File processing error: {e}")
        return False, f"❌ Error processing {uploaded_file.name}: {str(e)}"


# ============ HANDLE PDF REMOVAL ============
def handle_pdf_removal(filename, system, notebook_manager):
    nb_id = st.session_state.active_notebook_id
    system["vs_manager"].delete_documents_by_source(filename)
    st.session_state.all_documents = [
        doc for doc in st.session_state.all_documents
        if doc.metadata.get("source") != filename
    ]
    if filename in st.session_state.uploaded_files_list:
        st.session_state.uploaded_files_list.remove(filename)
    notebook_selection = st.session_state.get("selected_docs_by_notebook", {}).get(nb_id, {})
    notebook_selection.pop(filename, None)
    notebook_manager.remove_pdf_from_notebook(nb_id, filename)
    nb = notebook_manager.get_notebook(nb_id)
    if nb:
        st.session_state.stats.update({
            "total_chunks": nb["stats"]["total_chunks"],
            "text_chunks": nb["stats"]["text_chunks"],
            "image_chunks": nb["stats"]["image_chunks"],
            "table_chunks": nb["stats"]["table_chunks"],
            "total_files": len(nb.get("pdf_files", [])),
        })
    save_notebook_state()
    logger.info(f"Removed '{filename}' from notebook {nb_id}")


# ============ HANDLE SUMMARIZATION ============
def handle_summarization(content_type, system, source_file_filter=None):
    from core.summarizer import Summarizer
    docs = system["vs_manager"].get_documents_by_type(content_type, source_file_filter=source_file_filter)
    summarizer = Summarizer(system.get("llm"))
    summary = summarizer.summarize_by_type(content_type, docs)
    return summary


# ============ HANDLE QUERY ============
def handle_query(query, content_filter, system, settings, source_file_filter=None):
    """Process user query through the RAG pipeline with guardrails and autocorrect."""
    try:
        if not system.get("llm"):
            return (
                "⚠️ **LLM not loaded.** Please check HF_TOKEN in .env file.\n\n"
                "The system uses HuggingFace Llama 3.1 8B API."
            ), [], []

        # Guardrail check
        if settings.get("guardrails_enabled", True):
            from core.guardrails import Guardrails
            guardrail = Guardrails(vs_manager=system["vs_manager"])
            is_allowed, reason = guardrail.check(query)
            if not is_allowed:
                return reason, [], []

        from core.retriever import AdvancedRetriever
        from core.rag_chain import RAGChain

        # Build retriever
        retriever = AdvancedRetriever(
            vectorstore_manager=system["vs_manager"],
            llm=system["llm"],
            all_documents=st.session_state.all_documents,
        )

        # Retrieve
        retrieved_docs = retriever.retrieve(
            query=query,
            content_type_filter=content_filter,
            top_k=settings["top_k"],
            source_file_filter=source_file_filter,
            retrieval_mode=settings.get("retrieval_mode", "Hybrid (Vector + BM25)"),
            mmr_lambda=settings.get("mmr_lambda"),
        )

        if not retrieved_docs:
            return (
                "🔍 I couldn't find any relevant information in the uploaded documents. "
                "Try rephrasing your question or uploading additional documents."
            ), [], []

        # Generate answer
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

        # Generate follow-up suggestions
        suggestions = []
        try:
            from core.question_suggester import QuestionSuggester
            suggester = QuestionSuggester(system.get("llm"))
            suggestions = suggester.suggest(query, answer)
        except Exception as e:
            logger.warning(f"Suggestion generation failed: {e}")

        return answer, sources, suggestions

    except Exception as e:
        logger.error(f"Query handling error: {e}")
        return f"❌ Error generating answer: {str(e)}", [], []


# ============ MAIN APP ============
def main():
    # ── Restore saved session (survive page refresh) ──
    if not st.session_state.get("authenticated"):
        from core.auth_manager import AuthManager
        auth = AuthManager()
        saved = auth.load_session()
        if saved:
            st.session_state.authenticated = True
            st.session_state.user_data = saved

    # ── Authentication Gate ──
    if not st.session_state.get("authenticated"):
        render_login_page()
        return

    # ── Header ──
    st.markdown(f"""
    <div class="app-header">
        <h1>{t("app_title")}</h1>
        <p>{t("app_subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Initialize Notebook Manager ──
    notebook_manager = get_notebook_manager()

    # ── Sidebar ──
    settings = render_sidebar(notebook_manager)
    llm_provider = settings.get("llm_provider", "HuggingFace (Llama-3.1)")
    ollama_model = settings.get("ollama_model", "qwen2.5:3b")

    # ── Load System ──
    with st.spinner("🔄 Loading AI Models... This may take a minute on first run."):
        system = initialize_system(llm_provider, ollama_model)

    if "error" in system:
        st.error(f"⚠️ System initialization failed: {system['error']}")
        st.info("Please check that all dependencies are installed correctly.")
        return

    st.session_state.system_initialized = True
    st.session_state.stats["model_loaded"] = system.get("llm") is not None

    # ── Ensure active notebook & switch collection ──
    notebooks = notebook_manager.list_notebooks()
    if not notebooks:
        nb = notebook_manager.create_notebook("My Notebook")
        st.session_state.active_notebook_id = nb["id"]

    if not st.session_state.active_notebook_id and notebooks:
        st.session_state.active_notebook_id = notebooks[0]["id"]

    active_nb = notebook_manager.get_notebook(st.session_state.active_notebook_id)
    if active_nb:
        switch_notebook_collection(system, active_nb)

    # ── Status Bar (compact) ──
    llm_status = "green" if system.get("llm") else "red"
    llm_text = "Loaded" if system.get("llm") else "Not Found"
    nb_name = active_nb["name"] if active_nb else "—"
    user_name = st.session_state.get("user_data", {}).get("display_name", "User")

    st.markdown(f"""
    <div class="status-bar">
        <span><span class="status-dot {llm_status}"></span>LLM: {llm_text}</span>
        <span><span class="status-dot green"></span>Vector DB: Active</span>
        <span><span class="status-dot green"></span>Embeddings: Ready</span>
        <span><span class="status-dot green"></span>📓 {nb_name}</span>
        <span style="margin-left:auto; color:#64748b;">
            👤 {user_name} · 🕐 {datetime.now().strftime("%H:%M")}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Show LLM warning
    if system.get("llm_error"):
        st.warning(
            f"⚠️ **LLM not loaded:** {system['llm_error']}\n\n"
            "You can still upload and process documents. Chat will work once the model loads."
        )

    notebook_actions = settings.get("notebook_actions", {})

    # ── Handle Notebook Actions ──
    if notebook_actions.get("notebook_switched"):
        save_notebook_state()
        new_nb = notebook_manager.get_notebook(st.session_state.active_notebook_id)
        if new_nb:
            switch_notebook_collection(system, new_nb, force=True)
        st.rerun()

    if notebook_actions.get("notebook_created"):
        save_notebook_state()
        new_nb = notebook_manager.get_notebook(st.session_state.active_notebook_id)
        if new_nb:
            switch_notebook_collection(system, new_nb, force=True)
        st.rerun()

    if notebook_actions.get("notebook_deleted"):
        save_notebook_state()
        nb_id = st.session_state.active_notebook_id
        system["vs_manager"].delete_collection()
        notebook_manager.delete_notebook(nb_id)
        st.session_state.notebook_documents.pop(nb_id, None)
        st.session_state.notebook_messages.pop(nb_id, None)
        st.session_state.notebook_files.pop(nb_id, None)
        remaining = notebook_manager.list_notebooks()
        if remaining:
            st.session_state.active_notebook_id = remaining[0]["id"]
        else:
            nb = notebook_manager.create_notebook("My Notebook")
            st.session_state.active_notebook_id = nb["id"]
        st.rerun()

    if notebook_actions.get("pdf_to_remove"):
        handle_pdf_removal(notebook_actions["pdf_to_remove"], system, notebook_manager)
        st.rerun()

    if notebook_actions.get("summarize_type"):
        sum_type = notebook_actions["summarize_type"]
        type_labels = {"text": "📄 Text", "image": "🖼️ Image", "table": "📊 Table"}
        label = type_labels.get(sum_type, sum_type)
        with st.spinner(f"🧬 Generating {label} summary..."):
            selected_sources = get_selected_sources_for_active_notebook(notebook_manager)
            
            if not selected_sources and st.session_state.get("uploaded_files_list"):
                summary = "⚠️ **No documents selected!** Please check the box next to at least one document in the workspace settings to allow the AI to summarize."
            else:
                summary = handle_summarization(sum_type, system, source_file_filter=selected_sources)
        add_message("assistant", f"### {label} Summary\n\n{summary}")
        save_notebook_state()
        st.rerun()

    if settings["clear_chat"]:
        st.session_state.messages = []
        st.session_state.suggested_questions = []
        system["memory_manager"].clear_memory()
        save_notebook_state()
        st.rerun()

    if settings["clear_db"]:
        if VECTORSTORE_DIR.exists():
            shutil.rmtree(VECTORSTORE_DIR)
        st.session_state.all_documents = []
        st.session_state.uploaded_files_list = []
        st.session_state.selected_docs = {}
        st.session_state.selected_docs_by_notebook = {}
        st.session_state.stats = {
            "total_chunks": 0, "text_chunks": 0,
            "image_chunks": 0, "table_chunks": 0,
            "total_files": 0, "model_loaded": True, "ram_usage_mb": 0,
        }
        save_notebook_state()
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

    # ── Dashboard Metrics (compact strip) ──
    render_metrics(st.session_state.stats)

    # ── Filter Buttons + Chat ──
    content_filter = render_filter_buttons()

    # ── Process Uploaded Files ──
    if settings["uploaded_files"]:
        for uploaded_file in settings["uploaded_files"]:
            if uploaded_file.name not in st.session_state.uploaded_files_list:
                with st.spinner(f"📄 Processing **{uploaded_file.name}**..."):
                    success, message = process_uploaded_file(
                        uploaded_file, system, settings, notebook_manager
                    )
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # ── Chat Interface ──
    user_input = render_chat_interface()
    
    selected_sources = get_selected_sources_for_active_notebook(notebook_manager)

    # ── Handle user input ──
    if user_input:
        if not st.session_state.uploaded_files_list:
            add_message("assistant", t("no_docs_warning"))
            save_notebook_state()
            st.rerun()
        elif not selected_sources:
            add_message("assistant", "⚠️ **No documents selected!** Please check the box next to at least one document in the workspace settings to allow the AI to search it.")
            save_notebook_state()
            st.rerun()
        else:
            # Autocorrect
            try:
                autocorrect = get_autocorrect_engine()
                corrected, was_changed = autocorrect.correct(user_input)
                if was_changed:
                    add_message("user", user_input,
                                visibility=settings.get("query_visibility", "group"))
                    add_message("assistant",
                                f"✏️ *{t('did_you_mean')}: **{corrected}** ?*\n\n*(Using corrected query)*")
                    user_input = corrected
                else:
                    add_message("user", user_input,
                                visibility=settings.get("query_visibility", "group"))
            except Exception:
                add_message("user", user_input,
                            visibility=settings.get("query_visibility", "group"))

            # Generate answer
            with st.spinner(t("thinking")):
                answer, sources, suggestions = handle_query(
                    user_input, content_filter, system, settings, selected_sources
                )

            # Add assistant response
            add_message("assistant", answer, sources,
                        visibility=settings.get("query_visibility", "group"))

            # Store suggestions
            st.session_state.suggested_questions = suggestions

            save_notebook_state()
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
