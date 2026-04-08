"""
Custom CSS — Premium dark-themed Streamlit styling.
Clean, open, spacious layout. Compact metrics. Glassmorphism.
"""

CUSTOM_CSS = """
<style>
    /* ============ IMPORTS ============ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ============ GLOBAL ============ */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1400px;
    }

    /* ============ HEADER ============ */
    .app-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }

    .app-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(102, 126, 234, 0.08) 0%, transparent 50%);
        pointer-events: none;
    }

    .app-header h1 {
        font-size: 24px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #a78bfa 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .app-header p {
        color: #94a3b8;
        font-size: 12px;
        margin: 3px 0 0 0;
        font-weight: 400;
    }

    /* ============ STATUS BAR ============ */
    .status-bar {
        background: rgba(22, 33, 62, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 10px;
        padding: 8px 18px;
        display: flex;
        gap: 16px;
        align-items: center;
        flex-wrap: wrap;
        border: 1px solid rgba(102, 126, 234, 0.1);
        margin-bottom: 12px;
        font-size: 11px;
        color: #94a3b8;
    }

    .status-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 5px;
        animation: pulse 2s infinite;
    }

    .status-dot.green { background: #48bb78; box-shadow: 0 0 6px rgba(72, 187, 120, 0.5); }
    .status-dot.yellow { background: #ecc94b; }
    .status-dot.red { background: #fc8181; box-shadow: 0 0 6px rgba(252, 129, 129, 0.5); }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ============ COMPACT METRICS ============ */
    [data-testid="stMetric"] {
        background: rgba(26, 26, 46, 0.5);
        border: 1px solid rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
    }

    [data-testid="stMetric"] label {
        font-size: 11px !important;
        color: #64748b !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #e2e8f0 !important;
    }

    /* ============ SIDEBAR ============ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e0e0e0;
    }

    [data-testid="stSidebar"] .stSlider label {
        color: #94a3b8 !important;
        font-size: 13px;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(102, 126, 234, 0.1);
        margin: 12px 0;
    }

    /* ============ BUTTONS ============ */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.2s ease;
        border: 1px solid rgba(102, 126, 234, 0.15);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
    }

    /* ============ CHAT MESSAGES ============ */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        margin: 4px 0;
        border: 1px solid rgba(255, 255, 255, 0.03);
    }

    /* ============ SOURCE CARDS ============ */
    .source-card {
        background: rgba(45, 55, 72, 0.4);
        border-radius: 10px;
        padding: 10px 14px;
        margin: 5px 0;
        border-left: 3px solid #ed8936;
        font-size: 12px;
        transition: all 0.2s ease;
    }

    .source-card:hover {
        transform: translateX(2px);
    }

    .source-card.type-text { border-left-color: #4299e1; }
    .source-card.type-image { border-left-color: #48bb78; }
    .source-card.type-table { border-left-color: #ed8936; }

    /* ============ FILE UPLOAD ============ */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(102, 126, 234, 0.2) !important;
        border-radius: 12px;
        transition: border-color 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: rgba(102, 126, 234, 0.45) !important;
    }

    /* ============ SYSTEM INFO ============ */
    .sys-info {
        background: rgba(15, 12, 41, 0.4);
        border-radius: 8px;
        padding: 10px 14px;
        border: 1px solid rgba(102, 126, 234, 0.08);
        font-size: 10px;
        color: #64748b;
    }

    .sys-info strong {
        color: #94a3b8;
    }

    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {
        font-size: 13px;
        font-weight: 600;
        color: #94a3b8;
    }

    /* ============ HIDE DEFAULTS ============ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ============ CHAT INPUT ============ */
    [data-testid="stChatInput"] { border-radius: 12px; }
    [data-testid="stChatInput"] textarea { border-radius: 12px; }

    /* ============ SCROLLBAR ============ */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #4a5568; }

    /* ============ DIVIDERS ============ */
    hr {
        border-color: rgba(102, 126, 234, 0.06) !important;
        margin: 12px 0 !important;
    }

    /* ============ ANIMATIONS ============ */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animate-in { animation: fadeIn 0.3s ease-out; }

    /* ============ NOTEBOOK PANEL ============ */
    .notebook-pdf-item {
        background: rgba(102, 126, 234, 0.05);
        border: 1px solid rgba(102, 126, 234, 0.1);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .notebook-pdf-item .pdf-name {
        font-size: 11px;
        font-weight: 600;
        color: #e2e8f0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .notebook-pdf-item .pdf-stats {
        font-size: 9px;
        color: #64748b;
        letter-spacing: 0.5px;
    }

    .notebook-empty {
        background: rgba(15, 12, 41, 0.2);
        border: 1px dashed rgba(102, 126, 234, 0.12);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        color: #64748b;
        font-size: 12px;
        margin: 8px 0;
    }

    .notebook-info-badge {
        background: rgba(102, 126, 234, 0.08);
        border: 1px solid rgba(102, 126, 234, 0.12);
        border-radius: 10px;
        padding: 8px 12px;
        text-align: center;
        font-size: 11px;
        color: #94a3b8;
    }

    .notebook-info-badge strong {
        color: #a78bfa;
        font-size: 12px;
    }

    /* ============ USER HEADER ============ */
    .user-header {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: rgba(102, 126, 234, 0.06);
        border-radius: 6px;
        font-size: 11px;
        color: #a78bfa;
    }

    /* ============ VISIBILITY BADGE ============ */
    .visibility-badge {
        display: inline-block;
        font-size: 9px;
        padding: 1px 5px;
        border-radius: 4px;
        margin-left: 4px;
        font-weight: 600;
    }

    .visibility-badge.local {
        background: rgba(236, 201, 75, 0.12);
        color: #ecc94b;
    }

    .visibility-badge.group {
        background: rgba(72, 187, 120, 0.12);
        color: #48bb78;
    }

    /* ============ TABS ============ */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 6px 14px; }
</style>
"""
