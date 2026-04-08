"""
Citation Panel — Displays sources and citations for the selected message.
"""

import streamlit as st


def render_citation_panel():
    """Render the citations/sources panel for the latest assistant message with sources."""
    # Find the latest assistant message with sources
    sources = []
    for msg in reversed(st.session_state.get("messages", [])):
        if msg["role"] == "assistant" and msg.get("sources"):
            sources = msg["sources"]
            break

    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(15,12,41,0.6),rgba(22,33,62,0.6));
                border-radius:12px;padding:16px;border:1px solid rgba(102,126,234,0.15);
                margin-bottom:12px;">
        <h4 style="margin:0 0 12px 0;font-size:14px;color:#a78bfa;
                   letter-spacing:0.5px;">📎 SOURCES & CITATIONS</h4>
    """, unsafe_allow_html=True)

    if not sources:
        st.markdown("""
        <div style="text-align:center;padding:24px;color:#64748b;font-size:13px;">
            <div style="font-size:32px;margin-bottom:8px;">📭</div>
            Ask a question to see sources here
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, source in enumerate(sources):
            ctype = source.get("content_type", "text")
            type_colors = {"text": "#4299e1", "image": "#48bb78", "table": "#ed8936"}
            color = type_colors.get(ctype, "#4299e1")
            type_icon = {"text": "📄", "image": "🖼️", "table": "📊"}.get(ctype, "📄")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(f"{type_icon} Source {i+1} — {ctype.title()}", expanded=False):
                st.caption(f"📁 {source.get('source', 'Unknown')} &nbsp;•&nbsp; 📃 Page {source.get('page', '?')}")
                st.markdown(f"> {source.get('preview', '')}")

    st.markdown("</div>", unsafe_allow_html=True)
