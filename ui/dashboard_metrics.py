"""
Dashboard Metrics — Gradient metric cards showing knowledge base stats.
"""

import streamlit as st


def render_metrics(stats):
    """
    Render dashboard metric cards.

    Args:
        stats: dict with keys like total_chunks, text_chunks, image_chunks,
               table_chunks, total_files, ram_usage_mb
    """
    cols = st.columns(6)

    cards = [
        {
            "icon": "📦",
            "value": stats.get("total_chunks", 0),
            "label": "Total Chunks",
            "color": "purple",
        },
        {
            "icon": "📄",
            "value": stats.get("text_chunks", 0),
            "label": "Text Chunks",
            "color": "blue",
        },
        {
            "icon": "🖼️",
            "value": stats.get("image_chunks", 0),
            "label": "Image Chunks",
            "color": "green",
        },
        {
            "icon": "📊",
            "value": stats.get("table_chunks", 0),
            "label": "Table Chunks",
            "color": "orange",
        },
        {
            "icon": "📚",
            "value": stats.get("total_files", 0),
            "label": "PDF Files",
            "color": "pink",
        },
        {
            "icon": "🧠",
            "value": stats.get("ram_usage_mb", 0),
            "label": "RAM (MB)",
            "color": "cyan",
        },
    ]

    for col, card in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div class="metric-card {card['color']} animate-in">
                <span class="metric-icon">{card['icon']}</span>
                <h3>{card['value']}</h3>
                <p>{card['label']}</p>
            </div>
            """, unsafe_allow_html=True)
