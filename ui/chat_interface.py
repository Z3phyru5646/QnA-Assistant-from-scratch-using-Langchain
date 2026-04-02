"""
Chat Interface — Chat messages display and input handling.
"""

import streamlit as st
from datetime import datetime


def render_chat_interface():
    """
    Render the chat messages and input box.

    Returns:
        user_input: the text the user typed, or None
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 **Hello!** I'm your Local RAG Knowledge Assistant.\n\n"
                    "Upload a PDF document using the sidebar, and I'll help you "
                    "find information from it. You can filter answers by "
                    "**Text**, **Images**, or **Tables** using the buttons above!\n\n"
                    "💡 *Tip: I work 100% locally — your data never leaves this machine.*"
                ),
                "timestamp": datetime.now().strftime("%H:%M"),
                "sources": [],
            }
        ]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Timestamp
            ts = message.get("timestamp", "")
            if ts:
                st.caption(f"🕐 {ts}")

            # Sources (for assistant messages)
            if message["role"] == "assistant" and message.get("sources"):
                with st.expander(f"📎 View Sources ({len(message['sources'])})", expanded=False):
                    for i, source in enumerate(message["sources"]):
                        ctype = source.get("content_type", "text")
                        type_class = f"type-{ctype}"
                        type_icon = {"text": "📄", "image": "🖼️", "table": "📊"}.get(ctype, "📄")

                        st.markdown(f"""
                        <div class="source-card {type_class}">
                            <strong>{type_icon} Source {i+1}</strong><br>
                            <span style="color:#94a3b8;">
                                📁 {source.get('source', 'Unknown')} &nbsp;|&nbsp;
                                📃 Page {source.get('page', '?')} &nbsp;|&nbsp;
                                🏷️ {ctype.title()}
                            </span><br>
                            <span style="color:#64748b; font-size:12px;">
                                {source.get('preview', '')[:150]}...
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("💬 Ask a question about your documents...")
    return user_input


def add_message(role, content, sources=None):
    """Add a message to the chat history in session state."""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M"),
        "sources": sources or [],
    })
