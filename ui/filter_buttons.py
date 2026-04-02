"""
Filter Buttons — Content type filter toggle (All / Text / Images / Tables).
"""

import streamlit as st


def render_filter_buttons():
    """
    Render content type filter buttons.
    Updates st.session_state.content_filter.

    Returns:
        The active filter value (None, "text", "image", "table")
    """
    # Initialize
    if "content_filter" not in st.session_state:
        st.session_state.content_filter = None

    st.markdown('<div class="filter-section">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    current = st.session_state.get("content_filter")

    with col1:
        if st.button(
            "🔍 All Sources",
            use_container_width=True,
            type="primary" if current is None else "secondary",
            key="filter_all",
        ):
            st.session_state.content_filter = None
            st.rerun()

    with col2:
        if st.button(
            "📄 Text Only",
            use_container_width=True,
            type="primary" if current == "text" else "secondary",
            key="filter_text",
        ):
            st.session_state.content_filter = "text"
            st.rerun()

    with col3:
        if st.button(
            "🖼️ Images Only",
            use_container_width=True,
            type="primary" if current == "image" else "secondary",
            key="filter_image",
        ):
            st.session_state.content_filter = "image"
            st.rerun()

    with col4:
        if st.button(
            "📊 Tables Only",
            use_container_width=True,
            type="primary" if current == "table" else "secondary",
            key="filter_table",
        ):
            st.session_state.content_filter = "table"
            st.rerun()

    # Filter indicator
    active = st.session_state.get("content_filter")
    if active:
        label = {"text": "📄 TEXT", "image": "🖼️ IMAGE", "table": "📊 TABLE"}.get(active, active.upper())
        st.markdown(f"""
        <div class="filter-indicator">
            Filtering answers from: <strong>{label}</strong> content only
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="filter-indicator">
            Searching across: <strong>🔍 ALL</strong> content types
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.get("content_filter")
