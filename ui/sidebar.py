"""
Sidebar Component — File upload, notebook panel, settings, actions, system monitor.
Reorganized with collapsible sections and adaptive chunking toggle.
"""

import streamlit as st
from config.settings import (
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS,
    LLM_TEMPERATURE, MMR_DIVERSITY_SCORE
)
from config.translations import t, LANGUAGES
from ui.notebook_panel import render_notebook_panel
from ui.system_monitor import render_system_monitor


def render_sidebar(notebook_manager):
    """Render the sidebar with all controls as a Top Bar Expander. Returns settings dict."""
    with st.expander("🛠️ Workspace Settings, Documents & Uploads", expanded=False):
        
        # ── User & Brand row ──
        ucol1, ucol2, ucol3 = st.columns([1, 2, 1])
        with ucol2:
            st.markdown("""
            <div style="text-align:center; padding: 4px 0;">
                <span style="font-size: 24px;">🧠</span>
                <span style="font-size:16px; font-weight:700;
                           background: linear-gradient(135deg, #667eea, #a78bfa);
                           -webkit-background-clip: text;
                           -webkit-text-fill-color: transparent;">
                    RAG Knowledge Assistant
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        with ucol3:
            user_data = st.session_state.get("user_data")
            if user_data:
                col_user, col_logout = st.columns([3, 1])
                with col_user:
                    st.markdown(f"👤 **{user_data.get('display_name', 'User')}**")
                with col_logout:
                    if st.button("🚪", key="btn_logout", help="Logout"):
                        from core.auth_manager import AuthManager
                        AuthManager().clear_session()
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()

        st.divider()

        # ── Main Settings Area (2 columns) ──
        col1, col2 = st.columns(2)

        with col1:
            # ── Notebook Panel & Upload ──
            st.markdown(f"##### {t('upload_docs')}")
            uploaded_files = st.file_uploader(
                t("drop_files"),
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help="Upload PDF, DOCX, or TXT files",
                label_visibility="collapsed",
            )
            st.markdown("---")
            notebook_actions = render_notebook_panel(notebook_manager)
            
            st.markdown("---")
            # ── System Resources ──
            st.markdown("##### 💻 System")
            render_system_monitor()

        with col2:
            # ── RAG Settings ──
            adaptive_chunking = st.toggle(t("adaptive_chunking"), value=True,
                                           help="Auto-adjust chunk size based on document content")

            if adaptive_chunking:
                st.success("📐 Chunk size auto-adjusts based on your document's density")
                chunk_size = CHUNK_SIZE
                chunk_overlap = CHUNK_OVERLAP
            else:
                chunk_size = st.slider(t("chunk_size"), 300, 3000, CHUNK_SIZE, 100)
                chunk_overlap = st.slider(t("overlap"), 50, 600, CHUNK_OVERLAP, 50)

            top_k = st.slider(t("top_k"), 1, 10, TOP_K_RESULTS)
            temperature = st.slider(t("temperature"), 0.0, 1.0, LLM_TEMPERATURE, 0.1)
            mmr_lambda = st.slider(t("mmr_diversity"), 0.0, 1.0, MMR_DIVERSITY_SCORE, 0.1)

            guardrails_enabled = st.toggle(t("guardrails"), value=True)
            
            st.markdown(f"##### {t('retrieval_strategy')}")
            retrieval_mode = st.selectbox(
                "Mode",
                ["Hybrid (Vector + BM25)", "Vector Only (MMR)", "BM25 Only"],
                index=0,
                label_visibility="collapsed",
            )

            st.markdown("##### 🤖 LLM Provider")
            llm_provider = st.radio(
                "provider",
                ["HuggingFace (Llama-3.1)", "Local Ollama"],
                index=0,
                horizontal=True,
                label_visibility="collapsed",
            )
            
            ollama_model = "qwen2.5:3b"
            if "Ollama" in llm_provider:
                ollama_model = st.text_input("Ollama Model Name", value="qwen2.5:3b")

            st.markdown("##### 🔒 Query Visibility")
            query_visibility = st.radio(
                "vis_mode",
                ["👥 Group", "🔒 Private"],
                index=0,
                horizontal=True,
                label_visibility="collapsed",
            )
            
            # Actions
            colA, colB, colC = st.columns(3)
            with colA: clear_chat = st.button(t("clear_chat"), use_container_width=True)
            with colB: clear_db = st.button(t("clear_db"), use_container_width=True)
            with colC: export_chat = st.button(t("export_chat"), use_container_width=True)

    # Note: Language selector dropped here for cleaner layout, can add back if needed.
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
        "adaptive_chunking": adaptive_chunking,
        "guardrails_enabled": guardrails_enabled,
        "query_visibility": "local" if "Private" in query_visibility else "group",
        "notebook_actions": notebook_actions,
        "llm_provider": llm_provider,
        "ollama_model": ollama_model,
    }
