"""
Dashboard Metrics — Compact inline stats using native Streamlit columns.
"""

import streamlit as st


def render_metrics(stats):
    """
    Render dashboard metrics as a compact single row using st.columns.
    """
    chips = [
        ("📦", stats.get("total_chunks", 0), "Chunks"),
        ("📄", stats.get("text_chunks", 0), "Text"),
        ("🖼️", stats.get("image_chunks", 0), "Images"),
        ("📊", stats.get("table_chunks", 0), "Tables"),
        ("📚", stats.get("total_files", 0), "Docs"),
        ("🧠", stats.get("ram_usage_mb", 0), "RAM MB"),
    ]

    cols = st.columns(len(chips))
    for col, (icon, value, label) in zip(cols, chips):
        with col:
            st.metric(label=f"{icon} {label}", value=value)
