"""
Chat Interface — Chat messages display with visibility badges and suggestion pills.
"""

import streamlit as st
from datetime import datetime


def render_chat_interface():
    """
    Render the chat messages and input box.
    Sources are shown in the citation panel (separate), not inline.
    Returns: user_input text or None
    """
    from config.translations import t

    # SVGs for custom gradient avatars
    import base64
    ai_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#7c3aed"/><stop offset="100%" stop-color="#f97316"/></linearGradient></defs><circle cx="50" cy="50" r="50" fill="url(#g1)"/><text x="50" y="55" font-family="Arial" font-size="45" fill="white" font-weight="bold" text-anchor="middle" dominant-baseline="middle">AI</text></svg>"""
    user_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#2dd4bf"/></linearGradient></defs><circle cx="50" cy="50" r="50" fill="url(#g2)"/><text x="50" y="55" font-family="Arial" font-size="45" fill="white" font-weight="bold" text-anchor="middle" dominant-baseline="middle">U</text></svg>"""
    
    avatar_map = {
        "assistant": f"data:image/svg+xml;base64,{base64.b64encode(ai_svg.encode('utf-8')).decode('utf-8')}",
        "user": f"data:image/svg+xml;base64,{base64.b64encode(user_svg.encode('utf-8')).decode('utf-8')}"
    }

    # Display chat messages
    for idx, message in enumerate(st.session_state.get("messages", [])):
        avatar_src = avatar_map.get(message["role"], "👤")
        with st.chat_message(message["role"], avatar=avatar_src):
            st.markdown(message["content"])

            # Compact footer: timestamp + visibility badge
            footer_parts = []
            ts = message.get("timestamp", "")
            if ts:
                footer_parts.append(f"🕐 {ts}")

            visibility = message.get("visibility", "group")
            vis_icon = "🔒" if visibility == "local" else "👥"
            footer_parts.append(f"{vis_icon} {visibility.title()}")

            # Source count badge (clickable hint)
            if message["role"] == "assistant" and message.get("sources"):
                src_count = len(message["sources"])
                footer_parts.append(f"📎 {src_count} source(s)")

            if footer_parts:
                st.caption(" · ".join(footer_parts))

            # Render inline sources dropdown if available
            if message["role"] == "assistant" and message.get("sources"):
                with st.expander(f"📎 View {len(message['sources'])} Sources & Citations", expanded=False):
                    for i, source in enumerate(message["sources"]):
                        ctype = source.get("content_type", "text")
                        type_icon = {"text": "📄", "image": "🖼️", "table": "📊"}.get(ctype, "📄")
                        
                        st.markdown(f"**{type_icon} Source {i+1} — {ctype.title()}**")
                        st.caption(f"📁 {source.get('source', 'Unknown')} &nbsp;•&nbsp; 📃 Page {source.get('page', '?')}")
                        st.markdown(f"> {source.get('preview', '')}")
                        
                        if i < len(message["sources"]) - 1:
                            st.divider()

    # Suggested questions (after last assistant message)
    suggestions = st.session_state.get("suggested_questions", [])
    if suggestions:
        st.markdown('<div class="section-header">💡 Suggested Follow-ups</div>', unsafe_allow_html=True)
        cols = st.columns(len(suggestions))
        for i, (col, q) in enumerate(zip(cols, suggestions)):
            with col:
                if st.button(f"💡 {q}", key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.suggestion_clicked = q
                    st.rerun()

    # Chat input
    user_input = st.chat_input(t("chat_placeholder"))

    # Check if suggestion was clicked
    if st.session_state.get("suggestion_clicked"):
        user_input = st.session_state.suggestion_clicked
        st.session_state.suggestion_clicked = None

    return user_input


def add_message(role, content, sources=None, visibility="group"):
    """Add a message to the chat history in session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M"),
        "sources": sources or [],
        "visibility": visibility,
        "user_id": st.session_state.get("user_data", {}).get("user_id", "local"),
    })
