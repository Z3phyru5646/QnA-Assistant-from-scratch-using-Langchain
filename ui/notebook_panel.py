"""
Notebook Panel UI — Notebook selector, document selection, and summarization controls.
"""

import streamlit as st


def _get_notebook_selection_state(notebook_id, pdf_files):
    """
    Keep document selection isolated per notebook so single-document queries
    do not inherit stale checkbox state from another notebook.
    """
    store = st.session_state.setdefault("selected_docs_by_notebook", {})
    notebook_selection = store.setdefault(notebook_id, {})
    active_names = [pdf["filename"] for pdf in pdf_files]

    for filename in active_names:
        notebook_selection.setdefault(filename, True)

    stale_names = [name for name in notebook_selection if name not in active_names]
    for name in stale_names:
        notebook_selection.pop(name, None)

    # Keep legacy key in sync for any older code paths.
    st.session_state.selected_docs = dict(notebook_selection)
    return notebook_selection


def render_notebook_panel(notebook_manager):
    """
    Render notebook management UI in the sidebar.
    Returns dict with action signals.
    """
    from config.translations import t

    actions = {
        "notebook_switched": False,
        "notebook_created": False,
        "notebook_deleted": False,
        "pdf_to_remove": None,
        "summarize_type": None,
    }

    st.markdown(f"##### {t('notebooks')}")

    notebooks = notebook_manager.list_notebooks()
    if not notebooks:
        nb = notebook_manager.create_notebook("My Notebook")
        notebooks = [nb]
        st.session_state.active_notebook_id = nb["id"]
        actions["notebook_created"] = True

    if "active_notebook_id" not in st.session_state or not st.session_state.active_notebook_id:
        st.session_state.active_notebook_id = notebooks[0]["id"]

    notebook_names = [nb["name"] for nb in notebooks]
    notebook_ids = [nb["id"] for nb in notebooks]

    current_idx = 0
    if st.session_state.active_notebook_id in notebook_ids:
        current_idx = notebook_ids.index(st.session_state.active_notebook_id)

    selected_idx = st.selectbox(
        "Select Notebook",
        range(len(notebook_names)),
        index=current_idx,
        format_func=lambda i: f"📓 {notebook_names[i]}",
        key="notebook_selector",
        label_visibility="collapsed",
    )

    if notebook_ids[selected_idx] != st.session_state.active_notebook_id:
        st.session_state.active_notebook_id = notebook_ids[selected_idx]
        actions["notebook_switched"] = True

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New", use_container_width=True, key="btn_new_nb"):
            st.session_state.show_new_notebook_input = True

    with col2:
        if st.button("🗑️ Delete", use_container_width=True, key="btn_del_nb"):
            if len(notebooks) > 1:
                actions["notebook_deleted"] = True
            else:
                st.toast("Cannot delete the last notebook!", icon="⚠️")

    if st.session_state.get("show_new_notebook_input", False):
        new_name = st.text_input(
            "Notebook Name",
            placeholder="Enter notebook name...",
            key="new_nb_name_input",
            label_visibility="collapsed",
        )
        if st.button("Create Notebook", use_container_width=True, key="btn_create_nb"):
            if new_name and new_name.strip():
                nb = notebook_manager.create_notebook(new_name.strip())
                st.session_state.active_notebook_id = nb["id"]
                st.session_state.show_new_notebook_input = False
                actions["notebook_created"] = True
                st.rerun()
            else:
                st.toast("Please enter a notebook name", icon="⚠️")

    st.markdown("---")

    active_nb = notebook_manager.get_notebook(st.session_state.active_notebook_id)

    if active_nb and active_nb.get("pdf_files"):
        st.markdown(f"##### {t('pdfs_in_notebook')}")
        notebook_selection = _get_notebook_selection_state(
            active_nb["id"],
            active_nb["pdf_files"],
        )

        for pdf_info in active_nb["pdf_files"]:
            fname = pdf_info["filename"]
            text_c = pdf_info.get("text_chunks", 0)
            img_c = pdf_info.get("image_chunks", 0)
            tbl_c = pdf_info.get("table_chunks", 0)

            col_chk, col_stats, col_btn = st.columns([0.5, 4, 1.5], vertical_alignment="center")
            with col_chk:
                is_selected = st.checkbox(
                    "✓",
                    value=notebook_selection[fname],
                    key=f"select_{active_nb['id']}_{fname}",
                    label_visibility="collapsed",
                )
                notebook_selection[fname] = is_selected

            with col_stats:
                st.markdown(
                    f"""
                    <div class="notebook-pdf-item" style="opacity: {1.0 if is_selected else 0.4}; margin:0;">
                        <span class="pdf-name" style="font-weight:600;color:#e2e8f0;display:block;margin-bottom:4px;">{fname}</span>
                        <span class="pdf-stats" style="font-size:11px;color:#94a3b8;">Text chunks: {text_c} &nbsp;|&nbsp; Images: {img_c} &nbsp;|&nbsp; Tables: {tbl_c}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_btn:
                if st.button("Remove", key=f"remove_pdf_{active_nb['id']}_{fname}"):
                    actions["pdf_to_remove"] = fname

        st.markdown("---")
    else:
        st.markdown(
            """
            <div class="notebook-empty">
                📭 No documents yet. Upload files below!
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

    if active_nb and active_nb.get("pdf_files"):
        st.markdown(f"##### {t('summarize_category')}")

        llm_available = st.session_state.get("stats", {}).get("model_loaded", False)
        if not llm_available:
            st.caption("LLM not loaded — summarization unavailable")

        total_text = active_nb["stats"].get("text_chunks", 0)
        total_img = active_nb["stats"].get("image_chunks", 0)
        total_tbl = active_nb["stats"].get("table_chunks", 0)

        sum_col1, sum_col2, sum_col3 = st.columns(3)
        with sum_col1:
            text_disabled = not llm_available or total_text == 0
            if st.button(
                f"📄 Text ({total_text})",
                use_container_width=True,
                key="sum_text",
                disabled=text_disabled,
                help="Summarize all text content" if not text_disabled else "No text chunks available",
            ):
                actions["summarize_type"] = "text"

        with sum_col2:
            img_disabled = not llm_available or total_img == 0
            if st.button(
                f"🖼️ Img ({total_img})",
                use_container_width=True,
                key="sum_image",
                disabled=img_disabled,
                help="Summarize image descriptions" if not img_disabled else "No image chunks available",
            ):
                actions["summarize_type"] = "image"

        with sum_col3:
            tbl_disabled = not llm_available or total_tbl == 0
            if st.button(
                f"📊 Tbl ({total_tbl})",
                use_container_width=True,
                key="sum_table",
                disabled=tbl_disabled,
                help="Summarize table data" if not tbl_disabled else "No table chunks available",
            ):
                actions["summarize_type"] = "table"

        st.markdown("---")

    if active_nb:
        total = active_nb["stats"]["total_chunks"]
        pdf_count = len(active_nb.get("pdf_files", []))
        st.markdown(
            f"""
            <div class="notebook-info-badge">
                <strong>📓 {active_nb['name']}</strong><br>
                <span>{pdf_count} doc(s) • {total} chunks</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return actions
