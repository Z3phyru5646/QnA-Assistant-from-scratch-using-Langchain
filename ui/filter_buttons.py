"""
Filter Buttons — Minimal inline pill-style content type filter.
"""

import streamlit as st


def render_filter_buttons():
    """
    Render content type filter as small inline pills.
    Returns: active filter value (None, "text", "image", "table")
    """
    if "content_filter" not in st.session_state:
        st.session_state.content_filter = None

    current = st.session_state.get("content_filter")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔍 All", use_container_width=True,
                     type="primary" if current is None else "secondary",
                     key="filter_all"):
            st.session_state.content_filter = None
            st.rerun()
    with col2:
        if st.button("📄 Text", use_container_width=True,
                     type="primary" if current == "text" else "secondary",
                     key="filter_text"):
            st.session_state.content_filter = "text"
            st.rerun()
    with col3:
        if st.button("🖼️ Images", use_container_width=True,
                     type="primary" if current == "image" else "secondary",
                     key="filter_image"):
            st.session_state.content_filter = "image"
            st.rerun()
    with col4:
        if st.button("📊 Tables", use_container_width=True,
                     type="primary" if current == "table" else "secondary",
                     key="filter_table"):
            st.session_state.content_filter = "table"
            st.rerun()

    return st.session_state.get("content_filter")
