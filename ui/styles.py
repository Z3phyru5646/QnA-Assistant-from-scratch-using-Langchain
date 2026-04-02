"""
Custom CSS — Premium dark-themed Streamlit styling.
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
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* ============ HEADER ============ */
    .app-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
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
        font-size: 28px;
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
        font-size: 13px;
        margin: 4px 0 0 0;
        font-weight: 400;
    }

    /* ============ STATUS BAR ============ */
    .status-bar {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 10px 20px;
        display: flex;
        gap: 16px;
        align-items: center;
        border: 1px solid rgba(102, 126, 234, 0.15);
        margin-bottom: 16px;
        font-size: 12px;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }

    .status-dot.green { background: #48bb78; box-shadow: 0 0 8px rgba(72, 187, 120, 0.5); }
    .status-dot.yellow { background: #ecc94b; box-shadow: 0 0 8px rgba(236, 201, 75, 0.5); }
    .status-dot.red { background: #fc8181; box-shadow: 0 0 8px rgba(252, 129, 129, 0.5); }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
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
        border-color: rgba(102, 126, 234, 0.15);
        margin: 12px 0;
    }

    /* ============ METRIC CARDS ============ */
    .metric-card {
        border-radius: 14px;
        padding: 18px 16px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.06);
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }

    .metric-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 14px 14px 0 0;
    }

    .metric-card.purple {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
    }
    .metric-card.purple::after { background: linear-gradient(90deg, #667eea, #764ba2); }

    .metric-card.blue {
        background: linear-gradient(135deg, rgba(66, 153, 225, 0.15) 0%, rgba(56, 178, 172, 0.15) 100%);
    }
    .metric-card.blue::after { background: linear-gradient(90deg, #4299e1, #38b2ac); }

    .metric-card.green {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.15) 0%, rgba(56, 178, 172, 0.15) 100%);
    }
    .metric-card.green::after { background: linear-gradient(90deg, #48bb78, #38b2ac); }

    .metric-card.orange {
        background: linear-gradient(135deg, rgba(237, 137, 54, 0.15) 0%, rgba(245, 101, 101, 0.15) 100%);
    }
    .metric-card.orange::after { background: linear-gradient(90deg, #ed8936, #f56565); }

    .metric-card.pink {
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(167, 139, 250, 0.15) 100%);
    }
    .metric-card.pink::after { background: linear-gradient(90deg, #ec4899, #a78bfa); }

    .metric-card.cyan {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
    }
    .metric-card.cyan::after { background: linear-gradient(90deg, #38bdf8, #3b82f6); }

    .metric-card h3 {
        font-size: 32px;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
    }

    .metric-card p {
        font-size: 11px;
        margin: 6px 0 0 0;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    .metric-card .metric-icon {
        font-size: 20px;
        margin-bottom: 8px;
        display: block;
    }

    /* ============ FILTER BUTTONS ============ */
    .filter-section {
        background: rgba(26, 26, 46, 0.6);
        border-radius: 12px;
        padding: 12px 16px;
        border: 1px solid rgba(102, 126, 234, 0.1);
        margin-bottom: 16px;
    }

    .filter-indicator {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 12px;
        color: #a78bfa;
        text-align: center;
        margin-top: 8px;
    }

    /* ============ CHAT MESSAGES ============ */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        margin: 4px 0;
        border: 1px solid rgba(255, 255, 255, 0.03);
    }

    /* ============ SOURCE CARDS ============ */
    .source-card {
        background: linear-gradient(135deg, rgba(45, 55, 72, 0.6) 0%, rgba(26, 32, 44, 0.6) 100%);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 6px 0;
        border-left: 3px solid #ed8936;
        font-size: 13px;
        transition: border-color 0.2s ease;
    }

    .source-card:hover {
        border-left-color: #f6ad55;
    }

    .source-card.type-text { border-left-color: #4299e1; }
    .source-card.type-image { border-left-color: #48bb78; }
    .source-card.type-table { border-left-color: #ed8936; }

    /* ============ FILE UPLOAD ============ */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(102, 126, 234, 0.3) !important;
        border-radius: 12px;
        transition: border-color 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: rgba(102, 126, 234, 0.6) !important;
    }

    /* ============ UPLOADED FILE BADGE ============ */
    .file-badge {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.1) 0%, rgba(56, 178, 172, 0.1) 100%);
        border: 1px solid rgba(72, 187, 120, 0.2);
        border-radius: 8px;
        padding: 6px 12px;
        margin: 4px 0;
        font-size: 12px;
        color: #48bb78;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* ============ SYSTEM INFO ============ */
    .sys-info {
        background: rgba(15, 12, 41, 0.5);
        border-radius: 8px;
        padding: 10px 14px;
        border: 1px solid rgba(102, 126, 234, 0.1);
        font-size: 11px;
        color: #64748b;
    }

    .sys-info strong {
        color: #94a3b8;
    }

    /* ============ BUTTONS ============ */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.2s ease;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {
        font-size: 14px;
        font-weight: 600;
        color: #94a3b8;
    }

    /* ============ HIDE DEFAULTS ============ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ============ CHAT INPUT ============ */
    [data-testid="stChatInput"] {
        border-radius: 12px;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 12px;
    }

    /* ============ SCROLLBAR ============ */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #4a5568; }

    /* ============ DIVIDERS ============ */
    hr {
        border-color: rgba(102, 126, 234, 0.1) !important;
        margin: 16px 0 !important;
    }

    /* ============ ANIMATION ============ */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animate-in {
        animation: fadeIn 0.4s ease-out;
    }

    /* ============ PROCESSING OVERLAY ============ */
    .processing-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(167, 139, 250, 0.08) 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
    }

    .processing-card .step {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 0;
        font-size: 13px;
        color: #94a3b8;
    }

    .processing-card .step.active {
        color: #a78bfa;
        font-weight: 600;
    }

    .processing-card .step.done {
        color: #48bb78;
    }
</style>
"""
