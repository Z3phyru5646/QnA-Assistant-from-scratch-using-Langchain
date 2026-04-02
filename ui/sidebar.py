"""
Sidebar Component — File upload, settings, actions, system info.
"""

import streamlit as st
from config.settings import (
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS,
    LLM_TEMPERATURE, MMR_DIVERSITY_SCORE
)


def render_sidebar():
    """Render the sidebar with all controls. Returns settings dict."""
    with st.sidebar:
        # ── Logo / Brand ──
        st.markdown("""
        <div style="text-align:center; padding: 8px 0 16px 0;">
            <span style="font-size: 42px;">🧠</span>
            <h2 style="margin:4px 0 0 0; font-size:18px; font-weight:700;
                       background: linear-gradient(135deg, #667eea, #a78bfa);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;">
                RAG Knowledge<br>Assistant
            </h2>
            <p style="font-size:10px; color:#64748b; margin:4px 0 0 0;
                      text-transform:uppercase; letter-spacing:2px;">
                Offline • Private • Local
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Document Upload ──
        st.markdown("##### 📄 Document Upload")
        uploaded_files = st.file_uploader(
            "Drop PDF files here",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF files to build your knowledge base",
            label_visibility="collapsed",
        )

        # Show uploaded files
        if st.session_state.get("uploaded_files_list"):
            st.markdown("##### 📚 Processed Files")
            for fname in st.session_state.uploaded_files_list:
                st.markdown(f"""
                <div class="file-badge">✅ {fname}</div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Settings ──
        st.markdown("##### ⚙️ RAG Settings")

        chunk_size = st.slider(
            "📏 Chunk Size",
            200, 1000, CHUNK_SIZE, 50,
            help="Maximum characters per text chunk"
        )
        chunk_overlap = st.slider(
            "🔗 Overlap",
            50, 400, CHUNK_OVERLAP, 50,
            help="Character overlap between consecutive chunks"
        )
        top_k = st.slider(
            "🎯 Top K Results",
            1, 10, TOP_K_RESULTS,
            help="Number of document chunks to retrieve"
        )
        temperature = st.slider(
            "🌡️ Temperature",
            0.0, 1.0, LLM_TEMPERATURE, 0.1,
            help="Lower = more focused, Higher = more creative"
        )
        mmr_lambda = st.slider(
            "🎲 MMR Diversity",
            0.0, 1.0, MMR_DIVERSITY_SCORE, 0.1,
            help="0 = max diversity, 1 = max relevance"
        )

        st.markdown("---")

        # ── Retrieval Mode ──
        st.markdown("##### 🔍 Retrieval Strategy")
        retrieval_mode = st.selectbox(
            "Mode",
            ["Hybrid (Vector + BM25)", "Vector Only (MMR)", "BM25 Only"],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Actions ──
        st.markdown("##### 🛠️ Actions")
        col1, col2 = st.columns(2)
        with col1:
            clear_chat = st.button("🗑️ Clear Chat", use_container_width=True)
        with col2:
            clear_db = st.button("💣 Clear DB", use_container_width=True)

        export_chat = st.button("📥 Export Chat", use_container_width=True)

        st.markdown("---")

        # ── System Info ──
        st.markdown("##### 💻 System")
        st.markdown("""
        <div class="sys-info">
            <strong>🤖 Model:</strong> TinyLlama-1.1B (Q4)<br>
            <strong>📐 Embeddings:</strong> MiniLM-L6-v2 (384d)<br>
            <strong>🗄️ Vector DB:</strong> ChromaDB (HNSW)<br>
            <strong>🔍 Search:</strong> Hybrid + Re-rank
        </div>
        """, unsafe_allow_html=True)

    return {
        "uploaded_files": uploaded_files,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "top_k": top_k,
        "temperature": temperature,
        "mmr_lambda": mmr_lambda,
        "retrieval_mode": retrieval_mode,
        "clear_chat": clear_chat,
        "clear_db": clear_db,
        "export_chat": export_chat,
    }
