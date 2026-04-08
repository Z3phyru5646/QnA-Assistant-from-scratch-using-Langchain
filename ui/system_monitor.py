"""
System Monitor — Live CPU, RAM, Disk, and GPU usage display.
"""

import streamlit as st
import psutil
import logging

logger = logging.getLogger(__name__)


def get_color_class(percent):
    """Return color based on usage percentage."""
    if percent < 50:
        return "#48bb78"  # green
    elif percent < 80:
        return "#ecc94b"  # yellow
    else:
        return "#fc8181"  # red


def render_system_monitor():
    """Render live system resource usage in the sidebar."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        resources = [
            ("🔲 CPU", cpu, f"{cpu:.0f}%"),
            ("🧠 RAM", mem.percent, f"{mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB"),
            ("💾 Disk", disk.percent, f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB"),
        ]

        # Try GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                resources.append(("🎮 GPU", gpu.load * 100, f"{gpu.memoryUsed:.0f}MB / {gpu.memoryTotal:.0f}MB"))
        except Exception:
            pass

        for name, percent, label in resources:
            color = get_color_class(percent)
            st.markdown(f"""
            <div style="margin:4px 0;">
                <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-bottom:2px;">
                    <span>{name}</span>
                    <span>{label}</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:6px;overflow:hidden;">
                    <div style="width:{min(percent, 100):.0f}%;height:100%;background:{color};border-radius:4px;
                                transition:width 0.5s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.caption(f"⚠️ Monitor error: {e}")
